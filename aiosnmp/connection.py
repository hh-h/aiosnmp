__all__ = ("SnmpConnection",)

import asyncio
from typing import Optional, Tuple, cast

from .protocols import Address, SnmpProtocol

DEFAULT_TIMEOUT = 1
DEFAULT_RETRIES = 6


class SnmpConnection:
    __slots__ = (
        "_protocol",
        "_transport",
        "_sockaddr",
        "host",
        "port",
        "local_addr",
        "loop",
        "timeout",
        "retries",
        "_closed",
        "validate_source_addr",
    )

    def __init__(
        self,
        *,
        host: str,
        port: int = 161,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        local_addr: Optional[Tuple[str, int]] = None,
        validate_source_addr: bool = True,
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._protocol: Optional[SnmpProtocol] = None
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._sockaddr: Optional[Address] = None
        self.timeout: float = timeout
        self.retries: int = retries
        self._closed: bool = False
        self.local_addr: Optional[Tuple[str, int]] = local_addr
        self.validate_source_addr: bool = validate_source_addr

    async def _connect(self) -> None:
        gai = await self.loop.getaddrinfo(self.host, self.port)
        address_family, *_, self._sockaddr = gai[0]
        connect_future = self.loop.create_datagram_endpoint(
            lambda: SnmpProtocol(self.timeout, self.retries, self.validate_source_addr),
            local_addr=self.local_addr,
            family=address_family,
        )
        transport, protocol = await asyncio.wait_for(connect_future, timeout=self.timeout)

        self._protocol = cast(SnmpProtocol, protocol)
        self._transport = cast(asyncio.DatagramTransport, transport)

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def is_connected(self) -> bool:
        return bool(self._protocol is not None and self._protocol.is_connected)

    def close(self) -> None:
        if self._transport is not None and not self._transport.is_closing():
            self._transport.close()

        self._protocol = None
        self._transport = None
        self._sockaddr = None
        self._closed = True
