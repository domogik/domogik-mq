
import zmq
import json
import sys
from time import time, sleep
from domogikmq.configloader import Loader
from domogikmq.common.utils import get_ip
import traceback

MSG_VERSION = "0_1"

class MQPub():
    def __init__(self, context, caller_id):
        print("MQPub > __init__")
        cfg = Loader('mq').load()
        self.cfg_mq = dict(cfg[1])
        if self.cfg_mq['ip'].strip() == "*":
            self.cfg_mq['ip'] = get_ip()
        pub_addr = "tcp://{0}:{1}".format(self.cfg_mq['ip'], self.cfg_mq['pub_port'])
        self.caller_id = caller_id
        self.s_send = context.socket(zmq.PUB)
        self.s_send.connect(pub_addr)

        """ About the below sleep :
            http://zguide.zeromq.org/page%3aall

            There is one more important thing to know about PUB-SUB sockets: you do not know precisely when a subscriber starts to get messages. Even if you start a subscriber, wait a while, and then start the publisher, the subscriber will always miss the first messages that the publisher sends. This is because as the subscriber connects to the publisher (something that takes a small but non-zero time), the publisher may already be sending messages out.

            This "slow joiner" symptom hits enough people often enough that we're going to explain it in detail. Remember that ZeroMQ does asynchronous I/O, i.e., in the background. Say you have two nodes doing this, in this order:

            Subscriber connects to an endpoint and receives and counts messages.
            Publisher binds to an endpoint and immediately sends 1,000 messages.
            Then the subscriber will most likely not receive anything. You'll blink, check that you set a correct filter and try again, and the subscriber will still not receive anything.

            Making a TCP connection involves to and from handshaking that takes several milliseconds depending on your network and the number of hops between peers. In that time, ZeroMQ can send many messages. For sake of argument assume it takes 5 msecs to establish a connection, and that same link can handle 1M messages per second. During the 5 msecs that the subscriber is connecting to the publisher, it takes the publisher only 1 msec to send out those 1K messages.
        """
        sleep(0.01)
        print("MQPub > End __init__")

    def __del__(self):
        print("MQPub > __del__ : 10ms pause")
        sleep(0.01)
        print("MQPub > __del__ : close connection")
        self.s_send.close()

    def send_event(self, category, content):
        """Send an event in in multi-part : first message id and then its content

        @param category : category of the message
        @param content : content of the message : must be in JSON format

        """
        try:
            print("MQPub > send_event category='{0}'".format(category))
            msg_id = "{0}.{1}.{2}".format(category, str(time()).replace('.','_'), MSG_VERSION)
            self.s_send.send_multipart([str.encode(msg_id),str.encode(json.dumps(content)) ] )
        except:
            print(u"MQPub > send_event > ERROR : {0}".format(traceback.format_exc()))
        #self.s_send.send( json.dumps(content) )

