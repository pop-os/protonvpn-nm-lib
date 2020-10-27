#!/usr/bin/env python

from setuptools import find_packages, setup

from protonvpn.constants import APP_VERSION

long_description = """
Contains the ProtonVPN NetworkManager Core + CLI
"""

setup(
    name="protonvpn-cli",
    version=APP_VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "protonvpn-cli = protonvpn.cli.cli:NetworkManagerPrototypeCLI"
        ]
    },
    description="Proton Technologies Core/CLI",
    author="Proton Technologies AG",
    author_email="contact@protonmail.com",
    long_description=long_description,
    install_requires=[
        "proton-client", "pyxdg", "keyring",
        "pythondialog", "PyGObject", "Jinja2",
        "distro"
    ],
    include_package_data=True,
    license="GPLv3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Security",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
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
