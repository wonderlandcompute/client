try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="optimusClient",
      version='0.1',
      description='optimus client',
      long_description=open('README.md').read(),
      author='The optimus contributors',
      packages=["optimusClient"]
      )
