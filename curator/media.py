#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import json
import os
import subprocess
import tempfile

from iso639 import languages

# Extensions
VIDEO_EXTENSIONS = ['avi', 'flv', 'mkv', 'mov', 'mp4', 'mpg', 'wmv']
AUDIO_EXTENSIONS = ['mp3', 'aac', 'ogg']
TEXTS_EXTENSIONS = ['srt', 'ass']

class Media:
    # Type
    TYPE_FILE = 1
    TYPE_LINK = 2

    # Stream
    STREAM_VIDEO = 1
    STREAM_AUDIO = 2
    STREAM_TEXTS = 3

    def __init__(self, path, type=None, stream=None):
        self.path = path
        self.stream = stream

        # Detect regular file or link
        if type is None:
            if os.path.isfile(path):
                self.type = Media.TYPE_FILE
            elif os.path.islink(path):
                self.type = Media.TYPE_LINK
        else:
            self.type = type

        # Cache directory, filename and extension
        root, ext = os.path.splitext(path)
        self.name = os.path.basename(path)
        self.dir = os.path.dirname(root)
        self.ext = ext[1:]

        # Cache stream information
        self.stream_info = None

    def has_video_ext(self):
        return self.ext in VIDEO_EXTENSIONS

    def has_audio_ext(self):
        return self.ext in AUDIO_EXTENSIONS

    def get_stream_info(self):
        if self.stream_info:
            return self.stream_info
        cmd = ['ffprobe', self.path]
        cmd += ['-show_streams']
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Failed get info from {self.path} with ffmpeg")
        output = result.stdout.decode('utf-8')
        info = json.loads(output)
        if self.stream:
            self.stream_info = info['streams'][self.stream]
        else:
            self.stream_info = info['streams']
        return self.stream_info

    def detect_language(self):
        if self.stream is None:
            raise Exception(f"Cannot detect language in containers. Specify an individual stream.")
        codec_type = self.get_stream_info()['codec_type']
        if codec_type == 'audio':
            return detect_audio_language(self)
        if codec_type == 'subtitle':
            return 'TODO'

    def __repr__(self):
        return f'Media("{self.path}")'

def media_input(paths, recursive=False):
    media = []
    for path in paths:
        if os.path.isfile(path):
            media.append(Media(path))
            continue
        for path in glob.glob(path, recursive=recursive):
            if os.path.isfile(path):
                media.append(Media(path))
    return media

def detect_audio_language(media, max_samples=10):
    """
    Detect language of an audio stream using OpenAI Whisper.
    """
    import whisper
    from whisper.audio import CHUNK_LENGTH
    model = whisper.load_model("base")

    # Calculate number of samples
    info = media.get_stream_info()
    duration = float(info['duration'])
    len_samples = float(CHUNK_LENGTH)
    num_samples = min(max_samples, int(duration / len_samples))

    results = {}
    with tempfile.TemporaryDirectory() as tmp:
        ext = info['codec_name']
        for index in range(num_samples):
            # Extract sample
            sample = os.path.join(tmp, f'sample{index:04d}.{ext}')
            cmd = ['ffmpeg', '-i', media.path, '-map', f'0:{media.stream}']
            cmd += ['-c', 'copy']
            cmd += ['-ss', str(index * duration / num_samples)]
            cmd += ['-t', str(len_samples)]
            cmd += [sample]
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                raise Exception(f"Failed extract audio sample from {self.path} with ffmpeg")

            # Detect language
            audio = whisper.load_audio(sample)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            _, probs = model.detect_language(mel)
            lang = max(probs, key=probs.get)
            results[lang] = results.get(lang, 0) + 1

    # Get highest occurring language and convert ISO 639-1 to ISO 639-3
    lang = max(results, key=probs.get)
    lang = languages.get(part1=lang).part3
    return lang
