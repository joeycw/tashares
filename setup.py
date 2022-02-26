from setuptools import setup, find_packages

setup(name='tashares',
      version='0.1.11',
      description='a TA model for China A-Shares',
      long_description='tashares is a python module to forecast China A-shares price trend in 1, 2 and 5 days. It is an open-source tool, that utilizes yfinance and talib to generate 155 techinical analysis features, and then leverage catboost to build three ranking models that order all stock prices of interest from trending up to trending down relatively.',
      long_description_content_type='text/x-rst',
      url='https://github.com/joeycw/tashares',
      author='joey.cw',
      author_email='joey.cw@protonmail.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      install_requires=[
          'yfinance>=0.1.70',
          'TA-Lib>=0.4.24',
          'catboost>=1.0.4',
      ])

# python -m pytest -s
