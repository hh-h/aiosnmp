API Reference
=============

Classes
^^^^^^^

.. autoclass:: aiosnmp.snmp.Snmp
   :members: get, get_next, get_bulk, walk, set, bulk_walk
.. autoclass:: aiosnmp.message.SnmpVarbind()
   :members: oid, value
.. autoclass:: aiosnmp.message.SnmpV2TrapMessage()
   :members: version, community, data

Exceptions
^^^^^^^^^^

.. autoexception:: aiosnmp.exceptions.SnmpTimeoutError()
.. autoexception:: aiosnmp.exceptions.SnmpUnsupportedValueType()
.. autoexception:: aiosnmp.exceptions.SnmpErrorTooBig()
.. autoexception:: aiosnmp.exceptions.SnmpErrorNoSuchName()
.. autoexception:: aiosnmp.exceptions.SnmpErrorBadValue()
.. autoexception:: aiosnmp.exceptions.SnmpErrorReadOnly()
.. autoexception:: aiosnmp.exceptions.SnmpErrorGenErr()
.. autoexception:: aiosnmp.exceptions.SnmpErrorNoAccess()
.. autoexception:: aiosnmp.exceptions.SnmpErrorWrongType()
.. autoexception:: aiosnmp.exceptions.SnmpErrorWrongLength()
.. autoexception:: aiosnmp.exceptions.SnmpErrorWrongEncoding()
.. autoexception:: aiosnmp.exceptions.SnmpErrorWrongValue()
.. autoexception:: aiosnmp.exceptions.SnmpErrorNoCreation()
.. autoexception:: aiosnmp.exceptions.SnmpErrorInconsistentValue()
.. autoexception:: aiosnmp.exceptions.SnmpErrorResourceUnavailable()
.. autoexception:: aiosnmp.exceptions.SnmpErrorCommitFailed()
.. autoexception:: aiosnmp.exceptions.SnmpErrorUndoFailed()
.. autoexception:: aiosnmp.exceptions.SnmpErrorAuthorizationError()
.. autoexception:: aiosnmp.exceptions.SnmpErrorNotWritable()
.. autoexception:: aiosnmp.exceptions.SnmpErrorInconsistentName()
