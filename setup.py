from setuptools import setup

setup(
    name='celeriac',
    version='0.1.dev0',
    packages=['celeriac'],
    install_requires=[
        'typing>=3.6.6; python_version<"3.5"',
    ],
)
