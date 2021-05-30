import pathlib
import re

from setuptools import setup
from setuptools_rust import Binding, RustExtension

BASE = pathlib.Path(__file__).parent

readme_file = BASE / "README.rst"
version_file = BASE / "aiosnmp" / "__init__.py"

version = re.findall(r'^__version__ = "(.+?)"$', version_file.read_text("utf-8"), re.M)[0]

setup(
    name="aiosnmp",
    version=version,
    packages=["aiosnmp"],
    url="https://github.com/hh-h/aiosnmp",
    license="MIT",
    author="Valetov Konstantin",
    author_email="forjob@thetrue.name",
    description="asyncio SNMP client",
    long_description=readme_file.read_text("utf-8"),
    long_description_content_type="text/x-rst",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Rust",
        "Development Status :: 4 - Beta",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.7",
    rust_extensions=[RustExtension("aiosnmp.asn1_rust", binding=Binding.PyO3)],
    zip_safe=False,
)
