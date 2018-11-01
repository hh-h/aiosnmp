import aiosnmp
from setuptools import setup

setup(
    name='aiosnmp',
    version=aiosnmp.__version__,
    packages=['aiosnmp'],
    url='https://github.com/hh-h/aiosnmp',
    license='MIT',
    author='Valetov Konstantin',
    author_email='forjob@thetrue.name',
    description='Asynchronous library for SnmpV2 commands and a SnmpV2Trap server',
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 3 - Alpha',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Framework :: AsyncIO',
    ]
)
