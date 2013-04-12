from greeter import Processor
from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol
from thrift.server.TNonblockingServer import TNonblockingServer

class GreeterHandler(object):
    def greeting(self, name):
        return 'hello,%s' % name

    def yo(self, name):
        print 'yoyo,%s' % name
        return None

class Server(object):
    def __init__(self, host, port):
        handler = GreeterHandler()
        processor = Processor(handler)
        transport = TSocket.TServerSocket(host, port)
        pfactory = TBinaryProtocol.TBinaryProtocolFactory()
        self._server = TNonblockingServer(processor,
                                    transport,
                                    pfactory,
                                    pfactory)

    def serve(self):
        self._server.serve()

if __name__ == '__main__':
    Server(host='127.0.0.1', port=9500).serve()
