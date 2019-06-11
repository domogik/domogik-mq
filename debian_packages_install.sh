#!/bin/bash

# INFORMATIONS
# ============
#
# * mysql-server is not installed by the install.py script as the database must
#   be created before launching the install.py script

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi


function continue() {

    if [ $1 -ne 0 ] ; then
        echo "Something bad happens during command"
        echo "You should stop this step to see what is bad"
        cont=""
        while [ "x${cont}" == "x" ] ; do
            echo "Continue [Y/n] ?"
            read cont
            if [ "x${cont}" == "xY" ] ; then
                echo "OK, let's continue..."
            elif [ "x${cont}" == "xn" ] ; then
                echo "Exiting!"
                exit 1
            else
                cont=""
            fi
        done
    fi
}

pkg_list="\
         git \
         gcc\
         libzmq3-dev \
         \
         python3 \
         python3-dev \
         python3-pkg-resources \
         python3-setuptools \
         python3-pip \
         python3-zmq \
         python3-netifaces \
         "

apt-get update
continue $?

apt-get install $pkg_list
continue $?

pip_list=" "

for elt in $pip_list
  do
    pip3 install $elt
    continue $?
done


