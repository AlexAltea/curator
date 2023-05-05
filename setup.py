#!/usr/bin/env python
# -*- coding: utf-8 -*-

import setuptools

from pkg_resources import parse_requirements

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

with open('requirements.txt', 'r') as f:
    requirements = [str(req) for req in parse_requirements(f)]

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
    install_requires=requirements,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License v2.0',
        'Programming Language :: Python :: 3.8',
        'Natural Language :: English',
    ],
)
