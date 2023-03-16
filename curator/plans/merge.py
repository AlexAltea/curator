import fractions
import logging
import os
import subprocess
import tempfile

from curator import Plan, Task, Media

# Default options
DEF_OPTS_MERGE = {
    # Video selection
    'try_video_criteria': ['resolution', 'codec', 'fps', 'length'],
    'try_video_codecs': ['hevc', 'h264', 'mpeg4'],
    'min_video_resolution': None,
    'max_video_resolution': None,
    'min_video_bitrate': None,
    'max_video_bitrate': None,

    # Audio selection
    'try_audio_criteria': ['codec', 'bitrate', 'channels'],
    'try_audio_codecs': ['flac', 'dts', 'eac3', 'ac3', 'mp3'],
    'min_audio_bitrate': None,
    'max_audio_bitrate': None,

    # Subtitle selection
    'try_subtitle_criteria': [],
}

class MergePlan(Plan):
    def columns(self):
        return [
            { 'name': 'Inputs', 'width': '50%' },
            { 'name': '→', 'width': '1' },
            { 'name': "Output", 'width': '50%' },
        ]

    def validate(self):
        # Overriding Plan.validate since MergePlans allow for inplace merges
        # where the output already exists in the filesystem.
        outputs = set()
        for task in self.tasks:
            for output in task.outputs:
                path = output.path
                if path in outputs:
                    task.add_error(f'Output {path} already exists in the plan')
                outputs.add(path)

class MergeTask(Task):
    def __init__(self, inputs, output, format, delete):
        super().__init__(inputs, [output])
        self.format = format
        self.delete = delete
        self.selected_streams = []

    def view(self):
        rows = []
        for m in self.inputs:
            rows.append((m.name,
                '↗' if rows else '→',
                ' ' if rows else self.outputs[0].name,
            ))
            for stream in self.selected_streams:
                if stream.media == m:
                    rows.append((f' - {stream}', '↗', ''))
        return rows

    def select_streams(self, video, audio, subtitle):
        self.selected_streams = [video]
        self.selected_streams += audio
        self.selected_streams += subtitle

    def apply(self):
        # Build ffmpeg command
        cmd = ['ffmpeg']
        for minput in self.inputs:
            cmd += ['-i', minput.path]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']
        for stream in self.selected_streams:
            index_m = self.inputs.index(stream.media)
            index_s = stream.index
            cmd += ['-map', f'{index_m}:{index_s}']

        # Create output file
        output = self.outputs[0]
        with tempfile.TemporaryDirectory(dir=output.dir, prefix='.temp-curator-') as tmp:
            output_tmp = os.path.join(tmp, f'output.{output.ext}')
            cmd += [output_tmp]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to merge into {output.name} with ffmpeg:\n{errors}")
            os.replace(output_tmp, output.path)
            if self.delete:
                for media in self.inputs:
                    if media.path == output.path:
                        continue # Do not accidentally remove output after in-place merges
                    os.remove(media.path)

def select_codec(s1, s2, codec_list):
    codec_scores = { codec: len(codec_list) - index for index, codec in codec_list }
    s1_codec = s1.get_info()['codec_name']
    s2_codec = s2.get_info()['codec_name']
    s1_codec_score = codec_scores.get(s1_codec, 0)
    s2_codec_score = codec_scores.get(s2_codec, 0)
    if s1_codec_score == 0:
        logging.warning(f"Select criteria does not consider codec {s1_codec} in stream {s1}")
    if s2_codec_score == 0:
        logging.warning(f"Select criteria does not consider codec {s2_codec} in stream {s2}")
    if s1_codec_score > s2_codec_score:
        return s1
    if s2_codec_score > s1_codec_score:
        return s2
    return None

