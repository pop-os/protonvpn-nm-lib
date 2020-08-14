#!/usr/bin/env python

from setuptools import setup, find_packages


long_description = '''
Contains the ProtonVPN NetworkManager Core + CLI
'''

setup(
    name='protonvpn-cli-experimental',
    version='0.0.1',
    packages=find_packages(),
    entry_points={
        "console_scripts": ["protonvpn-exp = cli:NetworkManagerPrototypeCLI"]
    },
    description='Proton Technologies Core/CLI',
    author='Proton Technologies',
    author_email='contact@protonmail.com',
    long_description=long_description,
    install_requires=[
        'proton-client', 'xdg', 'keyring',
        'pythondialog', 'PyGObject', 'Jinja2'
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
