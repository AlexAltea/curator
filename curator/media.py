import glob
import json
import os
import subprocess

from .stream import *

# Extensions
VIDEO_EXTENSIONS = ['avi', 'flv', 'mkv', 'mov', 'mp4', 'mpg', 'wmv']
AUDIO_EXTENSIONS = ['mp3', 'aac', 'ogg']
TEXTS_EXTENSIONS = ['srt', 'ass']

class Media:
    # Type
    TYPE_FILE = 1
    TYPE_LINK = 2

    def __init__(self, path, type=None):
        self.path = path

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

        # Cache media information
        self.streams = None
        self.info = None

    def has_video_ext(self):
        return self.ext in VIDEO_EXTENSIONS

    def has_audio_ext(self):
        return self.ext in AUDIO_EXTENSIONS

    def has_subtitle_ext(self):
        return self.ext in TEXTS_EXTENSIONS

    def get_streams(self):
        if self.streams is not None:
            return self.streams

        # Obtain information about streams within media
        cmd = ['ffprobe', self.path]
        cmd += ['-show_streams']
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Failed get info from {self.path} with ffmpeg")
        output = result.stdout.decode('utf-8')
        streams_info = json.loads(output)['streams']

        # Create and return stream objects
        streams = []
        for stream_info in streams_info:
            stream = Stream(self, stream_info['index'], stream_info)
            streams.append(stream)
        self.streams = streams
        return streams

    def get_info(self):
        if self.info:
            return self.info
        cmd = ['ffprobe', self.path]
        cmd += ['-show_format']
        cmd += ['-of', 'json']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            raise Exception(f"Failed get info from {self.path} with ffmpeg")
        output = result.stdout.decode('utf-8')
        self.info = json.loads(output)['format']
        return self.info

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
