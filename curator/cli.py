#!/usr/bin/env python3

import argparse
import logging
import os
import pathlib
import sys

import curator
from curator.databases import get_database
from curator.util import confirm

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
    logging.info(f'Analyzing {len(media)} input media files')
    return media

def curator_handle_plan(plan, args):
    plan.validate()
    if plan.is_empty():
        print('Current plan requires no tasks. There is nothing to be done.')
        return

    # Dry run
    if args.n:
        plan.show()
        return
    # Blind run
    if args.y:
        curator_apply_plan(plan)
        return
    # Interactive mode (default)
    plan.edit()
    tasks_enabled = len([t for t in plan if t.enabled])
    print(f"After changes, the current plan has {tasks_enabled} tasks enabled out of {len(plan)}.")
    if confirm("Apply plan?", default="no"):
        curator_apply_plan(plan)

def curator_apply_plan(plan):
    plan.optimize()
    plan.apply()
    tasks_failed = len([t for t in plan if t.failed])
    if not tasks_failed:
        print('All tasks completed successfully')
    else:
        print('Some tasks failed:')
        for task in plan:
            if not task.failed: continue
            print(f'- Task #{task.id} with input {task.inputs[0]} failed')

# Usage
CURATOR_USAGE = '''
Usage: curator <command> [<args>]

The following commands are supported:
  link    Create symbolic links to files in another directory.
  merge   Merge related files into a single container.
  rename  Rename files according to their metadata.
  tag     Update stream metadata/tags.
'''.strip()

def curator_convert(argv):
    parser = curator_argparser()
    parser.add_argument('-d', '--delete', action='store_true', help='delete inputs after converting')
    parser.add_argument('-f', '--format', choices=['mkv'], required=True)
    args = curator_args(parser, argv)

    from curator.plans import plan_convert
    media = curator_input(args)
    plan = plan_convert(media, args.format, args.delete)
    curator_handle_plan(plan, args)

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

    # Video stream selection
    parser.add_argument('--try-video-criteria', required=False, default='resolution,codec,fps',
        help='Comma-separated list of video criteria in decreasing order of importance')
    parser.add_argument('--try-video-codecs', required=False, default='hevc,h264,mpeg4',
        help='Comma-separated list of video codec in decreasing order of preference')
    parser.add_argument('--min-video-resolution', required=False, default=None,
        help='Try to discard video streams below this resolution')
    parser.add_argument('--max-video-resolution', required=False, default=None,
        help='Try to discard video streams above this resolution')
    parser.add_argument('--min-video-bitrate', required=False, default=None,
        help='Try to discard video streams below this bitrate')
    parser.add_argument('--max-video-bitrate', required=False, default=None,
        help='Try to discard video streams above this bitrate')

    args = curator_args(parser, argv)
    if args.min_video_resolution or args.min_video_bitrate or \
       args.max_video_resolution or args.max_video_bitrate:
        raise Exception("Unsupported argument")
    select = lambda *keys: { k: vars(args)[k] for k in keys }
    opts = select(
        'try_video_criteria',
        'try_video_codecs',
        'min_video_resolution',
        'max_video_resolution',
        'min_video_bitrate',
        'max_video_bitrate')
    for k in ('try_video_criteria', 'try_video_codecs'):
        opts[k] = opts[k].split(',')

    from curator.plans import plan_merge
    media = curator_input(args)
    plan = plan_merge(media, args.format, args.delete, opts)
    curator_handle_plan(plan, args)

def curator_rename(argv):
    parser = curator_argparser()
    parser.add_argument('-f', '--format', default="@name (@year).@ext")
    parser.add_argument('-d', '--db', required=False)
    parser.add_argument('--db-cache-days', required=False, type=int, default=30,
        help='Update database if older than N days. Set to 0 to force refresh (default: 30 days)')
    args = curator_args(parser, argv)

    from curator.plans import plan_rename
    db = get_database(args.db, args.db_cache_days) if args.db else None
    media = curator_input(args)
    plan = plan_rename(media, args.format, db)
    curator_handle_plan(plan, args)

def curator_tag(argv):
    parser = curator_argparser()
    parser.add_argument('-s', '--streams', default="all", choices=["all", "audio", "subtitle"])
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
        'convert': curator_convert,
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
