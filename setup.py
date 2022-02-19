from setuptools import setup, find_packages
import unittest


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tashares/tests', pattern='test_*.py')
    print(test_suite)
    return test_suite


setup(name='tashares',
      version='0.1.2',
      description='a TA model for China A-Shares',
      url='https://github.com/joeycw/tashares',
      author='joey.cw',
      author_email='joey.cw@protonmail.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      test_suite='setup.my_test_suite',
      tests_require=[],
      install_requires=[
          'build>=0.1',
          'setuptools',
          'yfinance>=0.1.70',
          'TA-Lib>=0.4.21',
          'catboost>=0.26.1',
      ])
