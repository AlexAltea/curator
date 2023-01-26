#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

CURATOR_VERSION = '0.1.1'
CURATOR_REPOSITORY_URL = 'https://github.com/AlexAltea/curator'
CURATOR_DOWNLOAD_URL = 'https://github.com/AlexAltea/curator/tarball/' + CURATOR_VERSION

# Description
CURATOR_DESCRIPTION = """Curator
=========

.. image:: https://github.com/AlexAltea/curator/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/AlexAltea/curator/actions/workflows/ci.yml

Automated normalization and curating of media collections. Written in Python 3.x.

More information at: https://github.com/AlexAltea/curator
"""

setuptools.setup(
    name='curator',
    version=CURATOR_VERSION,
    description='Automated normalization and curating of media collections',
    long_description=CURATOR_DESCRIPTION,
    license='Apache-2.0',
    author='Alexandro Sanchez Bach',
    author_email='alexandro@phi.nz',
    url=CURATOR_REPOSITORY_URL,
    download_url=CURATOR_DOWNLOAD_URL,
    packages=['curator', 'curator.databases', 'curator.plans'],
    entry_points={
        'console_scripts': ['curator=curator.cli:main'],
    },
    install_requires=[
        'chardet==3.0.4',
        'iso639-lang==2.1.0',
        'langid==1.1.6',
        'numpy>=1.21.6',
        'openai-whisper==20230117',
        'pysrt==1.1.2',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License v2.0',
        'Programming Language :: Python :: 3.8',
        'Natural Language :: English',
    ],
)
