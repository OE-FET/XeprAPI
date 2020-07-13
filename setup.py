# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


def get_metadata(relpath, varname):
    """Read metadata info from a file without importing it."""
    from os.path import dirname, join

    if "__file__" not in globals():
        root = "."
    else:
        root = dirname(__file__)

    for line in open(join(root, relpath), "rb"):
        line = line.decode("cp437")
        if varname in line:
            if '"' in line:
                return line.split('"')[1]
            elif "'" in line:
                return line.split("'")[1]


setup(
    name="XeprAPI",
    version=get_metadata("XeprAPI/__init__.py", "__version__"),
    description="Python interface for for Bruker Xepr.",
    author=get_metadata("XeprAPI/__init__.py", "__author__"),
    author_email="ss2151@cam.ac.uk",
    license="MIT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    package_data={
            "XeprAPI": [
                    "*.so",
                    "*.py",
            ],
    },
    install_requires=[
                "numpy>=1.2.1",
    ],
    python_requires='>=3.6',
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)
