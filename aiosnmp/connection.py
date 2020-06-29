__all__ = ("SnmpConnection",)

import asyncio
from typing import Optional, cast

from .protocols import SnmpProtocol

DEFAULT_TIMEOUT = 1
DEFAULT_RETRIES = 6


class SnmpConnection:
    __slots__ = (
        "_protocol",
        "_transport",
        "host",
        "port",
        "loop",
        "timeout",
        "retries",
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
        self.timeout: float = timeout
        self.retries: int = retries

    async def _connect(self) -> None:
        connect_future = self.loop.create_datagram_endpoint(
            lambda: SnmpProtocol(self.timeout, self.retries),
            remote_addr=(self.host, self.port),
        )
        transport, protocol = await asyncio.wait_for(
            connect_future, timeout=self.timeout
        )

        self._protocol = cast(SnmpProtocol, protocol)
        self._transport = cast(asyncio.DatagramTransport, transport)

    def close(self) -> None:
        if self._transport is not None and not self._transport.is_closing():
            self._transport.close()

        self._protocol = None
        self._transport = None
