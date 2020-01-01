import asyncio

import aiosnmp


async def main():
    with aiosnmp.Snmp(
        host="127.0.0.1",
        port=161,
        community="public",
        timeout=5,
        retries=3,
        max_repetitions=10,
    ) as snmp:
        # get
        results = await snmp.get(".1.3.6.1.2.1.1.1.0")
        for res in results:
            print(res.oid, res.value)

        # multi get
        results = await snmp.get([".1.3.6.1.2.1.1.1.0", ".1.3.6.1.2.1.1.4.0"])
        for res in results:
            print(res.oid, res.value)

        # bulk_walk
        results = await snmp.bulk_walk(".1.3.6.1.2.1.1")
        for res in results:
            print(res.oid, res.value)

        # set
        results = await snmp.set([(".1.3.6.1.2.1.1.4.0", "test")])
        for res in results:
            print(res.oid, res.value)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
