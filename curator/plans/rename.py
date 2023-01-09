#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import logging
import os

from curator.analysis import *
from curator import Plan, Task, Media

class RenamePlan(Plan):
    def handle_task(self, task):
        media, name = task
        src = media.path
        dst = os.path.join(media.dir, name)
        os.rename(src, dst)

    def show_tasks(self):
        thead = ("Old", "→", "New")
        tbody = []
        for task in self.tasks:
            media, name = task
            tbody.append((media.name, "→", name))
        return thead, tbody

class RenameTask(Task):
    def __init__(self, input, output):
        super().__init__([input], [output])

    def apply(self):
        src = self.inputs[0].path
        dst = self.outputs[0].path
        os.rename(src, dst)

def plan_rename(media, format):
    plan = RenamePlan()
    for m in media:
        filename = format
        if '@name' in format:
            name = detect_name(m.name)
            if name is None:
                logging.warning(f"Could not rename: {m.name} (name not detected)")
                continue
            filename = filename.replace('@name', str(name))
        if '@year' in format:
            year = detect_year(m.name)
            if year is None:
                logging.warning(f"Could not rename: {m.name} (year not detected)")
                continue
            filename = filename.replace('@year', str(year))
        if '@ext' in format:
            filename = filename.replace('@ext', m.ext.lower())
        if filename != m.name:
            plan.add_task((m, filename))
    return plan
