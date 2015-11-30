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

Module purpose
==============

PUB-SUB forwarder

Implements
==========


@author: Marc SCHNEIDER <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import zmq
#import daemon
from domogikmq.common.daemon import daemon
import sys
from domogikmq.configloader import Loader
from domogikmq import logger
from domogikmq.common.utils import get_ip
import traceback

def main():
    """
       Main loop for the forwarder
    """

    cfg = Loader('mq').load()
    config = dict(cfg[1])
    log = logger.Logger('mq_forwarder').get_logger()
    log.info("Starting the forwarder")
    frontend = None
    backend = None
    context = None
    
    try:
        context = zmq.Context(1)

        # Socket facing emitters
        frontend = context.socket(zmq.XSUB)
        # Forwarder subscribes to the emitter *pub* port
        if config['ip'].strip() == "*":
            config['ip'] = get_ip(log = log)
        sub_addr = "tcp://{0}:{1}".format(\
                   config['ip'], config['pub_port'])
        log.info("Waiting for messages on {0} [BIND]".format(sub_addr))
        frontend.bind(sub_addr)
        # We want to get all messages from emitters
        #frontend.setsockopt(zmq.SUBSCRIBE, "")
        
        # Socket facing receivers
        backend = context.socket(zmq.XPUB)
        # Forwarder publishes to the receiver *sub* port
        pub_addr = "tcp://{0}:{1}".format(\
                   config['ip'], config['sub_port'])
        log.info("Sending messages to {0} [BIND]".format(pub_addr))
        backend.bind(pub_addr)
        
        log.info("Forwarding messages...")
        #zmq.device(zmq.FORWARDER, frontend, backend)
        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)
        while True:
            events = dict(poller.poll(1000))
            if frontend in events:
                message = frontend.recv_multipart()
                log.debug("Forwarding message: {0}".format(message[0]))
                backend.send_multipart(message)
            if backend in events:
                message = backend.recv_multipart()
                log.error("BAD direction message: {0}".format(message))
                frontend.send_multipart(message)
    except Exception as exp:
        log.error(exp)
        log.error("Bringing down ZMQ device")
        raise Exception("Error with forwarder device : {0}".format(traceback.format_exc()))
    finally:
        if frontend != None:
            frontend.close()
        if backend != None:
            backend.close()
        if context != None:
            context.term()
        log.info("Forwarder stopped")

if __name__ == "__main__":
    with daemon.DaemonContext(
        stderr=sys.stderr,
        stdin=sys.stdin,
        stdout=sys.stdout):
        main()

"""
    xpub = ctx.socket(zmq.XPUB)
    xpub.bind(xpub_url)
    xsub = ctx.socket(zmq.XSUB)
    xsub.bind(xsub_url)

    poller = zmq.Poller()
    poller.register(xpub, zmq.POLLIN)
    poller.register(xsub, zmq.POLLIN)
    while True:
        events = dict(poller.poll(1000))
        if xpub in events:
            message = xpub.recv_multipart()
            print("[BROKER] subscription message: {0}".format(message[0]))
            xsub.send_multipart(message)
        if xsub in events:
            message = xsub.recv_multipart()
            # print("publishing message: {0}".format(message))
            xpub.send_multipart(message)
"""
