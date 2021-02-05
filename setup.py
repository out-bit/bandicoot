#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from bandicoot import __version__, __author__

try:
    from setuptools import setup, find_packages
except ImportError:
    print("bandicoot needs setuptools in order to build. Install it using"
            " your package manager (usually python-setuptools) or via pip (pip"
            " install setuptools).")
    sys.exit(1)

if len(sys.argv) > 1 and sys.argv[1] == 'bandicoot-cli':
    # python setup.py "bandicoot-cli" install
    del sys.argv[1]
    # bandicoot-cli only
    setup(name='bandicoot-cli',
          version=__version__,
          description='The command line and control center of a Data Center or Cloud.',
          author=__author__,
          author_email='david@davidwhiteside.com',
          url='https://github.com/starboarder2001/bandicoot',
          license='MIT',
          install_requires=["PyYAML", 'setuptools', 'ply', 'ascii_graph'],
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
             'bin/bandicoot',
             'bin/bandicoot-cli',
          ],
    )
else:
    # Full bandicoot Package
    # python setup.py install
    setup(name='bandicoots',
          version=__version__,
          description='The command line and control center of a Data Center or Cloud.',
          author=__author__,
          author_email='david@davidwhiteside.com',
          url='https://github.com/starboarder2001/bandicoot',
          license='MIT',
          install_requires=["requests", "Flask", "flask-cors", "PyJWT", "PyYAML", 'setuptools', 'ansible',
              'pymongo', 'ply', 'pycrypto', 'ldap3'],
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
             'bin/bandicoot',
             'bin/bandicoot-api',
             'bin/bandicoot-cli',
             'bin/bandicoot-api-install',
             'bin/bandicoot-api-install.yml',
          ],
          package_data={"": ["data_files/bandicoot-gui/*", "data_files/bandicoot-gui/css/*", "data_files/bandicoot-gui/imgs/*", "data_files/bandicoot-gui/js/*", "data_files/bandicoot-gui/templates/*"]},
    )
