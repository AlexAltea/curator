#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import functools
import operator
import os

from curator.analysis import *
from curator import Plan, Task, Media

class LinkPlan(Plan):
    def show_tasks(self):
        thead = ("Name",)
        tbody = []
        for task in self.tasks:
            name = task.inputs[0].name
            tbody.append((name,))
        return thead, tbody

class LinkTask(Task):
    def __init__(self, input, output):
        super().__init__([input], [output])
        assert(output.type == Media.TYPE_LINK)

    def apply(self):
        src = self.inputs[0].path
        lnk = self.outputs[0].path
        os.symlink(src, lnk)

def parse_query(query):
    lhs, rhs = query.split('=')
    path = lhs.split('.')
    return { 'lhs_path': path, 'op': operator.eq, 'rhs_value': rhs }

def filter_streams(streams, query):
    results = []
    query = parse_query(query)
    for stream in streams:
        try:
            lhs = functools.reduce(dict.get, query['lhs_path'], stream.get_info())
        except TypeError:
            continue
        rhs = query['rhs_value']
        if query['op'](lhs, rhs):
            results.append(stream)
    return results

def plan_link(media, filters, output):
    plan = LinkPlan()
    for m in media:
        if m.has_video_ext():
            streams = m.get_streams()
            for query in filters:
                streams = filter_streams(streams, query)
            if not streams:
                continue
            path = os.path.join(output, m.name)
            link = Media(path, Media.TYPE_LINK)
            task = LinkTask(m, link)
            plan.add_task(task)
    return plan
