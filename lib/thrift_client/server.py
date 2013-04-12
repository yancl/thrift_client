from connection import factory
import utils

class Server(object):
    def __init__(self, conn_str, client_class, options = {}):
        self._conn_str = conn_str
        self._client_class = client_class
        self._options = options
        self._markdown_til = None
        self._client = None
        self._connected = False
        self._connection = self._new_connection()

    def client(self):
        #lazy connection
        if not self._client:
            self._connect()
            transport = self._connection.transport()
            protocol = self._options['protocol'](transport)
            self._client = self._client_class(protocol)
        return self._client
        
    def mark_down(self, til):
        self.close(True)
        self._markdown_til = utils.now() + til

    def is_up(self):
        return not self.is_down()

    def is_down(self):
        if self._markdown_til and self._markdown_til > utils.now():
            return True
        return False

    def close(self, teardown=False):
        if teardown:
            self._connection.close()
            self._client = None
            self._connected = False

    def _new_connection(self):
        return factory.Factory.create(
                    self._options['transport'],
                    self._options['transport_wrapper'],
                    self._conn_str,
                    self._options['connect_timeout'])

    def _connect(self):
        if not self._connected:
            self._connection.set_timeout(self._options['connect_timeout'])
            self._connection.connect()
            self._connection.set_timeout(self._options['timeout'])

    def __str__(self):
        return self._conn_str
