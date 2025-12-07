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
    version='1.0.0',
    description='z/OS CCSID converter using fcntl for code page detection and conversion',
    long_description=read_file('README.md'),
    long_description_content_type='text/markdown',
    author='IBM',
    author_email='',
    url='https://github.com/cicsdev/cics-banking-sample-application-cbsa',
    license='Apache-2.0',
    packages=find_packages(),
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX',
        'Environment :: Console',
    ],
    keywords='zos ccsid converter codepage ebcdic ascii mainframe',
    entry_points={
        'console_scripts': [
            'zos-ccsid-converter=zos_ccsid_converter.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

# Made with Bob
