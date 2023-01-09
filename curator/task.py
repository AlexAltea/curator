#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

class Task:
    def __init__(self, inputs=[], outputs=[]):
        self.inputs = inputs
        self.outputs = outputs
        self.enabled = True
        self.warning = None
        self.id = None
