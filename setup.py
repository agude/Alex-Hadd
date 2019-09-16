#!/usr/bin/env python3

import re
from setuptools import setup


# Get the version from the main script
version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open("ahadd/ahadd.py").read(),
    re.M,
).group(1)


# Try to import pypandoc to convert the readme, otherwise ignore it
try:
    import pypandoc

    long_description = pypandoc.convert("README.md", "rst")
except ImportError:
    long_description = ""


# Configure the package
setup(
    name="alex hadd",
    version=version,
    description="Script for adding ROOT histograms in parallel",
    long_description=long_description,
    author="Alexander Gude",
    author_email="alex.public.account@gmail.com",
    url="https://github.com/agude/Alex-Hadd",
    license="MIT",
    platforms=["any"],
    packages=["ahadd"],
    entry_points={
        "console_scripts": [
            "ahadd = ahadd.ahadd:main"
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Utilities",
    ],
    keywords=[
        "hadd",
        "ROOT",
        "ROOT histogram",
        "CERN ROOT",
    ],
    setup_requires=[
        "pypandoc",
        "pytest-runner",
    ],
    tests_require=["pytest"],
    python_requires=">=3.6, <4",
)
