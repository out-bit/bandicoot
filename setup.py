#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from outbit import __version__, __author__

try:
    from setuptools import setup, find_packages
except ImportError:
    print("outbit needs setuptools in order to build. Install it using"
            " your package manager (usually python-setuptools) or via pip (pip"
            " install setuptools).")
    sys.exit(1)

setup(name='outbit',
      version=__version__,
      description='The command line and control center of a Data Center or Cloud.',
      author=__author__,
      author_email='david@davidwhiteside.com',
      url='https://github.com/starboarder2001/outbit',
      license='MIT',
      install_requires=["redis", "Flask", "PyYAML", 'setuptools'],
      package_dir={ '': 'lib' },
      packages=find_packages('lib'),
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Installation/Setup',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities',
      ],
      scripts=[
         'bin/outbit',
         'bin/outbit-api',
      ],
      data_files=[],
)
