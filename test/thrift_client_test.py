import sys
sys.path.insert(0, '../')

from lib import ThriftClient, ArgumentError, NoServersAvailable
from greeter.greeter import Client

if __name__ == '__main__':
    print ThriftClient(client_class=Client,servers=['127.0.0.1:9500'], options={}).greeting('yancl')
    ThriftClient(client_class=Client,servers=['127.0.0.1:9500'], options={}).yo('yancl')
