import json
import os
import subprocess
import tempfile

import chardet
import iso639
import langid
import pysrt

# Default options
DEF_OPTS_LANGUAGE = {
    'only_macrolanguages': False
}

class Stream:
    def __init__(self, media, index, info=None):
        self.media = media
        self.index = index

        # Cache stream information
        self.info = info

        # Store warnings about the stream
        self.warnings = set()

    def __repr__(self):
        return f'Stream("{self.path}", index={self.index})'

    def is_video(self):
        return self.get_info()['codec_type'] == 'video'

    def is_audio(self):
        return self.get_info()['codec_type'] == 'audio'

    def is_subtitle(self):
        return self.get_info()['codec_type'] == 'subtitle'

    def get_info(self):
        if self.info:
            return self.info
        cmd = ['ffprobe', self.path]
        cmd += ['-show_streams']
        cmd += ['-select_streams', str(self.index)]
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Failed get info from {self.path} with ffmpeg")
        output = result.stdout.decode('utf-8')
        self.info = json.loads(output)['streams']
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

    def detect_language(self, opts=DEF_OPTS_LANGUAGE):
        opts = DEF_OPTS_LANGUAGE if opts is None else opts
        codec_type = self.get_info()['codec_type']
        if codec_type == 'audio':
            return self.detect_audio_language(opts)
        if codec_type == 'subtitle':
            return self.detect_subtitle_language(opts)

    def detect_audio_language(self, opts, max_samples=10):
        """
        Detect language of an audio stream using OpenAI Whisper.
        """
        assert(self.is_audio())

        import whisper
        from whisper.audio import CHUNK_LENGTH
        model = whisper.load_model("base")

        # Calculate number of samples
        duration = self.get_duration()
        len_samples = float(CHUNK_LENGTH)
        num_samples = min(max_samples, int(duration / len_samples))

        results = {}
        with tempfile.TemporaryDirectory() as tmp:
            ext = self.get_info()['codec_name']
            for index in range(num_samples):
                # Extract sample
                sample = os.path.join(tmp, f'sample{index:04d}.{ext}')
                cmd = ['ffmpeg', '-i', self.media.path, '-map', f'0:{self.index}']
                cmd += ['-c', 'copy']
                cmd += ['-ss', str(index * duration / num_samples)]
                cmd += ['-t', str(len_samples)]
                cmd += [sample]
                result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result.returncode != 0:
                    raise Exception(f"Failed to extract audio sample from {self.media.path} with ffmpeg")

                # Detect language
                audio = whisper.load_audio(sample)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio).to(model.device)
                _, probs = model.detect_language(mel)
                lang = max(probs, key=probs.get)
                results[lang] = results.get(lang, 0) + 1

        # Rename keys since OpenAI Whisper does not fully adhere to ISO 639-1
        replacements = [('jw', 'jv')]
        for old, new in replacements:
            results[new] = results.pop(old)

        # Optionally merge into ISO 639-3 macrolanguages and return highest ocurring
        if opts['only_macrolanguages']:
            macro_results = {}
            for key, value in results.items():
                part3 = iso639.languages.get(part1=key).part3
                macro = iso639.languages.get(part1=key).macro
                lang = macro if macro else part3
                macro_results[lang] = macro_results.get(lang, 0) + value
            lang = max(macro_results, key=macro_results.get)
            return lang

        # Get highest occurring language and convert ISO 639-1 to ISO 639-3
        lang = max(results, key=results.get)
        lang = iso639.languages.get(part1=lang).part3
        return lang

    def detect_subtitle_language(self, opts):
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
            lang = iso639.languages.get(part1=lang).part3
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
                raise Exception(f"Failed to extract subtitles from {path} with ffmpeg")
            return srt_language(output)
