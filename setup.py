try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="disneylandClient",
      version='0.1',
      description='disneyland client',
      url="https://github.com/skygrid/pydisneyland",
      long_description=open('README.md').read(),
      author='The Skygrid contributors',
      packages=["disneylandClient"],
      install_requires=["PyYAML", "grpcio==1.4", "protobuf"]
      )
