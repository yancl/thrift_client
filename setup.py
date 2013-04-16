#!/usr/bin/env python

from distutils.core import setup

setup(
        name = "thrift_client",
        version = "0.10",
        description="python thrift client supports failover",
        maintainer="yancl",
        maintainer_email="kmoving@gmail.com",
        packages=['thrift_client', 'thrift_client.client', 'thrift_client.client.connection']
)
