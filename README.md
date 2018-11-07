# aiosnmp
[![Build Status](https://travis-ci.com/hh-h/aiosnmp.svg?branch=master)](https://travis-ci.com/hh-h/aiosnmp)
[![PyPI version](https://badge.fury.io/py/aiosnmp.svg)](https://badge.fury.io/py/aiosnmp)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://img.shields.io/badge/license-MIT-brightgreen.svg)
[![Python version](https://img.shields.io/badge/python-3.6%2B-brightgreen.svg)](https://img.shields.io/badge/python-3.6%2B-brightgreen.svg)

aiosnmp is an asynchronous SNMP client for use with asyncio.

## Installation
```shell
pip install aiosnmp
```

## Notice
Only snmp v2c supported, no v3 support

## Basic Usage
```python
import asyncio
import aiosnmp

async def main():
    snmp = aiosnmp.Snmp(host="127.0.0.1", port=161, community="public")

    for res in await snmp.get(".1.3.6.1.2.1.1.1.0"):
        print(res.oid, res.value)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

more in [**/examples**](https://github.com/hh-h/aiosnmp/tree/master/examples)

## TODO
* documentation
* snmp v3 support
* more tests

## License
aiosnmp is developed and distributed under the MIT license.
