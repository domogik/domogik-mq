#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pwd
import sys
import platform
import ConfigParser
import argparse
import shutil
import logging
import pkg_resources


BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

logging.basicConfig(filename='install.log', level=logging.DEBUG)

def info(msg):
    logging.info(msg)
    print("{0} [ {1} ] {2}".format(BLUE, msg, ENDC))

def ok(msg):
    logging.info(msg)
    print("{0} ==> {1}  {2}".format(OK, msg, ENDC))

def warning(msg):
    logging.warning(msg)
    print("{0} ==> {1}  {2}".format(WARNING, msg, ENDC))

def fail(msg):
    logging.error(msg)
    print("{0} ==> {1}  {2}".format(FAIL, msg, ENDC))

def debug(msg):
    logging.debug(msg)

def build_file_list(user, master):
    d_files = [
        ('/etc/domogik', [user, 0755], \
                ['examples/config/domogik-mq.cfg.sample']),
        ('/var/log/domogik', [user, 0755], []),
    ]

    if os.path.exists('/etc/default'):
        debug("Found directory to store the system wide config: /etc/default")
        d_files.append(('/etc/default/', [user, None], \
                ['examples/default/domogik-mq']))
    else:
        fail("Can't find directory where i can copy system wide config")
        exit(0)

    if master:
        if os.path.exists('/etc/init.d'):
            debug("Init script path is /etc/init.d")
            d_files.append(('/etc/init.d/', [user, 0755], \
                    ['examples/init/domogik-mq']))
        elif os.path.exists('/etc/rc.d'):
            debug("Init script path is /etc/rc.d")
            d_files.append(('/etc/rc.d/', [user, 0755], \
                    ['examples/init/domogik-mq']))
        else:
            warning("Can't find firectory for init script: Require manual install")

    return d_files


def copy_files(user, master):
    info("Copy files")
    try:
        for directory, perm, files in build_file_list(user, master):
            if not os.path.exists(directory):
                if perm[1] != None:
                    res = os.makedirs(directory, int(perm[1]))
                else:
                    res = os.makedirs(directory)
                if not res:
                    ok("Creating dir {0}".format(directory))
                else:
                    fail("Failed creating dir {0}".format(directory))
            else:
                ok("Directory {0} already exists".format(directory))
            if perm[0] != '':
                debug("chown directory {0} with {1}".format(directory, perm[0]))
                os.system('chown {0} {1}'.format(perm[0], directory))
            for fname in files:
                # copy the file
                shutil.copy(os.path.join(\
                        os.path.dirname(os.path.realpath(__file__)), \
                            fname), \
                        directory)
                ok("Copyed file {0}".format(fname))
                dfname = os.path.join(directory, os.path.basename(fname))
                if perm[0] != '':
                    debug("chown dile {0} with {1}".format(dfname, perm[0]))
                    os.system('chown {0} {1}'.format(perm[0], dfname))
                #if perm[1] != None:
                #    os.system('chmod {0} {1}'.format(perm[1], dfname))
    except:
        raise

def ask_user_name():
    info("Create domogik-mq user")
    print("As what user should domogik-mq run? [domogik]: "),
    new_value = sys.stdin.readline().rstrip('\n')
    if new_value == "":
        d_user = 'domogik'
    else:
        d_user = new_value
    debug("Username will be {0}".format(d_user))
    return d_user

def ask_master_install():
    print("Install MQ as master (lib+daemon) or client (lib only) ? [M/s]: "),
    new_value = sys.stdin.readline().rstrip('\n')
    if new_value == "m" or new_value == "M" or new_value == '':
        debug("Installing MQ Master")
        return True
    else:
        debug("Installing MQ Client")
        return False

def create_user(d_user, d_shell = "/bin/sh"):
    if d_user not in [x[0] for x in pwd.getpwall()]:
        print("Creating the {0} user and add it to dialout".format(d_user))
        cmd_line = 'adduser --system {0} --shell {1} '.format(d_user, d_shell)
        debug(cmd_line)
        os.system(cmd_line)
        cmd_line = 'adduser {0} dialout'.format(d_user)
        debug(cmd_line)
        os.system(cmd_line)
    if d_user not in [x[0] for x in pwd.getpwall()]:
        fail("Failed to create domogik-mq user")
    else:
        ok("Correctly created domogik-mq user")
    # return the user to use

def is_domogik_advanced(advanced_mode, sect, key):
    advanced_keys = {
        'mq': ['req_rep_port', 'pub_port', 'sub_port'],
    }
    if advanced_mode:
        return True
    else:
        if sect not in advanced_keys:
            return True
        else:
            if key not in advanced_keys[sect]:
                return True
            else:
                return False

