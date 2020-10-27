#!/usr/bin/env python

from setuptools import find_packages, setup

from protonvpn.constants import APP_VERSION

long_description = """
Contains ProtonVPN NetworkManager library code for Linux clients.
"""

setup(
    name="protonvpn-nm-lib",
    version=APP_VERSION,
    packages=find_packages(),
    description="ProtonVPN NetworkManager Linux library",
    author="Proton Technologies AG",
    author_email="contact@protonvpn.com",
    long_description=long_description,
    install_requires=[
        "proton-client", "pyxdg", "keyring",
        "PyGObject", "Jinja2", "distro"
    ],
    include_package_data=True,
    license="GPLv3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Security",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