def select_video_stream(s1, s2, opts=DEF_OPTS_MERGE):
    if s1 is None:
        return s2
    if s2 is None:
        return s1
    for criterion in opts['try_video_criteria']:
        # Resolution:
        # - Consider width as some sources include black bars which might increase the height.
        # - Only consider 10% increases as meaningful enough to trigger this criterion.
        if criterion == 'resolution':
            if s1.get_info()['width'] / s2.get_info()['width'] > 1.1:
                return s1
            if s2.get_info()['width'] / s1.get_info()['width'] > 1.1:
                return s2
        # Codec
        elif criterion == 'codec':
            stream = select_codec(s1, s2, opts['try_video_codecs'])
            if stream is not None:
                return stream
        # Frames
        elif criterion == 'fps':
            if fractions.Fraction(s1.get_info()['avg_frame_rate']) < \
               fractions.Fraction(s2.get_info()['avg_frame_rate']):
                return s1
            if fractions.Fraction(s2.get_info()['avg_frame_rate']) < \
               fractions.Fraction(s1.get_info()['avg_frame_rate']):
                return s2
        else:
            raise Exception(f"Unknown video selection criterion: {criterion}")
    logging.warning(f'Video criteria could not select between {s1} and {s2}')
    return s1

def select_audio_stream(s1, s2, opts=DEF_OPTS_MERGE):
    for criterion in opts['try_audio_criteria']:
        # Codec
        if criterion == 'codec':
            stream = select_codec(s1, s2, opts['try_audio_codecs'])
            if stream is not None:
                return stream
        # Bitrate
        elif criterion == 'bitrate':
            if int(s1.get_info()['bit_rate']) > int(s2.get_info()['bit_rate']):
                return s1
            if int(s2.get_info()['bit_rate']) > int(s1.get_info()['bit_rate']):
                return s2
        # Channels
        elif criterion == 'channels':
            if s1.get_info()['channels'] > s2.get_info()['channels']:
                return s1
            if s2.get_info()['channels'] > s1.get_info()['channels']:
                return s2
        else:
            raise Exception(f"Unknown video selection criterion: {criterion}")
    logging.warning(f'Audio criteria could not select between {s1} and {s2}')
    return s1

def select_subtitle_stream(s1, s2, opts=DEF_OPTS_MERGE):
    for criterion in opts['try_subtitle_criteria']:
        pass
    logging.warning(f'Subtitle criteria could not select between {s1} and {s2}')
    return s1

def find_related(target, media):
    basename, _ = os.path.splitext(target.name)
    matches = []
    for m in media:
        if basename in m.name and m is not target:
            matches.append(m)
    return matches

def plan_merge(media, format, delete=False, opts=DEF_OPTS_MERGE):
    plan = MergePlan()
    # Identify related files
    for m in media:
        if not m.is_format('matroska'):
            continue
        basepath, _ = os.path.splitext(m.path)
        output = Media(f'{basepath}.{format}', Media.TYPE_FILE)
        related = find_related(m, media)
        if len(related) >= 1:
            task = MergeTask([m] + related, output, format, delete)
            plan.add_task(task)
    # Choose which streams to preserve starting with video
    for task in plan:
        video_stream = None
        for s in task.input_video_streams():
            video_stream = select_video_stream(video_stream, s)
        # Then audio
        audio_streams = []
        for curr in task.input_audio_streams():
            inserted = False
            for index, prev in enumerate(audio_streams):
                curr_lang = curr.get_info()['tags'].get('language')
                prev_lang = prev.get_info()['tags'].get('language')
                if curr_lang == prev_lang != None:
                    audio_streams[index] = select_audio_stream(prev, curr)
                    inserted = True
                    break
            if not inserted:
                audio_streams.append(curr)
        # Then subtitles
        subtitle_streams = []
        for s in task.input_subtitle_streams():
            inserted = False
            for index, prev in enumerate(subtitle_streams):
                curr_lang = curr.get_info()['tags'].get('language')
                prev_lang = prev.get_info()['tags'].get('language')
                if curr_lang == prev_lang != None:
                    subtitle_streams[index] = select_subtitle_stream(prev, curr)
                    inserted = True
                    break
            if not inserted:
                subtitle_streams.append(curr)
        task.select_streams(video_stream, audio_streams, subtitle_streams)
    return plan
