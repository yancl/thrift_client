#!/usr/bin/env python
import os
import sys
from setuptools import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload -r internal')
    sys.exit()

setup(
        name = "thrift_client",
        version = "0.10",
        description="python thrift client supports failover",
        long_description=open("README.md").read(),
        author="yancl",
        author_email="kmoving@gmail.com",
        url='https://github.com/yancl/thrift_client',
        classifiers=[
            'Programming Language :: Python',
        ],
        platforms='Linux',
        license='MIT License',
        zip_safe=False,
        install_requires=[
            'distribute',
            'thrift',
        ],
        tests_require=[
            'nose',
        ],
        packages=['thrift_client', 'thrift_client.client', 'thrift_client.client.connection']
)
