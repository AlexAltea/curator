#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

from curator.media import *
from curator.stream import *

def test_detect_subtitle_language():
    srt_lang = lambda path: Media(path).get_streams()[0].detect_subtitle_language()
    assert(srt_lang("tests/samples/the_godfather_1972.da.srt") == 'dan')
    assert(srt_lang("tests/samples/the_godfather_1972.en.srt") == 'eng')
    assert(srt_lang("tests/samples/the_godfather_1972.es.srt") == 'spa')
    assert(srt_lang("tests/samples/the_godfather_1972.fr.srt") == 'fra')
    assert(srt_lang("tests/samples/the_godfather_1972.he.srt") == 'heb')
    assert(srt_lang("tests/samples/the_godfather_1972.it.srt") == 'ita')
    assert(srt_lang("tests/samples/the_godfather_1972.ko.srt") == 'kor')
    assert(srt_lang("tests/samples/the_godfather_1972.pl.srt") == 'pol')
    assert(srt_lang("tests/samples/the_godfather_1972.pt.srt") == 'por')
    assert(srt_lang("tests/samples/the_godfather_1972.zh.srt") == 'zho')

def test_stream():
    test_detect_subtitle_language()
