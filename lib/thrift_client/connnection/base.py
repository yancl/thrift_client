class Base(object):
    def __init__(self, transport, transport_wrapper, server, timeout):
        self._transport = transport
        self._transport_wrapper = transport_wrapper
        self._server = server
        self._timeout = timeout

    def connect(self):
        raise NotImplementedError('connect not implemented in base')

    def open(self):
        raise NotImplementedError('open not implemented in base')

    def close(self):
        raise NotImplementedError('close not implemented in base')
