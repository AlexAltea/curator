#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import os
import ffmpeg

from curator import Plan, Task, Media

class MergePlan(Plan):
    def handle_task(self, task):
        task.apply()

    def show_tasks(self):
        thead = ("Input", "→", "Output")
        tbody = []
        for task in self.tasks:
            tbody.append((task.inputs[0].name, "→", task.outputs[0].name))
            for minput in task.inputs[1:]:
                tbody.append((minput.name, "↗", ""))
        return thead, tbody

class MergeTask(Task):
    def __init__(self, inputs, output, delete):
        super().__init__(inputs, [output])
        self.delete = delete
    
    def apply(self):
        print('MergeTask::apply')

def plan_merge(media, output, delete=False):
    plan = MergePlan()
    cur_video = None
    cur_task = None
    for m in media:
        print(m.name)
        if m.has_video_ext():
            basename, _ = os.path.splitext(m.name)
            basepath, _ = os.path.splitext(m.path)
            cur_output = Media(f'{basepath}.{output}', Media.TYPE_FILE)
            cur_video = basename
            cur_task = MergeTask([m], cur_output, delete)
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
