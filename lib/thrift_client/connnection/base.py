class Base(object):
    def __init__(self, transport, transport_wrapper, server, timeout):
        self._transport = transport
        self._transport_wrapper = transport_wrapper
        self._server = server
        self._timeout = timeout

    def connect(self):
        raise NotImplementedError('connect not implemented in base')

    def open(self):
        self._transport.open()

    def close(self):
        self._transport.close()
