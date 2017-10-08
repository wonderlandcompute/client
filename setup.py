try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="optimusClient",
      version='0.1',
      description='optimus client',
      long_description=open('README.md').read(),
      license='BSD',
      author='The optimus contributors',
      packages=["optimusClient"],
      install_requires=["numpy", "scipy"]
      )
