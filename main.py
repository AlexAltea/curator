#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import argparse
import logging
import os
import pathlib
import sys

import curator

# Configuration
DEFAULT_CONFIG = 'curator.json'
DEFAULT_DATABASE = 'curator.db'

# Helpers
def curator_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='+', type=str)
    parser.add_argument('-y', action='store_true') # Auto-yes
    parser.add_argument('-n', action='store_true') # Auto-no
    parser.add_argument('-r', action='store_true') # Recursive
    return parser

def curator_handle_plan(plan, args):
    # Dry run
    if args.n:
        plan.show()
        return
    # Blind run
    if args.y:
        plan.apply()
        return

    # Interactive mode (default)
    plan.edit()
    #plan.apply()

# Usage
CURATOR_USAGE = '''
Usage: curator <command> [<args>]

The following commands are supported:
   merge   Merge related files into a single container.
   link    Create symbolic links to files in another directory.
   rename  Rename files according to their metadata.
'''

def curator_merge(argv):
    parser = curator_argparser()
    parser.add_argument('-o', '--output', choices=['mkv'], default='mkv')
    args = parser.parse_args(argv)

    print(curator.media_input(args.input))

def curator_rename(argv):
    parser = curator_argparser()
    parser.add_argument('-f', '--format', default="@name (@year).@ext")
    args = parser.parse_args(argv)

    media = curator.media_input(args.input, recursive=args.r)
    plan = curator.plan_rename(media, args.format)
    curator_handle_plan(plan, args)

def curator_link(argv):
    parser = curator_argparser()
    parser.add_argument('-f', '--filter')
    parser.add_argument('-o', '--output')
    args = parser.parse_args(argv)

    media = curator.media_input(args.input, recursive=args.r)
    plan = curator.plan_link(media, args.filter, args.output)
    curator_handle_plan(plan, args)

def main():
    commands = {
        'merge': curator_merge,
        'link': curator_link,
        'rename': curator_rename,
    }

    # If no arguments are provided
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print('Curator: Automated normalization and curating of media collections.')
        print(CURATOR_USAGE)
        return

    # Dispatch command otherwise
    command = sys.argv[1]
    handler = commands.get(command)
    if not handler:
        print('Unsupported command "{}"'.format(command))
        print(CURATOR_USAGE)
        exit(1)
    handler(sys.argv[2:])

if __name__ == '__main__':
    main()
