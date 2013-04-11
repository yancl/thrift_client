import xsocket

class Factory(object):
    @classmethod
    def create(cls, transport, transport_wrapper, server, timeout):
        return xsocket.Socket(transport, transport_wrapper, server, timeout)
