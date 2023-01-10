#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import json
import os
import subprocess

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

    def has_video_ext(self):
        return self.ext in VIDEO_EXTENSIONS

    def has_audio_ext(self):
        return self.ext in AUDIO_EXTENSIONS

    def get_stream_info(self):
        assert(self.stream is None)
        cmd = ['ffprobe', self.path]
        cmd += ['-show_streams']
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to merge into {self.outputs[0].name} with ffmpeg")
        info = json.loads(result.stdout)
        return info['streams']

    def __repr__(self):
        return f'Media("{self.path}")'

def media_input(paths, recursive=False):
    media = []
    for path in paths:
        for path in glob.glob(path, recursive=recursive):
            if os.path.isfile(path):
                media.append(Media(path))            
    return media
