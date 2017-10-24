try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="disneylandClient",
      version='0.1',
      description='disneyland client',
      long_description=open('README.md').read(),
      author='The disneyland contributors',
      packages=["disneylandClient"],
      install_requires=["PyYAML", "grpcio==1.4"]
      )
