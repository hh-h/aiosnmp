__all__ = ("SnmpConnection",)

import asyncio
from typing import Optional, cast

from .protocols import Address, SnmpProtocol

DEFAULT_TIMEOUT = 1
DEFAULT_RETRIES = 6


class SnmpConnection:
    __slots__ = (
        "_protocol",
        "_transport",
        "_peername",
        "host",
        "port",
        "loop",
        "timeout",
        "retries",
        "_closed",
    )

    def __init__(
        self,
        *,
        host: str,
        port: int = 161,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self._protocol: Optional[SnmpProtocol] = None
        self._transport: Optional[asyncio.DatagramTransport] = None
        self._peername: Optional[Address] = None
        self.timeout: float = timeout
        self.retries: int = retries
        self._closed: bool = False

    async def _connect(self) -> None:
        connect_future = self.loop.create_datagram_endpoint(
            lambda: SnmpProtocol(self.timeout, self.retries),
            remote_addr=(self.host, self.port),
        )
        transport, protocol = await asyncio.wait_for(connect_future, timeout=self.timeout)

        self._protocol = cast(SnmpProtocol, protocol)
        self._transport = cast(asyncio.DatagramTransport, transport)
        self._peername = self._transport.get_extra_info("peername", default=(self.host, self.port))

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
        self._peername = None
        self._closed = True
