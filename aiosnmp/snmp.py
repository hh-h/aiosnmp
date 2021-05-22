__all__ = ("Snmp",)

import ipaddress
from types import TracebackType
from typing import Any, List, Optional, Tuple, Type, Union

from .connection import SnmpConnection
from .exceptions import SnmpUnsupportedValueType
from .message import GetBulkRequest, GetNextRequest, GetRequest, SetRequest, SnmpMessage, SnmpVarbind, SnmpVersion


class Snmp(SnmpConnection):
    """This is class for initializing Snmp interface.

    :param str host: host where to connect to
    :param int port: port where to connect to, default: `161`
    :param SnmpVersion version: SNMP protocol version, only v2c supported now
    :param str community: SNMP community, default: `public`
    :param float timeout: timeout for one SNMP request/response, default `1`
    :param int retries: set the number of retries to attempt, default `6`
    :param int non_repeaters: sets the get_bulk max-repeaters used by bulk_walk, default `0`
    :param int max_repetitions: sets the get_bulk max-repetitions used by bulk_walk, default `10`
    :param Tuple[str,int] local_addr: tuple used to bind the socket locally, default getaddrinfo()
    :param bool validate_source_addr: verify that the packets came from the same source they were sent to
        default `True`

    Must be used with ``async with``

    .. code-block:: python

       async with aiosnmp.Snmp(host="127.0.0.1", port=161, community="public") as snmp:
           ...

    """

    __slots__ = ("version", "community", "non_repeaters", "max_repetitions")

    def __init__(
        self,
        *,
        version: SnmpVersion = SnmpVersion.v2c,
        community: str = "public",
        non_repeaters: int = 0,
        max_repetitions: int = 10,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.version: SnmpVersion = version
        self.community: str = community
        self.non_repeaters: int = non_repeaters
        self.max_repetitions: int = max_repetitions

    async def __aenter__(self) -> "Snmp":
        if not self.is_connected:
            await self._connect()

        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        self.close()
        return None

    async def _send(self, message: SnmpMessage) -> List[SnmpVarbind]:
        if not self._closed and self._protocol is None:
            await self._connect()

        if self._protocol is None:
            raise Exception("Connection is closed")

        assert self._sockaddr
        return await self._protocol._send(message, self._sockaddr)

    async def get(self, oids: Union[str, List[str]]) -> List[SnmpVarbind]:
        """The get method is used to retrieve one or more values from SNMP agent.

        :param oids: oid or list of oids, ``.1.3.6...`` or ``1.3.6...``. ``iso.3.6...`` is not supported
        :return: list of :class:`SnmpVarbind <aiosnmp.message.SnmpVarbind>`

        Example

        .. code-block:: python

           async with aiosnmp.Snmp(host="127.0.0.1", port=161, community="public") as snmp:
               for res in await snmp.get(".1.3.6.1.2.1.1.1.0"):
                   print(res.oid, res.value)

        """
        if isinstance(oids, str):
            oids = [oids]
        message = SnmpMessage(self.version, self.community, GetRequest([SnmpVarbind(oid) for oid in oids]))
        return await self._send(message)

    async def get_next(self, oids: Union[str, List[str]]) -> List[SnmpVarbind]:
        """The get_next method retrieves the value of the next OID in the tree.

        :param oids: oid or list of oids, ``.1.3.6...`` or ``1.3.6...``. ``iso.3.6...`` is not supported
        :return: list of :class:`SnmpVarbind <aiosnmp.message.SnmpVarbind>`
        """
        if isinstance(oids, str):
            oids = [oids]
        message = SnmpMessage(
            self.version,
            self.community,
            GetNextRequest([SnmpVarbind(oid) for oid in oids]),
        )
        return await self._send(message)

    async def get_bulk(
        self,
        oids: Union[str, List[str]],
        *,
        non_repeaters: Optional[int] = None,
        max_repetitions: Optional[int] = None,
    ) -> List[SnmpVarbind]:
        """The get_bulk method performs a continuous get_next operation based on the max_repetitions value.
        The non_repeaters value determines the number of variables in the
        variable list for which a simple get_next operation has to be done.

        :param oids: oid or list of oids, ``.1.3.6...`` or ``1.3.6...``. ``iso.3.6...`` is not supported
        :param non_repeaters: overwrite non_repeaters of :class:`Snmp <Snmp>`
        :param max_repetitions: overwrite max_repetitions of :class:`Snmp <Snmp>`
        :return: list of :class:`SnmpVarbind <aiosnmp.message.SnmpVarbind>`
        """
        if isinstance(oids, str):
            oids = [oids]
        nr: int = self.non_repeaters if non_repeaters is None else non_repeaters
        mr: int = self.max_repetitions if max_repetitions is None else max_repetitions
        message = SnmpMessage(
            self.version,
            self.community,
            GetBulkRequest([SnmpVarbind(oid) for oid in oids], nr, mr),
        )
        return await self._send(message)

    async def walk(self, oid: str) -> List[SnmpVarbind]:
        """The walk method uses get_next requests to query a network entity for a tree of information.

        :param oid: oid, ``.1.3.6...`` or ``1.3.6...``. ``iso.3.6...`` is not supported
        :return: list of :class:`SnmpVarbind <aiosnmp.message.SnmpVarbind>`
        """
        varbinds: List[SnmpVarbind] = []
        message = SnmpMessage(self.version, self.community, GetNextRequest([SnmpVarbind(oid)]))
        base_oid = oid if oid.startswith(".") else f".{oid}"
        vbs = await self._send(message)
        next_oid = vbs[0].oid
        if not next_oid.startswith(f"{base_oid}."):
            message = SnmpMessage(self.version, self.community, GetRequest([SnmpVarbind(base_oid)]))
            return await self._send(message)

        varbinds.append(vbs[0])
        while True:
            message = SnmpMessage(self.version, self.community, GetNextRequest([SnmpVarbind(next_oid)]))
            vbs = await self._send(message)
            next_oid = vbs[0].oid
            if not next_oid.startswith(f"{base_oid}."):
                break
            varbinds.append(vbs[0])
        return varbinds

    async def set(self, varbinds: List[Tuple[str, Union[int, str, bytes, ipaddress.IPv4Address]]]) -> List[SnmpVarbind]:
        """The set method is used to modify the value(s) of the managed object.

        :param varbinds: list of tuples[oid, int/str/bytes/ipv4]
        :return: list of :class:`SnmpVarbind <aiosnmp.message.SnmpVarbind>`

        Example

        .. code-block:: python

           async with aiosnmp.Snmp(host="127.0.0.1", port=161, community="private") as snmp:
               for res in await snmp.set([
                   (".1.3.6.1.2.1.1.1.0", 10),
                   (".1.3.6.1.2.1.1.1.1", "hello"),
               ]):
                   print(res.oid, res.value)

        """
        for varbind in varbinds:
            if not isinstance(varbind[1], (int, str, bytes, ipaddress.IPv4Address)):
                raise SnmpUnsupportedValueType(f"Only int, str, bytes and ip address supported, got {type(varbind[1])}")
        message = SnmpMessage(
            self.version,
            self.community,
            SetRequest([SnmpVarbind(oid, value) for oid, value in varbinds]),
        )
        return await self._send(message)

    async def bulk_walk(
        self,
        oid: str,
        *,
        non_repeaters: Optional[int] = None,
        max_repetitions: Optional[int] = None,
    ) -> List[SnmpVarbind]:
        """The bulk_walk method uses get_bulk requests to query a network entity efficiently for a tree of information.

        :param oid: oid, ``.1.3.6...`` or ``1.3.6...``. ``iso.3.6...`` is not supported
        :param non_repeaters: overwrite non_repeaters of :class:`Snmp <Snmp>`
        :param max_repetitions: overwrite max_repetitions of :class:`Snmp <Snmp>`
        :return: list of :class:`SnmpVarbind <aiosnmp.message.SnmpVarbind>`

        """
        nr: int = self.non_repeaters if non_repeaters is None else non_repeaters
        mr: int = self.max_repetitions if max_repetitions is None else max_repetitions
        base_oid: str = oid if oid.startswith(".") else f".{oid}"
        varbinds: List[SnmpVarbind] = []
        message = SnmpMessage(
            self.version,
            self.community,
            GetBulkRequest([SnmpVarbind(base_oid)], nr, mr),
        )
        vbs: List[SnmpVarbind] = await self._send(message)
        next_oid: str = ""
        for i, vb in enumerate(vbs):
            if not vb.oid.startswith(f"{base_oid}.") or vb.value is None:
                if i == 0:
                    message = SnmpMessage(
                        self.version,
                        self.community,
                        GetRequest([SnmpVarbind(base_oid)]),
                    )
                    return await self._send(message)
                return varbinds
            varbinds.append(vb)
            next_oid = vb.oid
        while next_oid:
            message = SnmpMessage(
                self.version,
                self.community,
                GetBulkRequest([SnmpVarbind(next_oid)], nr, mr),
            )
            vbs = await self._send(message)
            for vb in vbs:
                if not vb.oid.startswith(f"{base_oid}.") or vb.value is None:
                    next_oid = ""
                    break
                varbinds.append(vb)
                next_oid = vb.oid
        return varbinds
