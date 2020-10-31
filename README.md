# aiosnmp
[![Build Status](https://dev.azure.com/6660879/aiosnmp/_apis/build/status/hh-h.aiosnmp?branchName=master)](https://dev.azure.com/6660879/aiosnmp/_build/results?buildId=38&view=results)
[![Code Coverage](https://img.shields.io/codecov/c/github/hh-h/aiosnmp/master.svg?style=flat)](https://codecov.io/github/hh-h/aiosnmp?branch=master)
[![PyPI version](https://badge.fury.io/py/aiosnmp.svg)](https://badge.fury.io/py/aiosnmp)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://img.shields.io/badge/license-MIT-brightgreen.svg)
[![Code Style](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)
[![Python version](https://img.shields.io/badge/python-3.6%2B-brightgreen.svg)](https://img.shields.io/badge/python-3.6%2B-brightgreen.svg)

aiosnmp is an asynchronous SNMP client for use with asyncio.

## Installation
```shell
pip install aiosnmp
```

## Notice
Only snmp v2c supported, v3 version is not supported  
Oids should be like `.1.3.6...` or `1.3.6...`. `iso.3.6...` is not supported

## Basic Usage
```python
import asyncio
import aiosnmp

async def main():
    async with aiosnmp.Snmp(host="127.0.0.1", port=161, community="public") as snmp:
        for res in await snmp.get(".1.3.6.1.2.1.1.1.0"):
            print(res.oid, res.value)

asyncio.run(main())
```

more in [**/examples**](https://github.com/hh-h/aiosnmp/tree/master/examples)

## TODO
* documentation
* snmp v3 support
* more tests

## License
aiosnmp is developed and distributed under the MIT license.

## Run local tests
```shell
pip install -r requirements-dev.txt
tox
```

## Before submitting PR
```shell
pip install -r requirements-dev.txt
tox -e format
```
