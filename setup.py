#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='dlgo',
    version='0.1.0',
    description='',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='David Bradford',
    author_email='dbradf@gmail.com',
    url='https://github.com/dbradf/dlgo',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=[
        'Click==7.0',
        'Keras',
        'numpy',
        'PyYAML==5.4',
        'requests==2.22.0',
        'structlog',
        'tensorflow',
    ],
    entry_points={
        'console_scripts': [
            'bot_v_bot=dlgo.bot_v_bot:main',
            'dl_train=dlgo.agent.dl.train:main',
            'download_games=dlgo.data.index_processor:main',
            'gen_hashes=dlgo.util.gen_hashes:main',
            'gen_mcts_games=dlgo.util.gen_mcts_games:main',
        ]
    },
)
