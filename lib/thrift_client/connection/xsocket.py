import base
import exceptions

class Socket(base.Base):
    #def __init__(self, transport, transport_wrapper, server, timeout):
    def __init__(self, *args):
        super(Socket, self).__init__(*args)
        host, port = self._parse_server(self._server)
        self._transport = self._transport(host, port)
        self._transport.setTimeout(self._timeout*1000) #ms
        if self._transport_wrapper:
            self._transport = self._transport_wrapper(self._transport)
        self._opened = False

    def transport(self):
        return self._transport

    def connect(self):
        self.open()

    def open(self):
        if not self._opened:
            self._transport.open()
            self._opened = True

    def close(self):
        if self._opened:
            self._transport.close()

    def _parse_server(self, server):
        (host, port) = server.split(':')
        if not (host and port):
            raise exceptions.ArgumentError('server must be of form host:port')
        return (host, port)
