thrift_client
=============

A Thrift client wrapper that encapsulates some common failover behavior(python version of twitter thrift client).

Features
=============

* Transparent connection management
* Configurable failover and retry backoff

The Github source repository is {here}[http://github.com/yancl/thrift_client/]. Patches and contributions are very welcome.

Usage
=============

Instantiate a client:

```python
client = ThriftClient(Cassandra.Client, ['127.0.0.1:9160',], options={'retries':2})
```

You can then make calls to the server via the <tt>client</tt> instance as if was your internal Thrift client. The connection will be opened lazily and methods will be proxied through.

```python
client.get_string_list_property("keyspaces")
```

On failures, the client will try the remaining servers in the list before giving up. See ThriftClient for more.

Timeouts
=============

Timeouts are enforced per-try, so if you have a timeout of n and do m retries, the total time it could take is n*m.

Connection Handling
=============

The library will shuffle the host list then work its way down this list, only moving to the next host if it received an error or you've doing more than server_max_requests requests with that host (defaults to 0 which means there's no limit).

Servers that throw an error get marked as dead and will only be retried every server_retry_period seconds (at that time all dead servers are retried, no matter long they've been marked as dead).

Installation
=============

  sudo easy_install thrift_client

Contributing
=============

To contribute changes:

1. Fork the project
2. make your change, adding tests
3. send a pull request to me(@yancl,@dlutcat)

Reporting problems
=============

The Github issue tracker is {here}[http://github.com/yancl/thrift_client/issues].
