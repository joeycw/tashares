from setuptools import setup, find_packages
import unittest


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tashares/tests', pattern='test_*.py')
    print(test_suite)
    return test_suite


setup(name='tashares',
      version='0.1.3',
      description='a TA model for China A-Shares',
      long_description='tashares is a python module to forecast China A-shares price trend in 1, 2 and 5 days.',
      long_description_content_type='text/x-rst',
      url='https://github.com/joeycw/tashares',
      author='joey.cw',
      author_email='joey.cw@protonmail.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      test_suite='setup.my_test_suite',
      tests_require=[],
      install_requires=[
          'yfinance>=0.1.70',
          'TA-Lib',
          'catboost>=0.26.1',
      ])
