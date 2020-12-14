from setuptools import setup

try:
    from jinad.config import FastAPIConfig
    api = FastAPIConfig()
    __version__ = api.VERSION
except ModuleNotFoundError:
    __version__ = '0.0.0'

try:
    with open('README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

setup(
    name='jinad',
    version=__version__,
    description='Jinad is the daemon tool for running Jina on remote machines. Jina is the cloud-native neural search solution powered by the state-of-the-art AI and deep learning',
    packages=['jinad', 'jinad.api', 'jinad.api.endpoints', 'jinad.models', 'tests', 'tests.unit', 'tests.unit.api',
              'tests.unit.api.endpoints', 'tests.unit.models', 'tests.integration', 'tests.integration.api',
              'tests.integration.api.endpoints'],
    author='Jina Dev Team',
    author_email='dev-team@jina.ai',
    license='Apache 2.0',
    url='https://opensource.jina.ai',
    download_url='https://github.com/jina-ai/jinad/tags',
    python_requires='>=3.6',
    long_description=_long_description,
    long_description_content_type='text/markdown',
    setup_requires=[
        'setuptools>=18.0',
    ],
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
