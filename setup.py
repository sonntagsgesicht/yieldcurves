# -*- coding: utf-8 -*-

from codecs import open

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='yieldcurves',
    description='A Python library for financial yield curves.',
    version='0.2.7',
    author='sonntagsgesicht',
    author_email='sonntagsgesicht@icloud.com',
    url='https://github.com/sonntagsgesicht/yieldcurves',
    license='Apache License 2.0',
    packages=('yieldcurves',),
    install_requires=('curves', 'prettyclass', 'vectorizeit'),
    long_description='\n' + open('README.rst', encoding='utf-8').read(),
    long_description_content_type='text/x-rst',
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
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
