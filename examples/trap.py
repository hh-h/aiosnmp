import asyncio

import aiosnmp


async def handler(host: str, port: int, message: aiosnmp.SnmpV2TrapMessage) -> None:
    print(f"got packet from {host}:{port}")
    for d in message.data.varbinds:
        print(f"oid: {d.oid}, value: {d.value}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    trap_server = aiosnmp.SnmpV2TrapServer(host="127.0.0.1", port=162, communities=("public",), handler=handler)
    transport, _ = loop.run_until_complete(trap_server.run())

    try:
        print(f"running server on {trap_server.host}:{trap_server.port}")
        loop.run_forever()
    finally:
        transport.close()
