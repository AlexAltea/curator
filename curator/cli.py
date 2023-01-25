#!/usr/bin/env python3

import argparse
import logging
import os
import pathlib
import sys

import curator

def confirm(question, default="yes"):
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError(f"Invalid default answer: '{default}'")

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond 'yes' or 'no' ('y' or 'n').\n")

# Helpers
def curator_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='+', type=str)
    parser.add_argument('--log', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='WARNING')
    parser.add_argument('-q', '--query', action='append', help="metadata filter(s), e.g. `tags.language=eng`", default=[])
    parser.add_argument('-y', action='store_true') # Auto-yes
    parser.add_argument('-n', action='store_true') # Auto-no
    parser.add_argument('-r', action='store_true') # Recursive
    return parser

def curator_args(parser, argv):
    args = parser.parse_args(argv)
    logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s',
        level=getattr(logging, args.log), stream=sys.stderr)
    return args

def curator_input(args):
    media = curator.media_input(args.input, recursive=args.r, queries=args.query)
    logging.info(f'Processing {len(media)} input media files')
    return media

def curator_handle_plan(plan, args):
    if plan.is_empty():
        print('Current plan requires no tasks. There is nothing to be done.')
        return

    # Dry run
    if args.n:
        plan.show()
        return
    # Blind run
    if args.y:
        plan.apply()
        return
    # Interactive mode (default)
    #plan.edit() # TODO
    plan.show()
    if confirm("Continue?", default="no"):
        plan.apply()

# Usage
CURATOR_USAGE = '''
Usage: curator <command> [<args>]

The following commands are supported:
  link    Create symbolic links to files in another directory.
  merge   Merge related files into a single container.
  rename  Rename files according to their metadata.
  tag     Update stream metadata/tags.
'''.strip()

def curator_link(argv):
    parser = curator_argparser()
    parser.add_argument('-o', '--output', required=True)
    args = curator_args(parser, argv)

    from curator.plans import plan_link
    media = curator_input(args)
    plan = plan_link(media, args.output)
    curator_handle_plan(plan, args)

def curator_merge(argv):
    parser = curator_argparser()
    parser.add_argument('-d', '--delete', action='store_true', help='delete inputs after merging')
    parser.add_argument('-f', '--format', choices=['mkv'], default='mkv')
    args = curator_args(parser, argv)

    from curator.plans import plan_merge
    media = curator_input(args)
    plan = plan_merge(media, args.format, args.delete)
    curator_handle_plan(plan, args)

def curator_rename(argv):
    parser = curator_argparser()
    parser.add_argument('-f', '--format', default="@name (@year).@ext")
    args = curator_args(parser, argv)

    from curator.plans import plan_rename
    media = curator_input(args)
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
    parser.add_argument('--max-audio-samples', type=int, default=10,
        help='when detecting languages in audio, max number of samples to extract.')
    parser.add_argument('--min-score', type=float, default=0.8,
        help='when detecting languages in audio, max number of samples to extract.')
    args = curator_args(parser, argv)

    # Select relevant options
    select = lambda *keys: { k: vars(args)[k] for k in keys }
    if args.tag == 'language':
        opts = select('only_macrolanguages', 'max_audio_samples', 'min_score')

    from curator.plans import plan_tag
    media = curator_input(args)
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
        print('Curator: Automated normalization and curating of media collections.\n')
        print(CURATOR_USAGE)
        return

    # Configure logging
    blacklist = ['langid']
    for name in blacklist:
        logging.getLogger(name).setLevel(logging.ERROR)

    # Dispatch command otherwise
    command = sys.argv[1]
    handler = commands.get(command)
    if not handler:
        print('Unsupported command "{}"\n'.format(command))
        print(CURATOR_USAGE)
        exit(1)
    handler(sys.argv[2:])

if __name__ == '__main__':
    main()
