from setuptools import setup, find_packages

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: POSIX',
    'Operating System :: Microsoft :: Windows',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3 :: Only',
]

setup(name='pyteaser',
      version='2.0',
      description="PyTeaser takes any news article and extracts a brief summary from it",
      license='MIT',
      install_requires=['goose3'],
      packages=find_packages(),
      py_modules=['pyteaser'],
      author = 'Xiao Xu',
      author_email = 'xx56@cornell.edu',
      url = 'https://github.com/xiaoxu193/PyTeaser',
      test_suite='tests')
