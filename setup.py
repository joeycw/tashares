from setuptools import setup, find_packages
import unittest


def my_test_suite():
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tashares/tests', pattern='test_*.py')
    print(test_suite)
    return test_suite


setup(name='tashares',
      version='0.1.7',
      description='a TA model for China A-Shares',
      long_description='tashares is a python module to forecast China A-shares price trend in 1, 2 and 5 days. It is an open-source tool, that utilizes yfinance and talib to generate 155 techinical analysis features, and then leverage catboost to build three ranking models that order all stock prices of interest from trending up to trending down relatively.',
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
          'catboost',
      ])
