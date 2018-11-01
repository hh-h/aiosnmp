import os


def pytest_generate_tests(metafunc):
    if "host" in metafunc.fixturenames:
        metafunc.parametrize("host", ["127.0.0.1"])
    if "port" in metafunc.fixturenames:
        print(1)
        metafunc.parametrize("port", [int(os.environ["KOSHH/AIOSNMP_161_UDP"])])
