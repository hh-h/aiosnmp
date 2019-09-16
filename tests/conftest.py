import asyncio
import os

try:
    import uvloop
except ImportError:
    HAS_UVLOOP = False
else:
    HAS_UVLOOP = True


def pytest_addoption(parser):
    parser.addoption(
        "--event-loop", action="store", default="asyncio", choices=["asyncio", "uvloop"]
    )


def pytest_configure(config):
    loop_type = config.getoption("--event-loop")
    if loop_type == "uvloop" and not HAS_UVLOOP:
        raise RuntimeError("uvloop not installed.")

    if loop_type == "uvloop":
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def pytest_generate_tests(metafunc):
    if "host" in metafunc.fixturenames:
        metafunc.parametrize("host", ["127.0.0.1"])
    if "port" in metafunc.fixturenames:
        metafunc.parametrize("port", [int(os.environ["KOSHH_AIOSNMP_161_UDP_PORT"])])
