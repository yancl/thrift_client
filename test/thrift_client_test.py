import sys
sys.path.insert(0, '../')

import subprocess
import time
from lib import ThriftClient, ArgumentError, NoServersAvailable
from greeter.greeter import Client
from nose.tools import raises

class TestThriftClient(object):
    def setUp(self):
        print 'set up resources'
        self._servers = ["127.0.0.1:19991", "127.0.0.1:19992", "127.0.0.1:19993"]
        self._port = 19991
        self._timeout = 0.2
        self._options = {'protocol_extra_params':[False]}
        self._popen = subprocess.Popen(['python', 'greeter/server.py', '19993'])
        time.sleep(1)

    def tearDown(self):
        print 'tear down resources'
        self._popen.kill()
        self._popen.wait()

    def test_live_server(self): 
        v = ThriftClient(Client, [self._servers[-1]], self._options).greeting('world')
        assert v == 'hello,world'

    def test_inspect(self):
        client = ThriftClient(Client, [self._servers[0]], self._options)
        assert "<<class 'lib.client.ThriftClient'>(greeter.greeter.Client) @current_server=127.0.0.1:19991>" == client.inspect()
 
    @raises(NoServersAvailable)
    def test_dont_raise(self):
        self._options.update({'raise':False})
        ThriftClient(Client, [self._servers[0]], self._options).greeting('world')
        assert True

    @raises(NoServersAvailable)
    def test_dont_raise_with_defaults(self):
        self._options.update({'raise':False, 'defaults':{'greeting':1}})
        v = ThriftClient(Client, [self._servers[0]], self._options).greeting('world')
        assert v == 1

    @raises(AttributeError)
    def test_defaults_dont_override_no_method_error(self):
        self._options.update({'raise':False, 'defaults':{'missing':2}})
        ThriftClient(Client, [self._servers[0]], self._options).missing('world')

    def test_random_fall_through(self):
        self._options.update({'retries':2})
        for i in xrange(10):
            client = ThriftClient(Client, self._servers, self._options)
            client.greeting('world')
            client.disconnect()
