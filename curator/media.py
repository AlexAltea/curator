#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import os

# Extensions
VIDEO_EXTENSIONS = ['.avi', '.flv', '.mkv', '.mov', '.mp4', '.mpg', '.wmv']
AUDIO_EXTENSIONS = ['.mp3', '.aac', '.ogg']
TEXTS_EXTENSIONS = ['.srt', '.ass']

# Stream TYp
STREAM_VIDEO = 1
STREAM_AUDIO = 2
STREAM_TEXTS = 3

class Media:
    def __init__(self, path, stream=None):
        self.path = path
        self.stream = stream

        # Cache directory, filename and extension
        root, ext = os.path.splitext(path)
        self.name = os.path.basename(path)
        self.dir = os.path.dirname(root)
        self.ext = ext[1:]

    def __repr__(self):
        return f'Media("{self.path}")'

def media_input(paths, recursive=False):
    media = []
    for path in paths:
        for path in glob.glob(path, recursive=recursive):
            if os.path.isfile(path):
                media.append(Media(path))            
    return media
