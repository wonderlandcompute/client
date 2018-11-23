try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="wonderlandClient",
      version='0.1.4',
      description='wonderland client',
      url="https://github.com/wonderlandcompute/client",
      author='The Skygrid contributors',
      packages=["wonderlandClient"],
      install_requires=["PyYAML", "grpcio==1.4", "protobuf", "azure-storage-file"]
      )
