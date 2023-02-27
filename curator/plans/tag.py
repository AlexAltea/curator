import collections
import os
import subprocess
import tempfile
import shutil

from curator import Plan, Task, Media
from curator.util import *

class TagPlan(Plan):
    def columns(self):
        return [
            { 'name': 'Name', 'width': '50%' },
            { 'name': 'Stream', 'width': '6' },
            { 'name': "Old", 'width': '25%' },
            { 'name': '→', 'width': '1' },
            { 'name': "New", 'width': '25%' },
        ]

    def optimize(self):
        tasks = []
        last_id = 0
        last_task = None
        for task in self.tasks:
            if last_task and last_task.inputs == task.inputs:
                last_task.combine(task)
            else:
                last_id += 1
                last_task = task
                tasks.append(task)
                task.id = last_id
        self.tasks = tasks

class TagTask(Task):
    TagUpdate = collections.namedtuple('TagUpdate', ('index', 'tag', 'old', 'new'))

    def __init__(self, input):
        super().__init__([input], [])
        self.updates = []
        self.use_mkvpropedit = False
        self.path_mkvpropedit = None

    def combine(self, other):
        super().combine(other)
        self.updates += other.updates

    def view(self):
        rows = []
        for update in self.updates:
            rows.append([self.inputs[0].name, str(update.index), str(update.old), "→", str(update.new)])
        return rows

    def add_update(self, index, tag, old, new=None):
        self.updates.append(self.TagUpdate(index, tag, old, new))

    def apply(self):
        if self.use_mkvpropedit and self.path_mkvpropedit:
            self.apply_with_mkvpropedit()
            return

        m = self.inputs[0]
        cmd = ['ffmpeg']
        cmd += ['-i', m.path]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']
        cmd += ['-map', '0']
        cmd += ['-map_metadata', '0']

        for update in self.updates:
            cmd += [f'-metadata:s:{update.index}', f'{update.tag}={update.new}']

            # Tweaks
            s = m.get_streams()[update.index]
            if m.is_format('avi') and update.tag == 'language':
                if (audio_index := s.audio_index()) not in range(9):
                    raise Exception("RIFF IASx tags should only support up to 9 audio tracks")
                cmd += ['-metadata', f'IAS{audio_index + 1}={update.new}']

        with tempfile.TemporaryDirectory(dir=m.dir, prefix='.temp-curator-') as tmp:
            output = os.path.join(tmp, f'output.{m.ext}')
            cmd += [output]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode != 0:
                errors = result.stderr.decode('utf-8')
                raise Exception(f"Failed to update tags in {m.name} with ffmpeg:\n{errors}")
            os.replace(output, m.path)

    def apply_with_mkvpropedit(self):
        m = self.inputs[0]
        cmd = [self.path_mkvpropedit, m.path]
        cmd += ['--disable-language-ietf'] # Fix error 0xc00d3e8c in Windows Movies & TV app
        for update in self.updates:
            cmd += ['--edit', f'track:{update.index+1}']
            cmd += ['--set', f'{update.tag}={update.new}']
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            errors = result.stderr.decode('utf-8')
            raise Exception(f"Failed to update tags in {m.name} with mkvpropedit:\n{errors}")

def tag_value(stream, tag, opts=None):
    try:
        if tag == 'language':
            return stream.detect_language(opts)
    except Exception as e:
        print(f'Could not process {stream.media.path}')
    return None

def plan_tag(media, stype, tag, value=None, skip_tagged=False, opts=None):
    path_mkvpropedit = find_executable('mkvpropedit', [
        'C:/Program Files/MKVToolNix/mkvpropedit.exe',
        'C:/Program Files (x86)/MKVToolNix/mkvpropedit.exe',
    ])
    plan = TagPlan()
    for m in media:
        # Skip files with formats that do not support tagging
        if m.is_format('subviewer'):
            continue

        for stream in m.get_streams():
            # Filter streams and get old tag value
            stream_info = stream.get_info()
            if stream_info['codec_type'] not in ('audio', 'subtitle'):
                continue
            if stype != 'all' and stream_info['codec_type'] != stype:
                continue
            stream_value = stream_info['tags'].get(tag) or \
                           stream_info['tags'].get(tag.lower()) or \
                           stream_info['tags'].get(tag.upper())
            if skip_tagged and stream_value is not None:
                continue

            # Create tag update task
            task = TagTask(m)
            if m.is_format('avi'):
                task.add_warning("Modifying AVI metadata might affect stream synchronization.")
                if tag == 'languge' and stream.get_info()['codec_type'] == 'audio' and stream.audio_index() > 8:
                    task.add_error("Cannot change AVI audio stream using IASx tags. Index out of range.")
            if m.is_format('matroska'):
                task.use_mkvpropedit = True
                task.path_mkvpropedit = path_mkvpropedit
            old_value = stream_value
            new_value = value if value is not None else tag_value(stream, tag, opts)
            if old_value != new_value and new_value is not None:
                task.add_update(stream.index, tag, old_value, new_value)
                plan.add_task(task)
    return plan
