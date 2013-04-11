import xsocket

class Factory(object):
    def create(self, transport, transport_wrapper, server, timeout):
        return xsocket.Socket(transport, transport_wrapper, server, timeout)
