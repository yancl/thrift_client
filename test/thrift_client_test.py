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
        self._servers = ["127.0.0.1:19991", "127.0.0.1:19992", "127.0.0.1:19993"]
        self._port = 19991
        self._timeout = 0.2
        self._options = {'protocol_extra_params':[False]}
        self._popen = subprocess.Popen(['python', 'greeter/server.py', '19993'])
        time.sleep(1)

    def tearDown(self):
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

    def test_unknown_cb(self):
        def _():
            assert False
        client = ThriftClient(Client, self._servers, self._options)
        r = client.add_callback('unknown', _)
        eq_(r, None) 

    def test_multiple_cb(self):
        def post_connect(m, handle):
            m['calledcnt'] += 1
            eq_(handle, client)

        m = {'calledcnt':0}
        client = ThriftClient(Client, self._servers, self._options)
        for i in xrange(2):
            r = client.add_callback('post_connect', functools.partial(post_connect, m))
            eq_(client, r)
        client.greeting("someone")
        client.disconnect()
        eq_(2, m['calledcnt'])

    def test_no_servers_eventually_raise(self):
        def post_connect(m, handle):
            m['calledcnt'] += 1
            eq_(handle, client)

        m = {'calledcnt':0}
        client = ThriftClient(Client, self._servers[0:2], self._options)
        r = client.add_callback('post_connect', functools.partial(post_connect, m))
        try:
            client.greeting('someone')
        except NoServersAvailable:
            client.disconnect()
        eq_(0, m['calledcnt'])

    def test_socket_timeout(self):
        try:
            import time
            (q, threads) = self._stub_server(self._port)
            t0 = time.time()
            try:
                self._options.update({'timeout':1, 'connect_timeout':0.5})
                client = ThriftClient(Client, ['127.0.0.1:%d' % self._port], self._options).greeting('someone')
            except IOError: # socket.timeout subs IOError
                pass
            t1 = time.time()
            real = t1 - t0
            ok_(real > 0.5 and real < 1.05)
        finally:
            q.put(False)
            self._stop_server(threads)

    def test_framed_transport_timeout(self):
        try:
            import time
            (q, threads) = self._stub_server(self._port)
            t0 = time.time()
            try:
                self._options.update({'timeout':self._timeout, 'connect_timeout':self._timeout})
                client = ThriftClient(Client, ['127.0.0.1:%d' % self._port], self._options).greeting('someone')
            except IOError: # socket.timeout subs IOError
                pass
            t1 = time.time()
            real = t1 - t0
            ok_(real > self._timeout)
        finally:
            q.put(False)
            self._stop_server(threads)

    def test_buffered_transport_timeout(self):
        try:
            from thrift.transport import TTransport
            import time
            (q, threads) = self._stub_server(self._port)
            t0 = time.time()
            try:
                self._options.update({  'timeout':self._timeout,
                                        'connect_timeout':self._timeout,
                                        'transport_wrapper':TTransport.TBufferedTransport})
                client = ThriftClient(Client, ['127.0.0.1:%d' % self._port], self._options).greeting('someone')
            except IOError: # socket.timeout subs IOError
                pass
            t1 = time.time()
            real = t1 - t0
            ok_(real > self._timeout)
        finally:
            q.put(False)
            self._stop_server(threads)

    def test_buffered_transport_timeout_override(self):
        try:
            # FIXME Large timeout values always are applied twice for some bizarre reason
            log_timeout = 4 * self._timeout
            from thrift.transport import TTransport
            import time
            (q, threads) = self._stub_server(self._port)
            t0 = time.time()
            try:
                self._options.update({  'timeout':self._timeout,
                                        'timeout_overrides':{'greeting': log_timeout},
                                        'transport_wrapper':TTransport.TBufferedTransport})
                client = ThriftClient(Client, ['127.0.0.1:%d' % self._port], self._options).greeting('someone')
            except IOError: # socket.timeout subs IOError
                pass
            t1 = time.time()
            real = t1 - t0
            ok_(real > log_timeout)
        finally:
            q.put(False)
            self._stop_server(threads)

    def test_retry_period(self):
        self._options.update({'server_retry_period':1, 'retries':2})
        client = ThriftClient(Client, self._servers[0:2], self._options)
        try:
            client.greeting('someone')
        except NoServersAvailable:
            pass

        import time
        time.sleep(1.1)

        try:
            client.greeting('someone')
        except NoServersAvailable:
            pass

    @raises(NoServersAvailable)
    def test_connect_retry_period(self):
        self._options.update({'server_retry_period':0})
        client = ThriftClient(Client, [self._servers[0]], self._options)
        client.connect()

    def test_client_with_retry_period_drops_servers(self):
        self._options.update({'server_retry_period':1, 'retries':2})
        client = ThriftClient(Client, [self._servers[0]], self._options)
        try:
            client.greeting("someone")
        except NoServersAvailable:
            pass
        import time
        time.sleep(1.1)
        try:
            client.greeting("someone")
        except NoServersAvailable:
            pass

    def test_oneway_method(self):
        self._options.update({'server_max_requests':2, 'retries':2})
        client = ThriftClient(Client, self._servers, self._options)
        r = client.yo('dude')

    def test_server_max_requests_with_downed_servers(self):
        self._options.update({'server_max_requests':2, 'retries':2})
        client = ThriftClient(Client, self._servers, self._options)
        client.greeting("someone")
        last_client = client._last_client

        client.greeting("someone")
        eq_(last_client, client._last_client)

        # This next call maxes out the requests for that "client" object
        # and moves on to the next.
        client.greeting("someone")
        new_client = client._last_client
        ok_(last_client, new_client)

        # And here we should still have the same client as the last one...
        client.greeting("someone")
        eq_(new_client, client._last_client)

        # Until we max it out, too.
        client.greeting("someone")
        ok_(last_client, client._last_client)

    def _stub_server(self, port):
        import Queue
        q = Queue.Queue()
        q.put(True)
        def looper(q):
            sock = None
            socks = []
            try:
                import socket
                sock = socket.socket()
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('127.0.0.1', port))
                sock.listen(10)
                while q.get():
                    (s, a) = sock.accept()
                    socks.append(s)
            finally:
                #clean up
                for sock in socks:
                    sock.close()
                if sock:
                    sock.close()

        import threading
        t = threading.Thread(target=functools.partial(looper, q))
        t.setDaemon(True)
        t.start()
        threads = [t]
        return (q, threads)

    def _stop_server(self, threads):
        for thread in threads:
            thread.join()
