#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

import argparse
import os
import sys

# import curator

# Configuration
DEFAULT_CONFIG = 'curator.json'
DEFAULT_DATABASE = 'curator.db'

# Helpers
def curator_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=str, default=DEFAULT_CONFIG, nargs='?',
        help='Destination configuration file')
    return parser

def curator_argdict(args):
    args = vars(args).copy()
    args.pop('config')
    return args

# Usage
CURATOR_USAGE = '''
Usage: curator <command> [<args>]

The following commands are supported:
   merge   Merge multiple files.
'''

def curator_merge(argv):
    parser = curator_argparser()
    parser.add_argument('input', nargs='+', type=pathlib.Path)
    parser.add_argument('-o', '--output')
    parser.add_argument('-y') # Auto-yes 
    parser.add_argument('-n') # Auto-no
    args = parser.parse_args(argv)

def main():
    commands = {
        'merge': curator_merge,
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
