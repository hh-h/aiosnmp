import asyncio

import aiosnmp


async def handler(host: str, port: int, message: aiosnmp.SnmpV2TrapMessage) -> None:
    print(f"got packet from {host}:{port}")
    for d in message.data.varbinds:
        print(f"oid: {d.oid}, value: {d.value}")


async def main():
    p = aiosnmp.SnmpV2TrapServer(host='127.0.0.1', port=162, communities=("public",), handler=handler)
    await p.run()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
