#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

CURATOR_VERSION = '0.1.0'
CURATOR_REPOSITORY_URL = 'https://github.com/AlexAltea/curator'
CURATOR_DOWNLOAD_URL = 'https://github.com/AlexAltea/curator/tarball/' + CURATOR_VERSION

# Description
CURATOR_DESCRIPTION = """Curator
=========

.. image:: https://coveralls.io/repos/github/AlexAltea/curator/badge.svg?branch=master
    :target: https://coveralls.io/github/AlexAltea/curator?branch=master
    
.. image:: https://img.shields.io/pypi/v/curator.svg
    :target: https://pypi.python.org/pypi/curator

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
    packages=['curator', 'curator.plans'],
    entry_points = {
        'console_scripts': ['curator=curator.cli:main'],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License v2.0',
        'Programming Language :: Python :: 3.7',
        'Natural Language :: English',
    ],
)
