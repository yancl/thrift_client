import base
import exceptions

class Socket(base.Base):
    def __init__(self, transport, transport_wrapper, server, timeout):
        super(Socket, self).__init__(transport, transport_wrapper, server, timeout)
        host, port = self._parse_server(self._server)
        self._transport = transport(host, port)
        self._transport.setTimeout(timeout*1000) #ms
        if transport_wrapper:
            self._transport = self._transport_wrapper(self._transport)

    def connect(self):
        self.open()

    def open(self):
        self._transport.open()

    def close(self):
        self._transport.close()

    def _parse_server(self, server):
        (host, port) = server.split(':')
        if not (host and port):
            raise exceptions.ParamInvalidException('server must be of form host:port')
        return (host, port)
