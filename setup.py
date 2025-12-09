#!/usr/bin/env python3
"""
Setup script for zos-ccsid-converter package.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename), encoding='utf-8') as f:
        return f.read()

setup(
    name='zos-ccsid-converter',
    version='0.1.8',
    description='z/OS CCSID converter using fcntl for code page detection and conversion',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='Mike Fulton',
    author_email='',
    url='https://github.com/MikeFultonDev/zos_ccsid_converter',
    packages=find_packages(),
    python_requires='>=3.12',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Operating System :: Other OS',
        'Environment :: Console',
    ],
    keywords='zos z/OS ccsid converter codepage ebcdic ascii mainframe',
    entry_points={
        'console_scripts': [
            'zos-ccsid-converter=zos_ccsid_converter.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

# Made with Bob
