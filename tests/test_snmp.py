import ipaddress
from typing import Any, List, Tuple, Union

import pytest

from aiosnmp import Number, Snmp


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("oid", "value"),
    (
        (".1.3.6.1.4.1.8072.2.255.1.0", b"Life, the Universe, and Everything"),
        (".1.3.6.1.4.1.8072.2.255.2.1.2.1", 42),
        (".1.3.6.1.4.1.8072.2.255.2.1.3.1", ".1.3.6.1.4.1.8072.2.255.99"),
        (".1.3.6.1.4.1.8072.2.255.3.0", 363136200),
        (".1.3.6.1.4.1.8072.2.255.4.0", ipaddress.IPv4Address("127.0.0.1")),
        (".1.3.6.1.4.1.8072.2.255.5.0", 42),
        (".1.3.6.1.4.1.8072.2.255.6.0", 42),
        ([".1.3.6.1.4.1.8072.2.255.1.0"], b"Life, the Universe, and Everything"),
        ([".1.3.6.1.4.1.8072.2.255.2.1.2.1"], 42),
        ([".1.3.6.1.4.1.8072.2.255.2.1.3.1"], ".1.3.6.1.4.1.8072.2.255.99"),
        ([".1.3.6.1.4.1.8072.2.255.3.0"], 363136200),
        ([".1.3.6.1.4.1.8072.2.255.4.0"], ipaddress.IPv4Address("127.0.0.1")),
        ([".1.3.6.1.4.1.8072.2.255.5.0"], 42),
        ([".1.3.6.1.4.1.8072.2.255.6.0"], 42),
    ),
)
async def test_snmp_types(host: str, port: int, oid: Union[str, List[str]], value: Any) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.get(oid)
        assert len(results) == 1
        res = results[0]
        assert res.oid == oid if isinstance(oid, str) else oid[0]
        assert res.value == value


