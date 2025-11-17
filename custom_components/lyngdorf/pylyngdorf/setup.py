"""Setup configuration for pylyngdorf."""

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='pylyngdorf',
    version='0.1.0',
    description='Python library for controlling Lyngdorf MP-50/MP-60 processors',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Ryan Snodgrass',
    author_email='rsnodgrass@gmail.com',
    url='https://github.com/homeassistant-projects/hass-lyngdorf',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[
        'pyserial>=3.5',
        'pyserial-asyncio>=0.6',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Home Automation',
    ],
    keywords='lyngdorf mp-50 mp-60 home-automation rs232 serial',
)
