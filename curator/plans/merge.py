#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import os
import subprocess

from curator import Plan, Task, Media

class MergePlan(Plan):
    def show_tasks(self):
        thead = ("Inputs", "→", "Output")
        tbody = []
        for task in self.tasks:
            tbody.append((task.inputs[0].name, "→", task.outputs[0].name))
            for minput in task.inputs[1:]:
                tbody.append((minput.name, "↗", ""))
        return thead, tbody

class MergeTask(Task):
    def __init__(self, inputs, output, format, delete):
        super().__init__(inputs, [output])
        self.format = format
        self.delete = delete
    
    def apply(self):
        # Build ffmpeg command
        cmd = ['ffmpeg']
        for minput in self.inputs:
            cmd += ['-i', minput.path]
        for i in range(len(self.inputs)):
            cmd += ['-map', str(i)]
        cmd += ['-c', 'copy']

        # Reencode MP4/TX3G to MKV/SRT
        if self.inputs[0].ext == 'mp4' and self.format == 'mkv':
            cmd += ['-c:s', 'srt']

        # Create output file
        cmd += [self.outputs[0].path]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            raise Exception(f"Failed to merge into {self.outputs[0].name} with ffmpeg")
        if self.delete:
            for media in self.inputs:
                os.remove(media.path)

def plan_merge(media, format, delete=False):
    plan = MergePlan()
    cur_video = None
    cur_task = None
    for m in media:
        if m.has_video_ext():
            basename, _ = os.path.splitext(m.name)
            basepath, _ = os.path.splitext(m.path)
            cur_output = Media(f'{basepath}.{format}', Media.TYPE_FILE)
            cur_video = basename
            cur_task = MergeTask([m], cur_output, format, delete)
            continue
        elif cur_task and cur_video in m.name:
            cur_task.inputs.append(m)
            continue
        elif cur_task and len(cur_task.inputs) >= 2:
            plan.add_task(cur_task)
        cur_task = None
    if cur_task and len(cur_task.inputs) >= 2:
        plan.add_task(cur_task)
    return plan
