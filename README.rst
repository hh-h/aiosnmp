aiosnmp
=======


.. image:: https://dev.azure.com/6660879/aiosnmp/_apis/build/status/hh-h.aiosnmp?branchName=master
   :target: https://dev.azure.com/6660879/aiosnmp/_build/results?buildId=38&view=results
   :alt: Build Status


.. image:: https://img.shields.io/codecov/c/github/hh-h/aiosnmp/master.svg?style=flat
   :target: https://codecov.io/github/hh-h/aiosnmp?branch=master
   :alt: Code Coverage


.. image:: https://badge.fury.io/py/aiosnmp.svg
   :target: https://badge.fury.io/py/aiosnmp
   :alt: PyPI version


.. image:: https://img.shields.io/badge/license-MIT-brightgreen.svg
   :target: https://img.shields.io/badge/license-MIT-brightgreen.svg
   :alt: License


.. image:: https://img.shields.io/badge/code%20style-black-black.svg
   :target: https://github.com/ambv/black
   :alt: Code Style


.. image:: https://img.shields.io/badge/python-3.7%2B-brightgreen.svg
   :target: https://img.shields.io/badge/python-3.7%2B-brightgreen.svg
   :alt: Python version


aiosnmp is an asynchronous SNMP client for use with asyncio.

Notice on 0.6.0 build
---------------------

| If you have some problems with 0.6.0 build, please, create an issue and downgrade to 0.5.0.
| There is no difference between 0.5.0 and 0.6.0 only asn1 parser migrated to rust.


Installation
------------

.. code-block:: shell

   pip install aiosnmp

Documentation
-------------

https://aiosnmp.readthedocs.io/en/latest/api.html

Notice
------

| Only snmp v2c supported, v3 version is not supported
| Oids should be like ``.1.3.6...`` or ``1.3.6...``. ``iso.3.6...`` is not supported

Source address (host and port) validation
-----------------------------------------

By default, v2c should not validate source addr, but in this library, it is enabled by default.
You can disable validation by passing ``validate_source_addr=False`` to ``Snmp``.

Basic Usage
-----------

.. code-block:: python

   import asyncio
   import aiosnmp

   async def main():
       async with aiosnmp.Snmp(host="127.0.0.1", port=161, community="public") as snmp:
           for res in await snmp.get(".1.3.6.1.2.1.1.1.0"):
               print(res.oid, res.value)

   asyncio.run(main())

more in `/examples <https://github.com/hh-h/aiosnmp/tree/master/examples>`_

TODO
----

* snmp v3 support
* more tests

License
-------

aiosnmp is developed and distributed under the MIT license.

Run local tests
---------------

.. code-block:: shell

   pip install -r requirements-dev.txt
   tox

Before submitting PR
--------------------

.. code-block:: shell

   pip install -r requirements-dev.txt
   tox -e format
