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

Test domogik configuration

Implements
==========


@author: Fritz SMH <fritz.smh@gmail.com>, Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import pwd
import sys
from multiprocessing import Process, Pipe
from socket import gethostbyname, gethostname
from domogikmq.common.utils import get_ip

BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

user = ''

def info(msg):
    print("{0} [ {1} ] {2}".format(BLUE,msg,ENDC))
def ok(msg):
    print("{0} ==> {1}  {2}".format(OK,msg,ENDC))
def warning(msg):
    print("{0} ==> {1}  {2}".format(WARNING,msg,ENDC))
def fail(msg):
    print("{0} ==> {1}  {2}".format(FAIL,msg,ENDC))

def am_i_root():
    info("Check this script is started as root")
    assert os.getuid() == 0, "This script must be started as root"
    ok("Correctly started with root privileges.")

def test_imports():
    good = True
    info("Test imports")
    try:
        import domogikmq
    except ImportError:
        warning("domogikmq package can not be imported, check installation logs!")
        good = False
    try:
        import netifaces
    except ImportError:
        warning("netifaces package can not be imported, check installation logs!")
        good = False
    try:
        import zmq
    except ImportError:
        warning("zmq package can not be imported, check installation logs!")
        good = False
    assert good, "One or more import have failed, please install required packages and restart this script."
    ok("Imports are good")

def test_config_files():
    global user
    info("Test global config file to get the user")
    assert os.path.isfile("/etc/conf.d/domogik-mq") or os.path.isfile("/etc/default/domogik-mq"), \
            "No global config file found, please exec install.sh if you did not exec it before."
    assert not (os.path.isfile("/etc/conf.d/domogik-mq") and os.path.isfile("/etc/default/domogik-mq")), \
            "Global config file found at 2 locations. Please put it only at /etc/default/domogik-mq or \
            /etc/conf.d/domogik-mq then restart test_config.py as root"
    if os.path.isfile("/etc/default/domogik-mq"):
        file = "/etc/default/domogik-mq"
    else:
        file = "/etc/conf.d/domogik-mq"
    f = open(file,"r")
    r = f.readlines()
    lines = filter(lambda x: not x.startswith('#') and x != '\n',r)
    f.close()
    #user = ''
    manager_params = ''
    custom_path = ''
    hub_iface = ''
    launch_domogik_xpl_hub = ''
    for line in lines:
        item,value = line.strip().split("=")
        if item.strip() == "DOMOGIK_USER":
            user = value

    info("Test user / config file")

    #Check user config file
    try:
        user_entry = pwd.getpwnam(user)
    except KeyError:
        raise KeyError("The user %s does not exists, you MUST create it or change the DOMOGIK_USER parameter in %s. Please report this as a bug if you used install.sh." % (user, file))
    user_home = user_entry.pw_dir
    assert os.path.isfile("/etc/domogik/domogik-mq.cfg"), "The domogik config file /etc/domogik/domogik-mq.cfg does not exist. Please report this as a bug if you used install.sh." % user_home
    ok("Domogik MQ's user exists and has a config file")

    test_user_config_file(user_home, user_entry)

def _test_user_can_write(conn, path, user_entry):
    os.setgid(user_entry.pw_gid)
    os.setuid(user_entry.pw_uid)
    conn.send(os.access(path, os.W_OK))
    conn.close()

def _check_port_availability(s_ip, s_port, udp = False):
    """ Parse /proc/net/tcp to check if something listen on the port"""
    ip = gethostbyname(s_ip).split('.')
    port = "%04X" % int(s_port)
    ip = "%02X%02X%02X%02X" % (int(ip[3]),int(ip[2]),int(ip[1]),int(ip[0]))
    if udp == False:
        f = open("/proc/net/tcp")
    else:
        f = open("/proc/net/udp")
    lines = f.readlines()
    f.close()
    lines.pop(0)
    for line in lines:
        data = line.split()
        d_ip = data[1].split(':')[0]
        d_port = data[1].split(':')[1]
        if d_port == port:
            assert d_ip != ip and ip != "00000000", "A service already listen on ip %s and port %s. Stop it and restart test_config.py" % (s_ip, s_port)

def test_user_config_file(user_home, user_entry):
    info("Check user config file contents")
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.read("/etc/domogik/domogik-mq.cfg")

    #check [mq] section
    mq = dict(config.items('mq'))
    ok("Config file correctly loaded")

    info("Parse [mq] section")
    import domogikmq

    parent_conn, child_conn = Pipe()
    p = Process(target=_test_user_can_write, args=(child_conn, mq['log_dir_path'],user_entry,))
    p.start()
    p.join()
    assert parent_conn.recv(), "The directory %s for log does not exist or does not have right permissions" % mq['log_dir_path']

    assert mq['log_level'] in ['debug','info','warning','error','critical'], "The log_level parameter does not have a good value. Must \
            be one of debug,info,warning,error,critical"

    # Check ports
    info("Check ports availibility")
    mq_ip = mq['ip']
    if mq_ip == '*':
        mq_ip = get_ip()
    _check_port_availability(mq_ip, mq['req_rep_port'])
    _check_port_availability(mq_ip, mq['pub_port'])
    _check_port_availability(mq_ip, mq['sub_port'])
    ok("IPs/ports needed by Domogik MQ are not bound by anything else")

    ok("[mq] section seems good")


def test_version():
    info("Check python version")
    v = sys.version_info
    assert not (v[0] == 2 and v[1] < 7), "Python version is %s.%s, it must be >= 2.7, please upgrade" % (v[0], v[1])
    ok("Python version is >= 2.7")

def test_config():
    try:
        print("\n\n")
        info("Start to test configuration")
        am_i_root()
        test_imports()
        test_config_files()
        test_version()
        print("\n\n")
        ok("================================================== <==")
        ok(" Everything seems ok                               <==")
        ok(" You can now install Domogik                       <==")
        ok("================================================== <==")
    except:
        fail(sys.exc_info()[1])

if __name__ == "__main__":
    test_config()
