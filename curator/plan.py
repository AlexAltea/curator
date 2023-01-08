#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import logging

from .analysis import *
from .tui import *

class Plan:
    def __init__(self, tasks=[]):
        self.tasks = tasks

    def apply(self):
        for task in self.tasks:
            self.handle_task(*task)

    def add_task(self, task):
        self.tasks.append(task)

    def get_cols(self):
        return self.cols

    def get_rows(self):
        return

    def show(self):
        thead, tbody = self.show_tasks()
        print_plan(thead, tbody)

    def edit(self):
        return

# Plans
class RenamePlan(Plan):
    def handle_task(self, media, name):
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
