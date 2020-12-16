from os import path
from setuptools import setup
from setuptools import find_packages

try:
    pkg_name = 'jinad'
    libinfo_py = path.join(pkg_name, '__init__.py')
    libinfo_content = open(libinfo_py, 'r', encoding='utf8').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][0]
    exec(version_line)  # gives __version__
except ModuleNotFoundError:
    __version__ = '0.0.0'

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

try:
    with open('README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

setup(
    name=pkg_name,
    version=__version__,
    description='Jinad is the daemon tool for running Jina on remote machines. Jina is the cloud-native neural search solution powered by the state-of-the-art AI and deep learning',
    packages=find_packages(),
    author='Jina Dev Team',
    author_email='dev-team@jina.ai',
    license='Apache 2.0',
    url='https://opensource.jina.ai',
    download_url='https://github.com/jina-ai/jinad/tags',
    python_requires='>=3.7',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    setup_requires=[
        'setuptools>=18.0',
    ],
    install_requires=requirements,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Unix Shell',
        'Environment :: Console',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Topic :: Scientific/Engineering :: Image Recognition',
        'Topic :: Multimedia :: Video',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='jina cloud-native neural-search query search index elastic neural-network encoding '
             'embedding serving docker container image video audio deep-learning',
)
