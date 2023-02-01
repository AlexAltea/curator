import collections
import json
import logging
import os
import re
import subprocess
import tempfile

import chardet
import iso639
import langid
import pysrt

# Default options
DEF_OPTS_LANGUAGE = {
    'only_macrolanguages': False,
    'max_audio_samples': 10,
    'max_video_samples': 10,
    'min_score': 0.8,
}

class Stream:
    def __init__(self, media, index, info=None):
        self.media = media
        self.index = index

        # Cache stream information
        self.info = info
        self.packets = None

        # Store warnings about the stream
        self.warnings = set()

    def __repr__(self):
        return f'Stream("{self.media.path}", index={self.index})'

    def is_video(self):
        return self.get_info()['codec_type'] == 'video'

    def is_audio(self):
        return self.get_info()['codec_type'] == 'audio'

    def is_subtitle(self):
        return self.get_info()['codec_type'] == 'subtitle'

    def video_index(self):
        return len([s for s in self.media.get_streams()[:self.index] if s.is_video()])

    def audio_index(self):
        return len([s for s in self.media.get_streams()[:self.index] if s.is_audio()])

    def subtitle_index(self):
        return len([s for s in self.media.get_streams()[:self.index] if s.is_subtitle()])

    def has_packed_bframes(self):
        packet = self.get_packet(0)
        packet_offs = int(packet['pos'])
        packet_size = int(packet['size'])
        with open(self.media.path, 'rb') as f:
            f.seek(packet_offs)
            data = f.read(packet_size)
        match1 = re.search(br'\x00\x00\x01\xB2DivX(\d+)b(\d+)p', data)
        match2 = re.search(br'\x00\x00\x01\xB2DivX(\d+)Build(\d+)p', data)
        if match1 or match2:
            return True
        return False

    def get_info(self):
        if self.info:
            return self.info
        cmd = ['ffprobe', self.media.path]
        cmd += ['-show_streams']
        cmd += ['-select_streams', str(self.index)]
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to get info from {self} with ffmpeg:\n{errors}")
        output = result.stdout.decode('utf-8')
        self.info = json.loads(output)['streams']
        self.info.setdefault('tags', {})
        return self.info

    def get_duration(self):
        info = self.get_info()
        if 'duration' in info:
            return float(info['duration'])
        self.warnings.add("Stream has no `duration` information.")
        info = self.media.get_info()
        if 'duration' in info:
            return float(info['duration'])
        raise Exception("Could not determine stream duration.")

    def get_packets(self):
        if self.packets:
            return self.packets
        cmd = ['ffprobe', self.media.path]
        cmd += ['-show_packets']
        cmd += ['-select_streams', str(self.index)]
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to get packets from {self} with ffmpeg:\n{errors}")
        output = result.stdout.decode('utf-8')
        self.packets = json.loads(output)['packets']
        return self.packets

    def get_packet(self, index):
        if self.packets:
            return self.packets[index]
        cmd = ['ffprobe', self.media.path]
        cmd += ['-show_packets']
        cmd += ['-select_streams', str(self.index)]
        cmd += ['-read_intervals', f'%+#{index+1}']
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to get packets from {self} with ffmpeg:\n{errors}")
        output = result.stdout.decode('utf-8')
        packet = json.loads(output)['packets'][index]
        return packet

    def detect_language(self, opts=DEF_OPTS_LANGUAGE):
        opts = DEF_OPTS_LANGUAGE if opts is None else opts
        codec_type = self.get_info()['codec_type']
        if codec_type == 'audio':
            return self.detect_audio_language(opts)
        if codec_type == 'subtitle':
            return self.detect_subtitle_language(opts)

    def detect_audio_language(self, opts=DEF_OPTS_LANGUAGE):
        """
        Detect language of an audio stream using OpenAI Whisper.
        """
        assert(self.is_audio())
        debug = logging.getLogger().level == logging.DEBUG
        logging.debug(f'Detecting audio language in stream #{self.index} of media: "{self.media.name}"')

        import whisper
        from whisper.audio import CHUNK_LENGTH
        model = whisper.load_model("base")

        # Calculate number of samples
        duration = self.get_duration()
        len_samples = float(CHUNK_LENGTH)
        num_samples = min(opts['max_audio_samples'], int(duration / len_samples))

        results = {}
        with tempfile.TemporaryDirectory() as tmp:
            ext = self.media.ext
            for index in range(num_samples):
                # Extract sample
                sample = os.path.join(tmp, f'sample{index:04d}.{ext}')
                cmd = ['ffmpeg', '-i', self.media.path, '-map', f'0:{self.index}']
                cmd += ['-c:a', 'copy']
                cmd += ['-ss', str(index * duration / num_samples)]
                cmd += ['-t', str(len_samples)]
                cmd += [sample]
                result = subprocess.run(cmd, capture_output=True)
                if result.returncode != 0:
                    errors = result.stderr.decode('utf-8')
                    raise Exception(f"Failed to extract audio sample from {self.media.path} with ffmpeg:\n{errors}")

                # Detect language in sample
                audio = whisper.load_audio(sample)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio).to(model.device)
                _, probs = model.detect_language(mel)
                if debug:
                    highest_probs = dict(collections.Counter(probs).most_common(5))
                    highest_probs_rounded = { k: f'{v:.4f}' for k, v in highest_probs.items() }
                    logging.debug(f'Sample #{index:02d}: {highest_probs_rounded}')
                lang = max(probs, key=probs.get)
                prob = probs[lang]
                if opts['min_score'] <= prob:
                    results.setdefault(lang, []).append(prob)

        # Compute final scores as votes+avg(prob)
        results = { k: len(v) + sum(v)/len(v) for k, v in results.items() }
        if not results:
            return None

        # Rename keys since OpenAI Whisper does not fully adhere to ISO 639-1
        replacements = [('jw', 'jv')]
        for old, new in replacements:
            if old in results:
                results[new] = results.pop(old)

        # Optionally merge into ISO 639-3 macrolanguages and return highest ocurring
        if opts['only_macrolanguages']:
            macro_results = {}
            for key, value in results.items():
                part3 = iso639.Lang(pt1=key).pt3
                macro = iso639.Lang(pt1=key).macro()
                lang = macro.pt3 if macro else part3
                macro_results[lang] = macro_results.get(lang, 0) + value
            lang = max(macro_results, key=macro_results.get)
            return lang

        # Get highest occurring language and convert ISO 639-1 to ISO 639-3
        lang = max(results, key=results.get)
        lang = iso639.Lang(pt1=lang).pt3
        return lang

    def detect_subtitle_language(self, opts=DEF_OPTS_LANGUAGE):
        """
        Detect subtitle language copying/converting to SRT,
        extracting the raw text and detecting its language.
        """
        assert(self.is_subtitle())

        # Detect subtitle language
        def srt_language(path):
            with open(path, 'rb') as f:
                enc = chardet.detect(f.read())['encoding']
            subs = pysrt.open(path, encoding=enc)
            text = ' '.join(map(lambda x: x.text, subs))
            lang = langid.classify(text)[0]
            lang = iso639.Lang(pt1=lang).pt3
            return lang

        # Check if the parent media is already an SRT file
        path = self.media.path
        if self.media.ext == 'srt':
            return srt_language(path)

        # Otherwise extract subtitle stream, converting to SRT
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, 'output.srt')
            cmd = ['ffmpeg', '-i', path, '-map', f'0:{self.index}']
            if self.get_info()['codec_name'] == 'srt':
                cmd += ['-c:s', 'copy']
            cmd += [output]
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to extract subtitles from {path} with ffmpeg:\n{errors}")
            return srt_language(output)
