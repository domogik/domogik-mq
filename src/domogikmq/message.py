"""MQMessage

   handler class to handle a reqrep message

   this wrapper is written to easely extend the message type later on,
"""

import json
from collections import OrderedDict

class MQMessage():
    """MQMessage
       => part 0 = action (config.get, config,set, config.result)
       => part 1 = data
    """
    _action = None
    _data = {}

    def __init__(self, action=None, data=None):
        """ __init__
            can set action and data field
        """
        if action:
            self._action = self.set_action(action)
        else:
            self._action = None
        if data:
            self._data = data
        else:
            self._data = {}

    def set_action(self, action):
        """ setAction
            sets the action field
        """
        self._action = bytes(action, 'utf-8') if isinstance(action, str) else action

    def set_data(self, data):
        """ set_data
            sets the data field
        """
        self._data = data

    def add_data(self, key, value):
        """ addData
            append a data element to the stack
        """
        self._data[key] = value

    def get_action(self):
        """ getAction
            returns the current action
        """
        return self._action.decode()

    def get_data(self):
        """ getData
            returns the current data
        """
        return self._data

    def get(self):
        """ get
            returns a compiled list
        """
        stack = []
        stack.append( self._action )
        stack.append( json.dumps(self._data).encode() )
        return stack

    def set(self, stack):
        """ set
            input a message list and decompile
        """
        self._action = stack.pop(0)
        self._data = json.loads(stack.pop(0).decode(), object_pairs_hook=OrderedDict)

    def __repr__(self):
        """Return an internal representation of the class"""
        return "<MQMessage(action={0}, data='{1}')>".format(self._action, self._data)

