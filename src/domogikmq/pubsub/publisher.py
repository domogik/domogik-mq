
import zmq
import json
import sys
from time import time
from domogikmq.configloader import Loader
from domogikmq.common.utils import get_ip

MSG_VERSION = "0_1"

class MQPub(object):
    def __init__(self, context, caller_id):
        cfg = Loader('mq').load()
        self.cfg_mq = dict(cfg[1])
        if self.cfg_mq['ip'].strip() == "*":
            self.cfg_mq['ip'] = get_ip()
        pub_addr = "tcp://{0}:{1}".format(self.cfg_mq['ip'], self.cfg_mq['pub_port'])
        self.caller_id = caller_id
        self.s_send = context.socket(zmq.PUB)
        self.s_send.connect(pub_addr)

    def __del__(self):
        self.s_send.close()

    def send_event(self, category, content):
        """Send an event in in multi-part : first message id and then its content

        @param category : category of the message
        @param content : content of the message : must be in JSON format

        """
        msg_id = "{0}.{1}.{2}".format(category, str(time()).replace('.','_'), MSG_VERSION)
        self.s_send.send_multipart([msg_id,json.dumps(content) ] )
        #self.s_send.send( json.dumps(content) )

