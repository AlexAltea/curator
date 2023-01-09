#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import logging
import os

import ffmpeg

from .analysis import *
from .media import *
from .tui import *

class Plan:
    def __init__(self):
        self.tasks = []
        self.last_id = 0

    def add_task(self, task):
        self.last_id += 1
        self.tasks.append(task)
        task.id = self.last_id

    def apply(self):
        for task in self.tasks:
            if task.enabled:
                task.apply()

    def show(self):
        thead, tbody = self.show_tasks()
        print_plan(thead, tbody)

    def edit(self):
        return
