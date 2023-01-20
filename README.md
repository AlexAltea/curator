Curator
=======

Automated normalization and curating of media collections. Written in Python 3.x.

Install the package via:

```sh
pip install https://github.com/AlexAltea/curator/archive/master.zip
```

## Features

### Merge

```
$ curator merge -f mkv ./movies/The*
┌───┬──────────────────────────────────┬───┬────────────────────────────────┐
│ # │ Inputs                           │ → │ Output                         │
├───┼──────────────────────────────────┼───┼────────────────────────────────┤
│ 1 │ The Social Network (2010).mkv    │ → │ The Social Network (2010).mkv  │
│   │ The Social Network (2010).es.ac3 │ ↑ │                                │
│   │ The Social Network (2010).en.srt │ ↑ │                                │
│   │ The Social Network (2010).es.srt │ ↑ │                                │
│   │ The Social Network (2010).de.srt │ ↑ │                                │
│ 2 │ There Will Be Blood (2007).mp4   │ → │ There Will Be Blood (2007).mkv │
│   │ There Will Be Blood (2007).srt   │ ↑ │                                │
└───┴──────────────────────────────────┴───┴────────────────────────────────┘
```

### Rename

```
$ curator rename -f "@name (@year).@ext" ./downloads/*
┌───┬──────────────────────────────────────────────────────────┬───┬─────────────────────────────────┐
│ # │ Old                                                      │ → │ New                             │
├───┼──────────────────────────────────────────────────────────┼───┼─────────────────────────────────┤
│ 1 │ 10000.BC.2008_HDRip_[scarabey.org].mp4                   │ → │ 10000 BC (2008).mp4             │
│ 2 │ 2001.A.Space.Odyssey.1968.1080p.BluRay.x264-[YTS.AM].mp4 │ → │ 2001 A Space Odyssey (1968).mp4 │
│ 3 │ Jacobs.Ladder.1990.720p.BluRay.x264.YIFY.mkv             │ → │ Jacobs Ladder (1990).mkv        │
│ 4 │ Venom.2018.HDTS.XViD.AC3-ETRG.mkv                        │ → │ Venom (2018).mkv                │
└───┴──────────────────────────────────────────────────────────┴───┴─────────────────────────────────┘
```
