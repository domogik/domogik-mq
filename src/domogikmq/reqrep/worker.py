	# -*- coding: utf-8 -*-

"""Module containing worker functionality for the MDP implementation.

For the MDP specification see: http://rfc.zeromq.org/spec:7
"""

__license__ = """
    This file is part of MDP.

    MDP is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    MDP is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with MDP.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = 'Guido Goldstein'
__email__ = 'gst-py@a-nugget.de'


import sys
import time
from pprint import pprint
import traceback

import zmq
from zmq.eventloop.zmqstream import ZMQStream
from zmq.eventloop.ioloop import IOLoop, DelayedCallback, PeriodicCallback

from domogikmq.configloader import Loader
from domogikmq.common.utils import split_address
from domogikmq.message import MQMessage
from domogikmq.socket import ZmqSocket
from domogikmq.common.utils import get_ip

# Debug mode to activate to get stdout informations
DEBUG = False

class MQRep(object):

    """Class for the MDP worker side.

    Thin encapsulation of a zmq.DEALER socket.
    Provides a send method with optional timeout parameter.

    Will use a timeout to indicate a broker failure.
    """

    _proto_version = b'MDPW01'

    # TODO: integrate that into API
    HB_INTERVAL = 1000  # in milliseconds
    HB_LIVENESS = 3    # HBs to miss before connection counts as dead

    def __init__(self, context, service):
        """Initialize the MDPWorker.

        context is the zmq context to create the socket from.
        service is a byte-string with the service name.
        """
        if DEBUG:
            print("MQRep > __init__")
        cfg = Loader('mq').load()
        config = dict(cfg[1])
        if config['ip'].strip() == "*":
            config['ip'] = get_ip()
        self.endpoint = "tcp://{0}:{1}".format(config['ip'], config['req_rep_port'])
        self.context = context
        self.service = service.encode()
        self.stream = None
        self._tmo = None
        self.need_handshake = True
        self.ticker = None
        self._delayed_cb = None
        self.envelope = None
        self._create_stream()

        ### patch fritz
        self._reconnect_in_progress = False
        ### end patch fritz
        return

    def _create_stream(self):
        """Helper to create the socket and the stream.
        """
        if DEBUG:
            print("MQRep > _create_stream")
        socket = ZmqSocket(self.context, zmq.DEALER)
        ioloop = IOLoop.instance()
        self.stream = ZMQStream(socket, ioloop)
        self.stream.on_recv(self._on_mpd_message)
        self.stream.socket.setsockopt(zmq.LINGER, 0)
        self.stream.connect(self.endpoint)
        if self.ticker != None:
            if DEBUG:
                print("MQRep > _create_stream - stop ticker")
            self.ticker.stop()
        self.ticker = PeriodicCallback(self._tick, self.HB_INTERVAL)
        self._send_ready()
        self.ticker.start()
        return

    def _send_ready(self):
        """Helper method to prepare and send the workers READY message.
        """
        if DEBUG:
            print("MQREP > _send_ready")
        ready_msg = [ b'', self._proto_version, b'\x01', self.service ]
        self.stream.send_multipart(ready_msg)
        self.curr_liveness = self.HB_LIVENESS
        if DEBUG:
            print("MQREP > _send_ready > curr_liveness <= {0}".format(self.HB_LIVENESS))
        return

    def _tick(self):
        """Method called every HB_INTERVAL milliseconds.
        """
        if DEBUG:
            print("MQREP > _tick {0}".format(self.service))
        self.curr_liveness -= 1
        if DEBUG:
            print('MQREP > _tick - {0} tick = {1}'.format(time.time(), self.curr_liveness))
        self.send_hb()
        if self.curr_liveness >= 0:
            return
        if DEBUG:
            print('MQREP > _tick - {0} lost connection'.format(time.time()))
        # ouch, connection seems to be dead
        self.shutdown()
        # try to recreate it
        self._delayed_cb = DelayedCallback(self._create_stream, self.HB_INTERVAL)
        self._delayed_cb.start()
        return

    def send_hb(self):
        """Construct and send HB message to broker.
        """
        msg = [ b'', self._proto_version, b'\x04' ]
        self.stream.send_multipart(msg)
        return

    def shutdown(self):
        """Method to deactivate the worker connection completely.

        Will delete the stream and the underlying socket.
        """
        if self.ticker:
            self.ticker.stop()
            self.ticker = None
        if not self.stream:
            return
        self.stream.socket.close()
        self.stream.close()
        self.stream = None
        self.timed_out = False
        self.need_handshake = True
        self.connected = False
        return

    def reply(self, msg):
        """Send the given message.

        msg can either be a byte-string or a list of byte-strings.
        """
##         if self.need_handshake:
##             raise ConnectionNotReadyError()
        # prepare full message
        to_send = self.envelope
        self.envelope = None
        if isinstance(msg, list):
            to_send.extend(msg)
        else:
            to_send.append(msg)
        if DEBUG:
            print("MQRep > Reply to {0} at {1} - {2}".format(self.service, time.strftime("%H:%M:%S"), to_send))
        self.stream.send_multipart(to_send)
        self.curr_liveness = self.HB_LIVENESS
        return

    def _on_mpd_message(self, msg):
        """Helper method called on message receive.

        msg is a list w/ the message parts
        """
        if DEBUG:
            print("MQRep > _on_mpd_message from {0} : {1} - {2}".format(self.service, time.strftime("%H:%M:%S"), msg))
        # 1st part is empty
        msg.pop(0)
        # 2nd part is protocol version
        # TODO: version check
        proto = msg.pop(0)
        # 3rd part is message type
        msg_type = msg.pop(0)
        # XXX: hardcoded message types!
        # any message resets the liveness counter
        self.need_handshake = False
        self.curr_liveness = self.HB_LIVENESS
        if DEBUG:
            print("MQREP > _on_mpd_message > curr_liveness <= {0}".format(self.HB_LIVENESS))
        if msg_type == b'\x05': # disconnect
            if DEBUG:
                print("MQREP > _on_mpd_message > type x05 : disconnect")
            self.curr_liveness = 0 # reconnect will be triggered by hb timer
        elif msg_type == b'\x02': # request
            if DEBUG :
                print("MQREP > _on_mpd_message > type x02 : request from {0}".format(self.service))
                if self.envelope is not None :
                    print("MQREP > _on_mpd_message > request conflict : pending reply for {0}".format(self.envelope))
            # remaining parts are the user message
            envelope, msg = split_address(msg)
            envelope.append(b'')
            envelope = [ b'', self._proto_version, b'\x03'] + envelope # REPLY
            self.envelope = envelope
            mes = MQMessage()
            mes.set(msg)
            #print("MQRep > before self.on_mdp_request")
            #print(self.on_mdp_request)
            #print(mes)
            self.curr_liveness = self.HB_LIVENESS * 4 # Increase liveness for long reply ( 12 s)
            try:
                self.on_mdp_request(mes)
            except:
                print("ERROR {0}".format(traceback.format_exc()))
        else:
            if DEBUG:
                print("MQREP > _on_mpd_message > type ??? : invalid or hbeat")
            # invalid message
            # ignored
            # if \x04, this is a hbeat message
            pass
        return

    def on_mdp_request(self, msg):
        """Public method called when a request arrived.

        Must be overloaded!
        """
        pass
#

### Local Variables:
### buffer-file-coding-system: utf-8
### mode: python
### End:
