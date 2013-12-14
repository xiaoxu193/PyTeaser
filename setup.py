try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as file:
    long_description = file.read()

setup(name='pyteaser', version='1.0',
      description="PyTeaser is based on the original TextTeaser project written in Scala by Mojojolo. It's completely re-written in Python.",
      long_description=long_description,
      license='MIT', install_requires=['goose-extractor'], 
      py_modules=['pyteaser'])