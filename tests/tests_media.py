#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

from curator.media import *

def test_detect_subtitle_language():
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.da.srt")) == 'dan')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.en.srt")) == 'eng')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.es.srt")) == 'spa')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.fr.srt")) == 'fra')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.he.srt")) == 'heb')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.it.srt")) == 'ita')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.ko.srt")) == 'kor')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.pl.srt")) == 'pol')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.pt.srt")) == 'por')
    assert(detect_subtitle_language(Media("tests/samples/the_godfather_1972.zh.srt")) == 'zho')

def test_media():
    test_detect_subtitle_language()
