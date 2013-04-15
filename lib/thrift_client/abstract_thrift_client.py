from thrift.Thrift import TException
from thrift.Thrift import TApplicationException
from thrift.transport.TTransport import TTransportException
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from connection import exceptions
from server import Server
import utils

DISCONNECT_ERRORS = (
  IOError,
  TException,
  TApplicationException,
  TTransportException
)

DEFAULT_WRAPPED_ERRORS = (
  TApplicationException,
  TTransportException,
)

DEFAULTS = {
    'protocol' : TBinaryProtocol.TBinaryProtocol,
    'protocol_extra_params' : [],
    'transport' : TSocket.TSocket,
    'transport_wrapper' : TTransport.TFramedTransport,
    'raise' : True,
    'defaults' : {},
    'exception_classes' : DISCONNECT_ERRORS,
    'exception_class_overrides' : [],
    'retries' : 0,
    'server_retry_period' : 1,
    'server_max_requests' : None,
    'retry_overrides' : {},
    'wrapped_exception_classes' : DEFAULT_WRAPPED_ERRORS,
    'connect_timeout' : 0.1,
    'timeout' : 1,
    'timeout_overrides' : {},
    'cachedconnections' : False
}

class AbstractThriftClient(object):
    def __init__(self, client_class, servers, options = {}):
        self._client_class = client_class
        import random
        random.shuffle(servers)
        self._servers = servers
        self._options = options
        self._DEFAULTS = dict(DEFAULTS)
        self._DEFAULTS.update(options)
        self._options = self._DEFAULTS
        self._server_list = [Server( conn_str=server, 
                                    client_class=client_class,
                                    options=self._options) for server in servers]
        self._server_idx = 0
        self._current_server = self._server_list[self._server_idx]
        self._callbacks = {}
        self._req_count = 0
        self._server_max_req = self._options.get('server_max_requests', 0)
        self._client = None
        self._last_client = None
        self._client_methods = []
        self._hook_methods()
        
    def add_callback(self, callback_type, f):
        if callback_type in ('post_connect', 'before_method', 'on_exception'):
            if callback_type not in self._callbacks:
                self._callbacks[callback_type] = []
            self._callbacks[callback_type].append(f)
        return self

    def connect(self, method_name):
        start_time = utils.now()
        while True:
            try:
                self._current_server = self._next_live_server()
                self._client = self._current_server.client()
                self._last_client = self._client
                self._do_callbacks('post_connect', self)
                break
            except (IOError, TTransportException), e:
                self.disconnect(True)
                timeout = self._timeout(method_name)
                if timeout and utils.now() - start_time > timeout:
                    self._no_servers_available()

    def disconnect(self, error=False):
        if self._current_server:
            if error:
                self._current_server.mark_down(self._options['server_retry_period'])
            self._current_server.close()
        self._client = None
        self._current_server = None
        self._req_count = 0

    def inspect(self):
        return ("<%(class)s(%(client_class)s) @current_server=%(current_server)s>" % 
                {'class':self.__class__,
                 'client_class':self._client_class,
                 'current_server':self._current_server})

    def _hook_methods(self):
        def _wrapper(method_name):
            def _(*args, **kwargs):
                return self._handled_proxy(method_name, *args, **kwargs)
            return _

        for name in dir(self._client_class):
            if (name.startswith('_') or 
                name.startswith('recv_') or
                name.startswith('send_')):
                continue
            fn = getattr(self._client_class, name)
            if callable(fn):
                self._client_methods.append(name)
                setattr(self, name, _wrapper(name))

    def _do_callbacks(self, callback_type, *args):
        callbacks = self._callbacks.get(callback_type, [])
        for callback in callbacks:
            callback(*args)

    def _next_live_server(self):
        length = len(self._servers)
        for i in xrange(0, length):
            cur = (1 + self._server_idx + i) % length 
            if self._server_list[cur].is_up():
                self._server_idx = cur
                return self._server_list[cur]
        self._no_servers_available()

    def _no_servers_available(self):
        raise exceptions.NoServersAvailable("No live servers in %s" % ','.join(self._servers))

    def _timeout(self, method=None):
        return self._options['timeout_overrides'].get(method, 0) or self._options['timeout']

    def _handled_proxy(self, method_name, *args, **kwargs):
        tries = self._options['retry_overrides'].get(method_name, 0) or (self._options['retries'] + 1)
        while tries > 0:
            if not self._client:
                self.connect(method_name)
            self._req_count += 1
            self._do_callbacks('before_method', method_name)
            try:
                f = getattr(self._client, method_name)
                return f(*args, **kwargs)
            except self._options['exception_class_overrides'],e:
                return self._raise_or_default(e, method_name)
            except self._options['exception_classes'],e:
                self.disconnect(True)
                tries -= 1
                if tries <= 0:
                    return self._raise_or_default(e, method_name)
            except Exception,e:
                return self._raise_or_default(e, method_name)
            finally:
                if self._server_max_req and self._req_count >= self._server_max_req:
                    self.disconnect()

    def _raise_or_default(self, e, method_name):
        if self._options['raise']:
            self._raise_wrapped_error(e, method_name)
        else:
            return self._options['defaults'].get(method_name, None)

    def _raise_wrapped_error(self, e, method_name):
        self._do_callbacks('on_exception', e, method_name)
        raise e
