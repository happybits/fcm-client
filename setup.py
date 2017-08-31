try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='gcm-client',
    version='0.1.5',
    author='Sardar Yumatov',
    author_email='ja.doma@gmail.com',
    url='https://bitbucket.org/sardarnl/gcm-client',
    description='Python client for Google Cloud Messaging (GCM)',
    long_description=open('README.rst').read(),
    packages=['gcmclient'],
    license="Apache 2.0",
    keywords='gcm push notification google cloud messaging android',
    install_requires=['requests'],
    classifiers = [ 'Development Status :: 4 - Beta',
                    'Intended Audience :: Developers',
                    'License :: OSI Approved :: Apache Software License',
                    'Programming Language :: Python',
                    'Topic :: Software Development :: Libraries :: Python Modules']
)
