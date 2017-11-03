try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup



setup(name='pyteaser',
      version='1.0',
      description="PyTeaser takes any news article and extract a brief summary from it",
      license='MIT',
      install_requires=['Pillow', 'lxml', 'cssselect', 'jieba', 'bs4'],
      packages=find_packages(),
      py_modules=['pyteaser'],
      package_data={'goose': ['resources/images/*', 'resources/text/*']},
      author = 'Xiao Xu',
      author_email = 'xx56@cornell.edu',
      url = 'https://github.com/xiaoxu193/PyTeaser',
      test_suite='tests')
