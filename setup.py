try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

with open('README.md') as file:
    long_description = file.read()

setup(name='pyteaser',
      version='1.0',
      description="PyTeaser is based on the original TextTeaser project written in Scala by Mojojolo. It's completely re-written in Python.",
      long_description=long_description,
      license='MIT',
      install_requires=['Pillow', 'lxml', 'cssselect', 'jieba', 'beautifulsoup'],
      packages=find_packages(),
      py_modules=['pyteaser'],
      package_data={'goose': ['resources/images/*', 'resources/text/*']},
      test_suite='tests')