@pytest.mark.asyncio
async def test_snmp_get_next(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.get_next(".1.3.6.1.2.1.1")
        assert len(results) == 1
        res = results[0]
        assert res.oid.startswith(".1.3.6.1.2.1.1")


@pytest.mark.asyncio
@pytest.mark.parametrize("max_repetitions", (1, 2, 5, 10, 25))
async def test_snmp_get_bulk(host: str, port: int, max_repetitions: int) -> None:
    async with Snmp(host=host, port=port, max_repetitions=max_repetitions) as snmp:
        results = await snmp.get_bulk(".1.3.6.1.2.1.1")
        assert len(results) == max_repetitions
        for res in results:
            assert res.oid.startswith(".1.3.6.1.2.1.1")


@pytest.mark.asyncio
@pytest.mark.parametrize("max_repetitions", (1, 2, 5, 10, 25))
async def test_snmp_bulk_walk(host: str, port: int, max_repetitions: int) -> None:
    async with Snmp(host=host, port=port, timeout=3, max_repetitions=max_repetitions) as snmp:
        results = await snmp.bulk_walk(".1.3.6.1.2.1.1.9")
        assert len(results) == 30
        for res in results:
            assert res.oid.startswith(".1.3.6.1.2.1.1.9")


@pytest.mark.asyncio
async def test_snmp_walk(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.walk(".1.3.6.1.2.1.1.9.1.4")
        assert len(results) == 10
        for res in results:
            assert res.oid.startswith(".1.3.6.1.2.1.1.9.1.4")


@pytest.mark.asyncio
async def test_snmp_get_instead_of_walk(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.walk(".1.3.6.1.2.1.1.6.0")
        assert len(results) == 1
        res = results[0]
        assert res.oid == ".1.3.6.1.2.1.1.6.0"


@pytest.mark.asyncio
async def test_snmp_get_instead_of_bulk_walk(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.bulk_walk(".1.3.6.1.2.1.1.6.0")
        assert len(results) == 1
        res = results[0]
        assert res.oid == ".1.3.6.1.2.1.1.6.0"


@pytest.mark.asyncio
async def test_snmp_bulk_walk_end_of_mibs_from_the_start(host: str, port: int) -> None:
    async with Snmp(host=host, port=port, max_repetitions=15) as snmp:
        results = await snmp.bulk_walk(".1.3.6.1.6.3.16.1.5.2.1.6")
        assert len(results) == 6
        for res in results:
            assert res.oid.startswith(".1.3.6.1.6.3.16.1.5.2.1.6")


@pytest.mark.asyncio
async def test_snmp_bulk_walk_end_of_mibs_after_some_requests(host: str, port: int) -> None:
    async with Snmp(host=host, port=port, max_repetitions=15) as snmp:
        results = await snmp.bulk_walk(".1.3.6.1.6.3.16.1.5.2.1")
        assert len(results) == 24
        for res in results:
            assert res.oid.startswith(".1.3.6.1.6.3.16.1.5.2.1")


@pytest.mark.asyncio
async def test_snmp_non_existing_oid(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.get(".1.3.6.1.2.1.1.6.0.12312")
        assert len(results) == 1
        res = results[0]
        assert res.oid == ".1.3.6.1.2.1.1.6.0.12312"
        assert res.value is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("oids", "values"),
    (
        ([".1.3.6.1.2.1.1.6.0", ".1.3.6.1.2.1.1.4.0"], (b"unknown", b"root@unknown")),
        ([".1.3.6.1.2.1.1.6.0.1", ".1.3.6.1.2.1.1.4.0"], (None, b"root@unknown")),
        ([".1.3.6.1.2.1.1.6.0", ".1.3.6.1.2.1.1.4.0.1"], (b"unknown", None)),
        ([".1.3.6.1.2.1.1.6.0.1", ".1.3.6.1.2.1.1.4.0.2"], (None, None)),
    ),
)
@pytest.mark.asyncio
async def test_snmp_multiple_oids(host: str, port: int, oids: List[str], values: List[Any]) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.get(oids)
        assert len(results) == len(oids)
        for res, oid, value in zip(results, oids, values):
            assert res.oid == oid
            assert res.value == value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "varbinds",
    (
        [(".1.3.6.1.4.1.8072.2.255.1.0", b"test_bytes")],
        [(".1.3.6.1.4.1.8072.2.255.1.0", "test_str")],
        [(".1.3.6.1.4.1.8072.2.255.2.1.2.1", 42)],
        [(".1.3.6.1.4.1.8072.2.255.2.1.3.1", ".1.3.6.1.4.1.8072.2.255.99")],
        [(".1.3.6.1.4.1.8072.2.255.3.0", 363136200)],
        [(".1.3.6.1.4.1.8072.2.255.4.0", ipaddress.IPv4Address("127.0.0.1"))],
        [(".1.3.6.1.4.1.8072.2.255.5.0", 42)],
        [(".1.3.6.1.4.1.8072.2.255.6.0", 42)],
        [
            (".1.3.6.1.4.1.8072.2.255.1.0", b"test_bytes"),
            (".1.3.6.1.4.1.8072.2.255.6.0", 42),
        ],
        [(".1.3.6.1.4.1.8072.2.255.6.0", 42, Number.Gauge32)],
        [
            (".1.3.6.1.4.1.8072.2.255.1.0", b"test_bytes"),
            (".1.3.6.1.4.1.8072.2.255.5.0", 42),
            (".1.3.6.1.4.1.8072.2.255.6.0", 42, Number.Counter32),
        ],
    ),
)
async def test_snmp_set(host: str, port: int, varbinds: List[Tuple[str, Union[int, str, bytes]]]) -> None:
    async with Snmp(host=host, port=port, timeout=3, community="private") as snmp:
        results = await snmp.set(varbinds)
        assert len(results) == len(varbinds)
        for varbind, res in zip(varbinds, results):
            assert res.oid == varbind[0]
            assert res.value == varbind[1] if not isinstance(varbind[1], str) else varbind[1].encode()


@pytest.mark.asyncio
async def test_snmp_get_no_leading_dot(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.get("1.3.6.1.4.1.8072.2.255.2.1.2.1")
        assert len(results) == 1
        res = results[0]
        assert res.oid == ".1.3.6.1.4.1.8072.2.255.2.1.2.1"
        assert res.value == 42

        results = await snmp.get(["1.3.6.1.4.1.8072.2.255.2.1.2.1"])
        assert len(results) == 1
        res = results[0]
        assert res.oid == ".1.3.6.1.4.1.8072.2.255.2.1.2.1"
        assert res.value == 42


@pytest.mark.asyncio
async def test_snmp_get_next_no_leading_dot(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.get_next("1.3.6.1.2.1.1")
        assert len(results) == 1
        res = results[0]
        assert res.oid.startswith(".1.3.6.1.2.1.1")
        assert res.value is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("max_repetitions", (1, 2, 5, 10, 25))
async def test_snmp_get_bulk_no_leading_dot(host: str, port: int, max_repetitions: int) -> None:
    async with Snmp(host=host, port=port, max_repetitions=max_repetitions) as snmp:
        results = await snmp.get_bulk("1.3.6.1.2.1.1")
        assert len(results) == max_repetitions
        for res in results:
            assert res.oid.startswith(".1.3.6.1.2.1.1")


@pytest.mark.asyncio
@pytest.mark.parametrize("max_repetitions", (1, 2, 5, 10, 25))
async def test_snmp_bulk_walk_no_leading_dot(host: str, port: int, max_repetitions: int) -> None:
    async with Snmp(host=host, port=port, timeout=3, max_repetitions=max_repetitions) as snmp:
        results = await snmp.bulk_walk("1.3.6.1.2.1.1.9")
        assert len(results) == 30
        for res in results:
            assert res.oid.startswith(".1.3.6.1.2.1.1.9")


@pytest.mark.asyncio
async def test_snmp_walk_no_leading_dot(host: str, port: int) -> None:
    async with Snmp(host=host, port=port) as snmp:
        results = await snmp.walk("1.3.6.1.2.1.1.9.1.4")
        assert len(results) == 10
        for res in results:
            assert res.oid.startswith(".1.3.6.1.2.1.1.9.1.4")


@pytest.mark.asyncio
async def test_snmp_set_no_leading_dot(host: str, port: int) -> None:
    async with Snmp(host=host, port=port, timeout=3, community="private") as snmp:
        results = await snmp.set([("1.3.6.1.4.1.8072.2.255.2.1.2.1", 42)])
        assert len(results) == 1
        assert results[0].oid == ".1.3.6.1.4.1.8072.2.255.2.1.2.1"
        assert results[0].value == 42


@pytest.mark.asyncio
async def test_snmp_disable_validation_source_addr(host: str, port: int) -> None:
    async with Snmp(host=host, port=port, validate_source_addr=False) as snmp:
        results = await snmp.get(".1.3.6.1.2.1.1.6.0.12312")
        assert len(results) == 1
