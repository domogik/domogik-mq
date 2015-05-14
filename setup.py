#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

Help to manage Domogik installation

Implements
==========


@author: Domogik project
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

pyzmq_found = False

import pip
for mod in pip.get_installed_distributions():
    if ( mod.key == 'pyzmq' ):
        pyzmq_found = True

setup(
    name = 'Domogik MQ',
    version = '0.4.0',
    url = 'http://www.domogik.org/',
    description = 'MQ module for Domogik',
    author = 'Domogik team',
    author_email = 'domogik-general@lists.labs.libre-entreprise.org',
    install_requires=['setuptools', 'version',
          'pip >= 1.0',
          'simplejson >= 1.9.2',
          'python-daemon >= 1.5.5',
          'pyzmq >= 2.2.0'],
    zip_safe = False,
    license = 'GPL v3',
    packages = find_packages('src', exclude=["mpris"]),
    package_dir = { '': 'src' },
    package_data = {},
    scripts=[],
    entry_points = {
        'console_scripts': [
        """
            dmg_mq_dump = domogikmq.dump:main
            dmg_broker = domogikmq.reqrep.broker:main
            dmg_forwarder = domogikmq.pubsub.forwarder:main
        """
        ]
    },
    classifiers=[
        "Topic :: Home Automation",
        "Environment :: No Input/Output (Daemon)",
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English"
    ]
)

