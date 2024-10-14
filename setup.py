# -*- coding: utf-8 -*-

from codecs import open

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

pkg = __import__('yieldcurves')

setup(
    name=pkg.__name__,
    description=pkg.__doc__,
    version=pkg.__version__,
    author=pkg.__author__,
    author_email=pkg.__email__,
    url=pkg.__url__,
    license=pkg.__license__,
    packages=find_packages(where=pkg.__name__),
    package_data={pkg.__name__: list(pkg.__data__)},
    entry_points={'console_scripts': pkg.__scripts__},
    install_requires=pkg.__dependencies__,
    dependency_links=pkg.__dependency_links__,
    long_description='\n' + open('README.rst', encoding='utf-8').read(),
    long_description_content_type='text/x-rst',
    platforms='any',
    classifiers=[
        'Development Status :: ' + pkg.__dev_status__,
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Education',
        'Topic :: Software Development',
    ],
)
