__all__ = ("SnmpV2TrapServer",)

import asyncio
from typing import Callable, Iterable, Optional, Set

from .message import SnmpV2TrapMessage
from .protocols import SnmpTrapProtocol


async def _default_handler(host: str, port: int, message: SnmpV2TrapMessage) -> None:
    print(f"Got packet from {host}:{port} - {message}")


class SnmpV2TrapServer:
    __slots__ = ("host", "port", "communities", "handler")

    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 162,
        handler: Callable = _default_handler,
        communities: Optional[Iterable[str]] = None,
    ) -> None:
        self.host: str = host
        self.port: int = port
        self.communities: Optional[Set[str]] = None
        if communities is not None:
            self.communities = set(communities)
        self.handler: Callable = handler

    async def run(self) -> None:
        loop = asyncio.get_event_loop()

        await loop.create_datagram_endpoint(
            lambda: SnmpTrapProtocol(self.communities, self.handler),
            local_addr=(self.host, self.port),
        )
