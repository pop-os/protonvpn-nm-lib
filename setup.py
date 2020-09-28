#!/usr/bin/env python

from setuptools import find_packages, setup

from lib.constants import APP_VERSION

long_description = '''
Contains the ProtonVPN NetworkManager Core + CLI
'''

setup(
    name='protonvpn-cli-experimental',
    version=APP_VERSION,
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "protonvpn-exp = lib.cli.cli:NetworkManagerPrototypeCLI"
        ]
    },
    description='Proton Technologies Core/CLI',
    author='Proton Technologies',
    author_email='contact@protonmail.com',
    long_description=long_description,
    install_requires=[
        'proton-client', 'pyxdg', 'keyring',
        'pythondialog', 'PyGObject', 'Jinja2',
        'distro'
    ],
    include_package_data=True,
    license="MIT",
    platforms="OS Independent",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Security',
    ],
)
