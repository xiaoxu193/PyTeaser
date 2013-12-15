# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages
from imp import load_source

with open('README.md') as file:
	long_description = file.read()

setup(name='pyteaser',
    version='1.0',
    description="PyTeaser is based on the original TextTeaser project written in Scala by Mojojolo. It's completely re-written in Python.",
    long_description=long_description,
    license='MIT',
    package_dir = {'': "python-goose"},
    packages=['goose', 'goose.utils', 'goose.images', 'goose.resources', 'goose.videos'],
    include_package_data=True,
    install_requires=['Pillow', 'lxml', 'cssselect', 'jieba', 'beautifulsoup'],
    test_suite="tests"
)
