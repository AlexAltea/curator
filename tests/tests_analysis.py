#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Curator.
"""

from curator.analysis import *
from curator.media import *

def test_analysis_years():
    # Scene-syntax testing
    assert(1990 == detect_year('Jacobs.Ladder.1990.720p.BluRay.x264.YIFY'))
    assert(1968 == detect_year('2001.A.Space.Odyssey.1968.1080p.BluRay.x264-[YTS.AM]'))
    assert(2008 == detect_year('10000.BC.2008_HDRip_[scarabey.org]'))
    assert(2014 == detect_year('Interstellar.2014.4K.UltraHD.BluRay.2160p.x264.DTS-HD.MA.5.1.AAC.5.1-POOP'))
    
    # Custom-syntax testing
    assert(2013 == detect_year('Coherence (2013) [English]'))
    assert(2003 == detect_year('Bad Santa (Extended Cut) (2003) [English]'))
    assert(1984 == detect_year('1984 (1984) [English]'))
    assert(None == detect_year('Ani-Kuri 15 [Japanese]'))

    # Stress testing
    assert(2000 == detect_year('2000'))
    assert(2000 == detect_year('1234 2000'))
    assert(2000 == detect_year('1234 2000 1080'))
    assert(2000 == detect_year('1234 2000 1080 x1999'))
    assert(2000 == detect_year('1234 2000 1080 1999x'))
    assert(None == detect_year('1234'))
    assert(None == detect_year(''))

def test_analysis_names():
    # Scene-syntax testing
    assert(detect_name('Jacobs.Ladder.1990.720p.BluRay.x264.YIFY')
        == 'Jacobs Ladder')
    assert(detect_name('2001.A.Space.Odyssey.1968.1080p.BluRay.x264-[YTS.AM]')
        == '2001 A Space Odyssey')
    assert(detect_name('10000.BC.2008_HDRip_[scarabey.org]')
        == '10000 BC')
    assert(detect_name('Interstellar.2014.4K.UltraHD.BluRay.2160p.x264.DTS-HD.MA.5.1.AAC.5.1-POOP')
        == 'Interstellar')

    # Custom-syntax testing
    assert(detect_name('Coherence (2013) [English]')
        == 'Coherence')
    assert(detect_name('Bad Santa (Extended Cut) (2003) [English]')
        == 'Bad Santa')
    assert(detect_name('1984 (1984) [English]')
        == '1984')
    assert(detect_name('Ani-Kuri 15 [Japanese]')
        == 'Ani-Kuri 15')

def test_analysis_subtitle_language():
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

def test_analysis():
    test_analysis_years()
    test_analysis_names()
    test_analysis_subtitle_language()
