Curator
=======

Automated normalization and curating of media collections. Written in Python 3.x.

Curator is a collection of stateless CLI tools, following the [Unix philosophy](https://en.wikipedia.org/wiki/Unix_philosophy), to organize large collections of heterogeneous media. Each tool creates a *plan* made of *tasks* with clearly defined input and output files, which the user can optionally review before applying.

Install the package via:

```sh
pip install git+https://github.com/AlexAltea/curator.git
```

## Features

Curator can automatically rename and link media files, edit container metadata, remux and merge streams. Reducing manual labor and achieve reliable results across different media from potentially different sources, some tools rely on signal processing and machine learning (e.g. [Whisper](https://openai.com/blog/whisper/), [LangID](https://github.com/saffsd/langid.py)).

Highlighted use cases (current and planned):

- [x] Filter media by container and stream metadata (all).
- [x] Rename files based on existing filenames ([`curator-rename`](#rename)).
- [x] Merge streams from multiple related containers ([`curator-merge`](#merge)).
- [x] Detect audio/subtitle language from sound and text data ([`curator-tag`](#tag)).
- [ ] Rename files based on existing metadata and databases ([`curator-rename`](#rename)).
- [ ] Synchronize audio/subtitle streams ([`curator-merge`](#merge) and [`curator-sync`](#sync)).
- [ ] Remove scene banners from subtitles ([`curator-clean`](#clean)).
- [ ] Detect watermarks in video streams ([`curator-clean`](#clean) and [`curator-merge`](#merge)).
- [ ] Select highest quality audio/video streams ([`curator-merge`](#merge)).

Below you can find a description and examples of all tools provided by Curator:

### Link

TODO.

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

### Tag

TODO.