def write_domogik_configfile(advanced_mode):
    # read the sample config file
    newvalues = False
    config = ConfigParser.RawConfigParser()
    config.read( ['/etc/domogik/domogik-mq.cfg.sample'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            if is_domogik_advanced(advanced_mode, sect, item[0]):
                print("Key {0} [{1}]: ".format(item[0], item[1])),
                new_value = sys.stdin.readline().rstrip('\n')
                if new_value != item[1] and new_value != '':
                    # need to write it to config file
                    config.set(sect, item[0], new_value)
                    newvalues = True
    # write the config file
    with open('/etc/domogik/domogik-mq.cfg', 'wb') as configfile:
        ok("Writing the config file")
        config.write(configfile)

def write_domogik_configfile_from_command_line(args):
    # read the sample config file
    newvalues = False
    config = ConfigParser.RawConfigParser()
    config.read( ['/etc/domogik/domogik-mq.cfg.sample'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            new_value = eval("args.{0}_{1}".format(sect, item[0]))
            if new_value != item[1] and new_value != '' and new_value != None:
                # need to write it to config file
                print("Set [{0}] : {1} = {2}".format(sect, item[0], new_value))
                config.set(sect, item[0], new_value)
                newvalues = True
            debug("Value {0} in domogik-mq.cfg set to {1}".format(item[0], new_value))
    # write the config file
    with open('/etc/domogik/domogik-mq.cfg', 'wb') as configfile:
        ok("Writing the config file")
        config.write(configfile)

def needupdate():
    # first check if there are already some config files
    if os.path.isfile("/etc/domogik/domogik-mq.cfg"):
        print("Do you want to keep your current config files ? [Y/n]: "),
        new_value = sys.stdin.readline().rstrip('\n')
        if new_value == "y" or new_value == "Y" or new_value == '':
            debug("keeping curent config files")
            return False
        else:
            debug("NOT keeping curent config files")
            return True
    return True

def update_default(user):
    info("Update /etc/default/domogik-mq")
    os.system('sed -i "s;^DOMOGIK_USER.*$;DOMOGIK_USER={0};" /etc/default/domogik-mq'.format(user))

def install():
    parser = argparse.ArgumentParser(description='Domogik MQ installation.')
    parser.add_argument('--no-setup', dest='setup', action="store_true",
                   default=False, help='Don\'t install the python packages')
    parser.add_argument('--no-test', dest='test', action="store_true",
                   default=False, help='Don\'t run a config test')
    parser.add_argument('--no-config', dest='config', action="store_true",
                   default=False, help='Don\'t run a config writer')
    parser.add_argument('--no-create-user', dest='user_creation', \
                   action="store_false", \
                   default=True, help='Don\'t create a user')
    parser.add_argument('--daemon', dest='install_daemon', \
                    action="store_true", \
                    default=True, help='Install the daemon (master mode)')
    parser.add_argument("--user",
                   help="Set the domogik user")
    parser.add_argument("--user-shell", dest="user_shell",
                   help="Set the domogik user shell")

    # generate dynamically all arguments for the various config files
    # notice that we MUST NOT have the same sections in the different files!
    parser.add_argument('--command-line', dest='command_line', \
            action="store_true", default=False, \
            help='Configure the configuration files from the command line only')
    add_arguments_for_config_file(parser, \
            "examples/config/domogik-mq.cfg.sample")

    args = parser.parse_args()
    try:
        # CHECK python version
        if sys.version_info < (2, 6):
            print "Python version is to low, at least python 2.6 is needed"
            exit(0)

        # CHECK sources not in / or /root
        info("Check the sources location (not in /root/ or /")
        print os.getcwd()
        assert os.getcwd().startswith("/root/") == False, "Domogik MQ sources must not be located in the /root/ folder"

        # CHECK run as root
        info("Check this script is started as root")
        assert os.getuid() == 0, "This script must be started as root"
        ok("Correctly started with root privileges.")

        # RUN setup.py
        if not args.setup:
            info("Run setup.py")
            if os.system('python setup.py develop') !=  0:
                raise OSError("setup.py doesn't finish correctly")

        # ask for the domogik user
        if args.user == None or args.user == '':
            user = ask_user_name()
        else:
            ok("User setted to '{0}' from the command line".format(args.user))
            user = args.user

        # create user
        if args.user_creation:
            if args.user_shell:
                create_user(user, args.user_shell)
            else:
                create_user(user)

        # Ask Master or Client install
        if args.command_line:
            if args.install_daemon:
                master = True
            else:
                master = False
        else:
            master = ask_master_install()

        # Copy files
        copy_files(user, master)
        update_default(user)

        # write config file
        if args.command_line:
            info("Update the config file : /etc/domogik/domogik-mq.cfg")
            write_domogik_configfile_from_command_line(args)

        else:
            if not args.config and needupdate():
                info("Update the config file : /etc/domogik/domogik-mq.cfg")
                write_domogik_configfile(False)
    except:
        import traceback
        print "========= TRACEBACK ============="
        print traceback.format_exc()
        print "================================="
        fail(sys.exc_info())

def add_arguments_for_config_file(parser, fle):
    # read the sample config file
    config = ConfigParser.RawConfigParser()
    config.read( [fle] )
    for sect in config.sections():
        for item in config.items(sect):
            key = "{0}_{1}".format(sect, item[0])
            parser.add_argument("--{0}".format(key),
                help="Update section {0}, key {1} value".format(sect, item[0]))

if __name__ == "__main__":
    install()
