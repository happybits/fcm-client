import os
from os import path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

NAME = 'fcm-client'
PKGNAME = 'fcmclient'

ROOTDIR = path.abspath(os.path.dirname(__file__))

with open(os.path.join(ROOTDIR, 'README.rst')) as f:
    readme = f.read()

with open(os.path.join(ROOTDIR, PKGNAME, 'VERSION')) as f:
    version = str(f.read().strip())

setup(
    name=NAME,
    version=version,
    author='John Loehrer',
    author_email='72squared@gmail.com',
    url='https://github.com/happybits/%s' % NAME,
    description='Python client for Firebase Cloud Messaging (FCM)',
    long_description=readme,
    include_package_data=True,
    packages=[PKGNAME],
    license="Apache 2.0",
    keywords='fcm push notification google cloud messaging android',
    install_requires=['requests', 'six'],
    entry_points={
        'console_scripts': ['%s = %s.cli:main' % (PKGNAME, PKGNAME)]
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules']
)
