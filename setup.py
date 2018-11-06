import aiosnmp
from pathlib import Path
from setuptools import setup

readme = Path(__file__).with_name('README.md')

setup(
    name='aiosnmp',
    version=aiosnmp.__version__,
    packages=['aiosnmp'],
    url='https://github.com/hh-h/aiosnmp',
    license='MIT',
    author='Valetov Konstantin',
    author_email='forjob@thetrue.name',
    description='asyncio SNMP client',
    long_description=readme.read_text('utf-8'),
    long_description_content_type='text/markdown',
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Development Status :: 4 - Beta',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Framework :: AsyncIO',
    ],
    python_requires='>=3.6'
)
