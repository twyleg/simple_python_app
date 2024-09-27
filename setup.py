# Copyright (C) 2024 twyleg
import versioneer
from pathlib import Path
from setuptools import find_packages, setup


def read(relative_filepath):
    return open(Path(__file__).parent / relative_filepath).read()


def read_long_description() -> str:
    return read("README.md")


# fmt: off
setup(
    name="simple_python_app",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Torsten Wylegala",
    author_email="mail@twyleg.de",
    description="Simple framework that provides preconfigured components that most applications need.",
    license="GPL 3.0",
    keywords="framework boilerplate logging argparse config",
    url="https://github.com/twyleg/simple_python_app",
    packages=find_packages(),
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "pyyaml~=6.0.2",
        "jsonschema~=4.20.0",
        "prompt-toolkit~=3.0.48",
    ],
    entry_points={},
)
# fmt: on
