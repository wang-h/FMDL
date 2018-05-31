#from setuptools import find_packages, setup, Extension

from distutils.core import setup, Extension


setup(name='SuffixArray',
      version='1.4',
      description='Class for suffix arrays in characters or words',
      author='##',
      author_email='##',
      py_modules=['SuffixArray'],
      ext_modules=[Extension('_drittel', sources = ['drittel.cc','drittel_wrap.cxx'])]
 )

