import sys
sys.path.insert(0, '../')

import subprocess
import time
from lib import ThriftClient, ArgumentError, NoServersAvailable
from greeter.greeter import Client

class TestThriftClient(object):
    def setUp(self):
        print 'set up resources'
        self._servers = ["127.0.0.1:9991", "127.0.0.1:9992", "127.0.0.1:9993"]
        self._port = 9991
        self._timeout = 0.2
        self._options = {'protocol_extra_params':[False]}
        self._popen = subprocess.Popen(['python', 'greeter/server.py', '9993'])
        time.sleep(3)

    def tearDown(self):
        print 'tear down resources'
        self._popen.kill()
        self._popen.wait()

    def test_live_server(self): 
        v = ThriftClient(Client, [self._servers[-1]], self._options).greeting('world')
        assert v == 'hello,world'
