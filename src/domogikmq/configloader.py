#!/usr/bin/python
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

Plugin purpose
==============

Load config from file

Implements
==========

- Loader

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

####################################################
#       DON'T CHANGE ANYTHING AFTER THIS LINE      #
####################################################
import os
import pwd 
try:
    # from python3 onwards
    import configparser
except ImportError:
    # python 2
    import ConfigParser as configparser
import threading
import time
import fcntl


CONFIG_FILE = "/etc/domogik/domogik-mq.cfg"

class Loader():
    '''
    Parse Domogik MQ config files
    '''

    config = None 

    def __init__(self, part_name=None):
        '''
        Load the configuration for a part of the Domogik system
        @param part_name name of the part to load config from
        '''
        #if hasattr(self.__class__, "config") == False:
        #    self.__class__.config = None
        self.config = None
        self.part_name = part_name

    def load(self):
        '''
        Parse the config
        @return pair (main_config, plugin_config)
        '''
        # read config file
        self.config = configparser.ConfigParser()
        cfg_file = open(CONFIG_FILE)
        self.config.readfp(cfg_file)
        cfg_file.close()

        # get 'mq' config part
        result = self.config.items('mq')
        domogik_part = {}
        for k, v in result:
            domogik_part[k] = v

        # no other config part requested
        if self.part_name == None:
            result = (domogik_part, None)

        # Get requested (if so) config part
        if self.part_name:
            result =  (domogik_part, self.config.items(self.part_name))

        return result
