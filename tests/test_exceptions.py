import pytest

from aiosnmp import Snmp
from aiosnmp.exceptions import (
    SnmpErrorNoAccess,
    SnmpErrorNotWritable,
    SnmpErrorWrongType,
    SnmpTimeoutError,
    SnmpUnsupportedValueType,
)


@pytest.mark.asyncio
async def test_snmp_timeout_error(host: str) -> None:
    with Snmp(host=host, port=1) as snmp:
        with pytest.raises(SnmpTimeoutError):
            await snmp.get(".1.3.6.1.2.1.1.6.0")


@pytest.mark.asyncio
async def test_snmp_no_access(host: str, port: int) -> None:
    with Snmp(host=host, port=port, community="public") as snmp:
        with pytest.raises(SnmpErrorNoAccess):
            await snmp.set([(".1.3.6.1.2.1.1.6.0", "somewhere")])


@pytest.mark.asyncio
async def test_snmp_not_writable(host: str, port: int) -> None:
    with Snmp(host=host, port=port, community="private") as snmp:
        with pytest.raises(SnmpErrorNotWritable):
            await snmp.set([(".1.3.6.1.2.1.1.1.0", "somewhere")])


@pytest.mark.asyncio
async def test_snmp_unsupported_type(host: str, port: int) -> None:
    with Snmp(host=host, port=port, community="private") as snmp:
        with pytest.raises(SnmpUnsupportedValueType):
            await snmp.set([(".1.3.6.1.2.1.1.4.0", 1.1)])


@pytest.mark.asyncio
async def test_snmp_wrong_type(host: str, port: int) -> None:
    with Snmp(host=host, port=port, community="private") as snmp:
        with pytest.raises(SnmpErrorWrongType):
            await snmp.set([(".1.3.6.1.2.1.1.5.0", 1)])
