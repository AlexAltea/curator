#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import os
import subprocess
import tempfile

from curator.analysis import *
from curator import Plan, Task, Media

class TagPlan(Plan):
    def show_tasks(self):
        thead = ("Name", "Stream", "Old tag", "→", "New tag")
        tbody = []
        for task in self.tasks:
            m = task.inputs[0]
            tbody.append((m.name, str(m.stream), task.old_value, "→", task.new_value))
        return thead, tbody

class TagTask(Task):
    def __init__(self, input, tag, old_value, new_value=None):
        super().__init__([input], [])
        self.tag = tag
        self.old_value = old_value
        self.new_value = new_value

    def apply(self):
        m = self.inputs[0]
        cmd = ['ffmpeg']
        cmd += ['-i', m.path]
        cmd += ['-c:v', 'copy']
        cmd += ['-c:a', 'copy']
        cmd += ['-c:s', 'copy']
        cmd += [f'-metadata:s:{m.stream}', f'{self.tag}={self.new_value}']
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, f'output.{m.ext}')
            cmd += [output]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to update tags in {m.name} with ffmpeg:\n{result.stderr}")
            os.replace(output, m.path)

    def set_new_value(self, new_value):
        self.new_value = new_value

def plan_tag(media, stype, tag, value=None, skip_tagged=False):
    # Locate relevant streams
    plan = TagPlan()
    tasks = []
    for m in media:
        if m.has_video_ext():
            for stream in m.get_stream_info():
                if stream['codec_type'] != stype:
                    continue
                stream_index = stream['index']
                stream_value = stream['tags'].get(tag)
                if skip_tagged and stream_value is not None:
                    continue
                stream = Media(m.path, Media.TYPE_FILE, stream=stream_index)
                task = TagTask(stream, tag, stream_value)
                tasks.append(task)
    # Set or auto-detect value
    if value:
        for task in tasks:
            task.set_new_value(value)
    elif tag == 'language':
        for task in tasks:
            lang = task.inputs[0].detect_language()
            task.set_new_value(lang)
    # Prepare plan with changes
    for task in tasks:
        if task.old_value != task.new_value:
            plan.add_task(task)
    return plan