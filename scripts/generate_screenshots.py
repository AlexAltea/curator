#!/usr/bin/env python3

import glob
import os
import subprocess
import tempfile

# Configuration
PROJECT_ROOT = os.path.abspath("..")
PROJECT_DOCS = os.path.join(PROJECT_ROOT, "docs")

# Data
TERM_CURATOR_MERGE = '''$ curator merge -f mkv ./movies/The*
┌───┬──────────────────────────────────┬───┬────────────────────────────────┐
│ # │ Inputs                           │ → │ Output                         │
├───┼──────────────────────────────────┼───┼────────────────────────────────┤
│ 1 │ The Social Network (2010).mkv    │ → │ The Social Network (2010).mkv  │
│   │ The Social Network (2010).es.ac3 │ ↗ │                                │
│   │ The Social Network (2010).en.srt │ ↗ │                                │
│   │ The Social Network (2010).es.srt │ ↗ │                                │
│   │ The Social Network (2010).de.srt │ ↗ │                                │
│ 2 │ There Will Be Blood (2007).mp4   │ → │ There Will Be Blood (2007).mkv │
│   │ There Will Be Blood (2007).srt   │ ↗ │                                │
└───┴──────────────────────────────────┴───┴────────────────────────────────┘
Continue? (y/N) '''

TERM_CURATOR_RENAME = '''$ curator rename -f "@name (@year).@ext" ./downloads/*
┌───┬────────────────────────────────────────────────────┬───┬─────────────────────────────────┐
│ # │ Old                                                │ → │ New                             │
├───┼────────────────────────────────────────────────────┼───┼─────────────────────────────────┤
│ 1 │ 10000.BC.2008_HDRip_[scarabey.org].mp4             │ → │ 10000 BC (2008).mp4             │
│ 2 │ 2001.A.Space.Odyssey.1968.BluRay.x264-[YTS.AM].mp4 │ → │ 2001 A Space Odyssey (1968).mp4 │
│ 3 │ Jacobs.Ladder.1990.720p.BluRay.x264.YIFY.mkv       │ → │ Jacobs Ladder (1990).mkv        │
│ 4 │ Venom.2018.HDTS.XViD.AC3-ETRG.mkv                  │ → │ Venom (2018).mkv                │
└───┴────────────────────────────────────────────────────┴───┴─────────────────────────────────┘
Continue? (y/N) '''

def termtosvg(text, output):
    term_w = 100
    term_h = text.count('\n') + 1
    cmd = ['termtosvg']
    cmd += ['-t', 'window_frame']
    cmd += ['--screen-geometry', f'{term_w}x{term_h}']
    cmd += ['--still-frames']
    cmd += ['--command', f'echo -n -e {repr(text)}']
    with tempfile.TemporaryDirectory() as tmp:
        cmd += [tmp]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert(result.returncode == 0)
        files = glob.glob(os.path.join(tmp, '*'))
        last = sorted(files)[-1]
        os.replace(last, output)

def main():
    termtosvg(TERM_CURATOR_MERGE,
        os.path.join(PROJECT_DOCS, 'images/curator-merge.svg'))
    termtosvg(TERM_CURATOR_RENAME,
        os.path.join(PROJECT_DOCS, 'images/curator-rename.svg'))

if __name__ == "__main__":
    main()
