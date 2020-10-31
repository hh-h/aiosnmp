import pytest

from aiosnmp import Snmp


@pytest.mark.asyncio
async def test_connection_close(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        await snmp.get(".1.3.6.1.2.1.1.6.0")
        assert snmp._transport
        assert snmp._protocol
        assert snmp._peername

    assert snmp._transport is None
    assert snmp._protocol is None
    assert snmp._peername is None

    with pytest.raises(Exception) as exc_info:
        await snmp.get(".1.3.6.1.2.1.1.6.0")

    assert str(exc_info.value) == "Connection is closed"
