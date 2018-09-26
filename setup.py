try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="wonderlandClient",
      version='0.1.4',
      description='wonderland client',
      url="https://github.com/wonderlandcompute/client",
      long_description=open('README.md').read(),
      author='The Skygrid contributors',
      packages=["wonderlandClient"],
      install_requires=["PyYAML", "grpcio==1.4", "protobuf", "azure"]
      )
