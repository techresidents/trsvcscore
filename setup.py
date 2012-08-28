import os
import setuptools

from distutils.core import setup


def find_packages():
    packages = []
    for dir,subdirs,files in os.walk('trsvcscore'):
        package = dir.replace(os.path.sep, '.')
        if '__init__.py' not in files:
            # not a package
            continue
        packages.append(package)
    return packages

setup(
    name='trsvcscore',
    version = '0.9-SNAPSHSOT',
    author = 'Tech Residents, Inc.',
    packages = find_packages(),
    license = open('LICENSE').read(),
    description = 'Tech Residents Services Core Library',
    long_description = open('README').read(),
)
