import sys
sys.path.insert(0, '../')

import subprocess
import time
from lib import ThriftClient, ArgumentError, NoServersAvailable
from greeter.greeter import Client
from nose.tools import raises, ok_, eq_
import functools

class TestMultiServer(object):
    def setUp(self):
        self._servers = ["127.0.0.1:19991", "127.0.0.1:19992", "127.0.0.1:19993"]
        self._port = 19991
        self._timeout = 0.2
        self._options = {'protocol_extra_params':[False]}
        self._popens = []
        for server in self._servers:
            self._popens.append(subprocess.Popen(['python', 'greeter/server.py', server.split(':')[1]]))
        time.sleep(0.05)

    def tearDown(self):
        for popen in self._popens:
            popen.kill()
            popen.wait()

    def test_server_creates_new_client_that_can_talk_to_all_servers_after_disconnect(self):
        client = ThriftClient(Client, self._servers, self._options)
        client.greeting("someone")
        last_client = client._last_client
        client.greeting("someone")
        eq_(last_client, client._last_client) #Sanity check

        client.disconnect()

        client.greeting("someone")
        last_client = client._last_client
        client.greeting("someone")
        eq_(last_client, client._last_client)
        last_client = client._last_client
        client.greeting("someone")
        eq_(last_client, client._last_client)
        client.greeting("someone")
        client.greeting("someone")

    def test_server_doesnt_max_out_after_explicit_disconnect(self):
        self._options.update({'server_max_requests':2})
        client = ThriftClient(Client, self._servers, self._options)
        client.greeting("someone")
        last_client = client._last_client
        client.greeting("someone")
        eq_(last_client, client._last_client) # Sanity check

        client.disconnect()

        client.greeting("someone")
        last_client = client._last_client
        client.greeting("someone")
        eq_(last_client, client._last_client)

    def test_server_disconnect_doesnt_drop_servers_with_retry_period(self):
        self._options.update({'server_max_requests':2, 'retry_period':1})
        client = ThriftClient(Client, self._servers, self._options)
        for i in xrange(3):
            client.greeting("someone")
            last_client = client._last_client
            client.greeting("someone")
            eq_(last_client, client._last_client) # Sanity check

            client.disconnect()

            client.greeting("someone")
            last_client = client._last_client
            client.greeting("someone")
            eq_(last_client, client._last_client)

    def test_server_max_requests(self):
        self._options.update({'server_max_requests':2})
        client = ThriftClient(Client, self._servers, self._options)
        client.greeting("someone")
        last_client = client._last_client

        client.greeting("someone")
        eq_(last_client, client._last_client)

        # This next call maxes out the requests for that "client" object
        # and moves on to the next.
        client.greeting("someone")
        new_client = client._last_client
        ok_(last_client != new_client)

        # And here we should still have the same client as the last one...
        client.greeting("someone")
        eq_(new_client, client._last_client)

        # Until we max it out, too.
        client.greeting("someone")
        ok_(new_client != client._last_client)
        ok_(client._last_client != None)

        new_new_client = client._last_client
        # And we should still have one server left
        client.greeting("someone")
        eq_(new_new_client, client._last_client)
