from setuptools import setup

try:
    with open('README.md', encoding='utf8') as fp:
        _long_description = fp.read()
except FileNotFoundError:
    _long_description = ''

setup(
    name='jinad',
    version='0.0.1',
    packages=['jinad', 'jinad.api', 'jinad.api.endpoints', 'jinad.models', 'tests', 'tests.unit', 'tests.unit.api',
              'tests.unit.api.endpoints', 'tests.unit.models', 'tests.integration', 'tests.integration.api',
              'tests.integration.api.endpoints'],
    url='https://opensource.jina.ai',
    license='Apache 2.0',
    author='Jina Dev Team',
    author_email='dev-team@jina.ai',
    description='Jinad is the daemon tool for running Jina on remote machines. Jina is the cloud-native neural search solution powered by the state-of-the-art AI and deep learning',
    python_requires='>=3.6',
    long_description=_long_description,
    long_description_content_type='text/markdown',
)
