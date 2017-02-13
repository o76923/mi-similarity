from distutils.core import setup

setup(
    name='theorizeit',
    version='0.5',
    packages=[''],
    package_dir={'': 'py'},
    url='',
    license='',
    author='James E. Endicott',
    author_email='james.endicott@colorado.edu',
    description='', requires=['uvloop', 'asyncpg', 'aioredis']
)
