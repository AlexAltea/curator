import logging
import os
import subprocess
import tempfile

from curator import Plan, Task, Media
from curator.util import flatten

class ConvertPlan(Plan):
    def columns(self):
        return [
            { 'name': 'Inputs', 'width': '50%' },
            { 'name': '→', 'width': '1' },
            { 'name': "Output", 'width': '50%' },
        ]

class ConvertTask(Task):
    def __init__(self, input, output, format, delete=False):
        super().__init__([input], [output])
        assert(output.type == Media.TYPE_FILE)
        self.format = format
        self.delete = delete
        self.fflags = set()
        self.cflags = set()
        self.mflags = set()
        self.unpack_bframes = False
        self.skip_subtitles = False

    def view(self):
        return [(self.inputs[0].name, "→", self.outputs[0].name)]

    def apply(self):
        temp = None
        # Solve conflict when -fflags +genpts and -bsf:v mpeg4_unpack_bframes are both enabled
        input_media = self.inputs[0].path
        if self.unpack_bframes and '+genpts' in self.fflags:
            temp = tempfile.TemporaryDirectory(dir=self.inputs[0].dir, prefix='.temp-curator-')
            fixed_media = os.path.join(temp.name, "media.avi")
            cmd = ['ffmpeg']
            cmd += ['-i', input_media]
            cmd += ['-c:v', 'copy']
            cmd += ['-c:a', 'copy']
            cmd += ['-bsf:v', 'mpeg4_unpack_bframes']
            cmd += ['-map', '0']
            if self.skip_subtitles:
                cmd += ['-map', '-0:s']
            cmd += ['-map_metadata', '0']
            cmd += ['-movflags', 'use_metadata_tags']
            cmd += [fixed_media]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to generate PTS for {self.inputs[0].name} with ffmpeg:\n{errors}")
            input_media = fixed_media

        # Build ffmpeg command
        cmd = ['ffmpeg']
        if self.fflags:
            cmd += ['-fflags', ''.join(self.fflags)]
        cmd += ['-i', input_media]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']
        cmd += ['-c:d', 'copy']
        cmd += ['-c:t', 'copy']
        if self.cflags:
            cmd += flatten(self.cflags)
        if self.unpack_bframes and '+genpts' not in self.fflags:
            cmd += ['-bsf:v', 'mpeg4_unpack_bframes']
        cmd += ['-map', '0']
        if self.skip_subtitles:
            cmd += ['-map', '-0:s']
        if self.mflags:
            cmd += flatten(self.mflags)
        cmd += ['-map_metadata', '0']
        cmd += ['-movflags', 'use_metadata_tags']

        # Create output file
        output = self.outputs[0].path
        cmd += [output]
        result = subprocess.run(cmd, capture_output=True)
        if temp:
            temp.cleanup()
        if result.returncode != 0:
            if os.path.exists(output):
                os.remove(output)
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to convert to {output} with ffmpeg:\n{errors}")
        if self.delete:
            os.remove(self.inputs[0].path)

    def add_fflag(self, flag):
        self.fflags.add(flag)

    def add_cflag(self, flag):
        self.cflags.add(flag)

    def add_mflag(self, flag):
        self.mflags.add(flag)

def plan_convert(media, format, delete=False):
    plan = ConvertPlan()
    for m in media:
        root, ext = os.path.splitext(m.path)
        output_path = f'{root}.{format}'
        if os.path.exists(output_path):
            logging.debug(f'Skipping existing output: {output_path}')
            continue
        output_media = Media(output_path, Media.TYPE_FILE)
        task = ConvertTask(m, output_media, format, delete)

        # Tweaks for mismatching formats
        if m.get_info()['format_name'] in ('avi', 'ogg') and m.has_video():
            task.add_warning(f'Media contains packets without PTS data.')
            task.add_fflag('+genpts')
        if m.get_info()['format_name'] == 'avi' and m.has_video_codec('h264'):
            task.add_error('AVI contains H264 stream. Unpacking is required, but not supported.')
        if m.get_info()['format_name'] == 'avi' and m.has_subtitle():
            task.skip_subtitles = True
            task.add_warning('AVI contains subtitles. Conversion is not supported.')
        if m.has_packed_bframes():
            task.unpack_bframes = True
            task.add_warning(f'Media contains packed B-frames. Unpacking is required.')
        if format == 'mkv':
            for stream in m.get_streams():
                if stream.get_info()['codec_type'] == "subtitle" and \
                   stream.get_info()['codec_name'] == "mov_text":
                    task.add_warning(f'Conversion requires reencoding {stream}. Styles will be removed.')
                    task.add_cflag(('-c:s', 'text'))
        if format == 'mkv':
            for stream in m.get_streams():
                if stream.get_info()['codec_type'] == "data" and \
                   stream.get_info()['tags']['handler_name'] == "SubtitleHandler":
                    task.add_warning('Chapters have been included in {stream}. Stream will be dropped, but chapters might be carried over by ffmpeg.')
                    task.add_mflag(('-map', f'-0:{stream.index}'))
                if stream.get_info()['codec_type'] == "data" and \
                   stream.get_info()['tags']['handler_name'] == "Time Code Media Handler":
                    task.add_warning('Chapters have been included in {stream}. Stream will be dropped.')
                    task.add_mflag(('-map', f'-0:{stream.index}'))
        plan.add_task(task)
    return plan
