import sys
sys.path.insert(0, '../')

import subprocess
import time
from lib import ThriftClient, ArgumentError, NoServersAvailable
from greeter.greeter import Client
from nose.tools import raises, ok_, eq_
import functools

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
        eq_(v, 'hello,world')

    def test_inspect(self):
        client = ThriftClient(Client, [self._servers[0]], self._options)
        eq_("<<class 'lib.client.ThriftClient'>(greeter.greeter.Client) @current_server=127.0.0.1:19991>",
            client.inspect())
 
    def test_dont_raise(self):
        self._options.update({'raise':False})
        ThriftClient(Client, [self._servers[0]], self._options).greeting('world')

    def test_dont_raise_with_defaults(self):
        self._options.update({'raise':False, 'defaults':{'greeting':1}})
        v = ThriftClient(Client, [self._servers[0]], self._options).greeting('world')
        eq_(v, 1)

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

    def test_lazy_connection(self):
        ThriftClient(Client, self._servers[0:2], self._options)

    def test_post_conn_cb(self):
        def post_connect(m, handle):
            m['calledcnt'] += 1
            eq_(handle, client)

        m = {'calledcnt':0}
        client = ThriftClient(Client, self._servers, self._options)
        r = client.add_callback('post_connect', functools.partial(post_connect, m))
        eq_(client, r)
        client.greeting("someone")
        client.disconnect()
        eq_(1, m['calledcnt'])

    def test_before_method_cb(self):
        def before_method(m, method_name):
            try:
                m[method_name] += 1
            except KeyError,e:
                m[method_name] = 1

        before_method_counts = {}

        client = ThriftClient(Client, self._servers, self._options)
        r = client.add_callback('before_method', functools.partial(before_method, before_method_counts))
        eq_(client, r)
        client.greeting("someone")
        client.yo("dude")
        client.yo("dawg")
        client.disconnect()
        eq_({'greeting':1, 'yo':2}, before_method_counts)

    def test_on_exception_cb(self):
        def on_exception(on_exception_counts, e, method_name):
            try:
                on_exception_counts[method_name][e.__class__.__name__] += 1
            except KeyError:
                if method_name not in on_exception_counts:
                    on_exception_counts[method_name] = {}
                if e.__class__.__name__ not in on_exception_counts[method_name]:
                    on_exception_counts[method_name][e.__class__.__name__] = 1

        on_exception_counts = {}
        client = ThriftClient(Client, self._servers[0:2], self._options)
        r = client.add_callback('on_exception', functools.partial(on_exception, on_exception_counts))
        eq_(client, r)
        try:
            client.greeting("someone")
        except NoServersAvailable:
            client.disconnect()
        eq_({'greeting': {'NoServersAvailable': 1}}, on_exception_counts)
