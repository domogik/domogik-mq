from netifaces import interfaces, ifaddresses, AF_INET, AF_INET6



def socketid2hex(sid):
    """Returns printable hex representation of a socket id.
    """
    ret = ''.join("%02X" % ord(c) for c in sid)
    return ret

def split_address(msg):
    """Function to split return Id and message received by ROUTER socket.

    Returns 2-tuple with return Id and remaining message parts.
    Empty frames after the Id are stripped.
    """
    ret_ids = []
    for i, p in enumerate(msg):
        if p:
            ret_ids.append(p)
        else:
            break
    return (ret_ids, msg[i + 1:])

def get_ip(ip_type=AF_INET, log = None):
    """ Returns the first ip available (127... if only lo available, another if more than one available)
    @param ip_type: what ip type to get, can be
        AF_INET: for ipv4
        AF_INET6: for ipv6
    @return: one ip
    """
    interfaces_list = interfaces()
    if 'lo' in interfaces_list and len(interfaces_list) > 1: 
        interfaces_list.remove('lo')
    ips = []
    for intf in interfaces_list:
        intf = intf.strip()
        try:
            for addr in ifaddresses(intf)[ip_type]:
                msg = "Candidate ip : {0}".format(addr['addr'])
                if log != None:
                    log.info(msg)
                else:
                    print(msg)
                ips.append(addr['addr'])
        except:
            msg = "The network interface '{0}' is not available".format(intf)
            if log != None:
                log.debug(msg)
            else:
                print("{0}".format(msg))
    if len(ips) > 0:
        ip = ips[0]
    else:
        ip = None
    return ip


if __name__ == "__main__":
    print(get_ip())
