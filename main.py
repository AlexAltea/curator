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
  link    Create symbolic links to files in another directory.
  merge   Merge related files into a single container.
  rename  Rename files according to their metadata.
  tag     Update stream metadata/tags.
'''

def curator_link(argv):
    parser = curator_argparser()
    parser.add_argument('-f', '--filter', action='append', help="metadata filter(s), e.g. `tags.language=eng`", default=[])
    parser.add_argument('-o', '--output', required=True)
    args = parser.parse_args(argv)

    from curator.plans import plan_link
    media = curator.media_input(args.input, recursive=args.r)
    plan = plan_link(media, args.filter, args.output)
    curator_handle_plan(plan, args)

def curator_merge(argv):
    parser = curator_argparser()
    parser.add_argument('-d', '--delete', action='store_true', help='delete inputs after merging')
    parser.add_argument('-f', '--format', choices=['mkv'], default='mkv')
    args = parser.parse_args(argv)

    from curator.plans import plan_merge
    media = curator.media_input(args.input, recursive=args.r)
    plan = plan_merge(media, args.format, args.delete)
    curator_handle_plan(plan, args)

def curator_rename(argv):
    parser = curator_argparser()
    parser.add_argument('-f', '--format', default="@name (@year).@ext")
    args = parser.parse_args(argv)

    from curator.plans import plan_rename
    media = curator.media_input(args.input, recursive=args.r)
    plan = plan_rename(media, args.format)
    curator_handle_plan(plan, args)

def curator_tag(argv):
    parser = curator_argparser()
    parser.add_argument('-s', '--streams', required=True, choices=["audio", "subtitle"])
    parser.add_argument('-t', '--tag', required=True, choices=["language"])
    parser.add_argument('-v', '--value', required=False)
    parser.add_argument('--skip-tagged', action='store_true',
        help='skip streams if a valid tag already exists')
    # Tag-specific options
    parser.add_argument('--only-macrolanguages', action='store_true',
        help='when detecting languages, consider only macrolanguages. ' +
             'e.g. this will map `nno`/`nnb` detections into `nor`.')
    args = parser.parse_args(argv)

    # Select relevant options
    select = lambda *keys: { k: vars(args)[k] for k in keys }
    if args.tag == 'language':
        opts = select('only_macrolanguages')

    from curator.plans import plan_tag
    media = curator.media_input(args.input, recursive=args.r)
    plan = plan_tag(media, args.streams, args.tag, args.value, args.skip_tagged, opts)
    curator_handle_plan(plan, args)

def main():
    commands = {
        'link': curator_link,
        'merge': curator_merge,
        'rename': curator_rename,
        'tag': curator_tag,
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
