#!/bin/bash
#This file is part of B{Domogik} project (U{http://www.domogik.org}).
#
#License
#=======
#
#B{Domogik} is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#B{Domogik} is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Domogik. If not, see U{http://www.gnu.org/licenses}.
#
#Module purpose
#==============
#
#Clean domogik-mq installation
#
#Implements
#==========
#
#
#@author: Fritz < fritz.smh@gmail.com>
#@copyright: (C) 2007-2014 Domogik project
#@license: GPL(v3)
#@organization: Domogik



function stop_domogik_mq {
    if [ -f "/etc/init.d/domogik-mq" -o -f "/etc/rc.d/domogik-mq" ];then
        [ -f /etc/conf.d/domogik-mq ] && . /etc/conf.d/domogik-mq
        [ -f /etc/default/domogik-mq ] && . /etc/default/domogik-mq
        if [ -f "/etc/domogik/domogik.cfg" ];then
            echo "There is a Domogik on this system. Domogik won't run without Domogik-mq. Try to stop it before uninstall..."
            /etc/init.d/domogik stop
        fi
        if [ -f "/etc/domogik/domogik-mq.cfg" ];then
            echo "There is already a Domogik-mq on this system. Try to stop it before uninstall..."
            /etc/init.d/domogik-mq stop
        fi
    else
        echo "It seems Domogik-mq is not installed : no /etc/init.d|rc.d/domogik-mq file"
        exit 16
    fi
}


# IS root user ?
if [ $UID -ne 0 ];then
    echo "Please restart this script as root!"
    exit 10
fi

# Ask for confirmation
echo "This script will uninstall completely Domogik-mq :"
echo "- Domogik-mq core"
echo "- Configuration"
echo "- Logs"
echo "- ..."
echo "Are you sure ? [y/N]"
read choice
if [ "x"$choice == "x" ] ; then
    choice=n
fi
if [ $choice != "y" -a $choice != "Y" ] ; then
    echo "Aborting..."
    exit 0
fi

stop_domogik_mq

[ ! -f /etc/default/domogik-mq ] && [ ! -f /etc/conf.d/domogik-mq ] && echo "File /etc/default/domogik-mq or /etc/conf.d/domogik-mq doesn't exists : exiting" && exit 1

[ -f /etc/conf.d/domogik-mq ] && . /etc/conf.d/domogik-mq && GLOBAL_CONFIG=/etc/conf.d/domogik-mq
[ -f /etc/default/domogik-mq ] && . /etc/default/domogik-mq && GLOBAL_CONFIG=/etc/default/domogik-mq

echo "Domogik-mq installation found for user : $DOMOGIK_USER"

#RM="ls -l "  # for simulation
RM="rm -Rf "

echo "Delete /etc/default/domogik-mq"
$RM /etc/default/domogik-mq

echo "Delete rc.d script"
[ -f /etc/init.d/domogik-mq ] && $RM /etc/init.d/domogik-mq
[ -f /etc/rc.d/domogik-mq ] && $RM /etc/rc.d/domogik-mq

CONFIG_FILE=/etc/domogik/domogik-mq.cfg*
echo "Delete config file : $CONFIG_FILE"
$RM $CONFIG_FILE

echo "Delete $GLOBAL_CONFIG"
$RM $GLOBAL_CONFIG

echo "Delete /var/log/domogik/mq*"
$RM /var/log/domogik/mq*

PY_FOLDER=$(dirname $(python -c "print __import__('domogikmq').__path__[0]"))
if [[ ${PY_FOLDER:0:5} == "/usr/" ]] ; then
    echo "Remove python part : $PY_FOLDER"
    $RM $PY_FOLDER
else
    echo "Not removing $PY_FOLDER"
    echo "It seems to be development files"
fi

echo "Uninstall complete!"





