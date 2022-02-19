# -*- coding: utf-8 -*-
import pandas as pd
from datetime import datetime
import logging
import numpy as np
from tashares.cfg import config
from tashares.stockmeta import Stockmeta

rng = np.random.default_rng(seed=0)

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


class Stockjob(Stockmeta):
    """Generate ML features

    Args:
        symbol (string, required): stock symbol. Default: ''
        forecast_days (int, optional): forecast which day in future. Default: 1, i.e. tomorrow
        max_training_date (string, optional): the stopping date for training, to control training/test split. Default: '2021-01-01'
        stack (int, optional): stacking features of multiple days. Default: 1, i.e. today's feature only
    """

    stack: int = config.getint('DEFAULT', 'FeatureStacks')
    forecast_jobs = config['DEFAULT']['ForecastJobs']
    max_training_date = config['DEFAULT']['MaxTrainingDate']
    features = pd.DataFrame()
    max_shift = 0

    def __init__(self, *args, **kwargs):
        super(Stockjob, self).__init__(*args, **kwargs)
        self.max_training_date = datetime.strptime(
            kwargs.get('max_training_date', self.max_training_date), '%Y-%m-%d')
        self.stack = kwargs.get('stack_features', self.stack)
        self.update_features()

    def update_features(self):

        self.features = self.ta  # reference only
        if self.features.empty:
            return

        # stacking
        original = self.ta[['open', 'high', 'low', 'close', 'volume']]
        for stack in range(1, self.stack+1):
            content = original.shift(stack)
            content.columns = [
                str(col) + f'_{stack}' for col in original.columns]
            self.features = pd.concat([self.features, content], axis=1)

        self._add_target()
        self._add_meta()

        logging.debug(f" {self.ticker.ticker} : {len(self.features.columns)} features")

    def _add_target(self):
        '''handcrafted a set of targets
        '''

        if self.features.empty:
            return

        for job in self.forecast_jobs.split(','):
            forecast_days = int(job)
            assert forecast_days > 0
            if forecast_days > self.max_shift:
                self.max_shift = forecast_days
            target = (self.features['adj close'].shift(-forecast_days) -
                      self.features['adj close']) / self.features['adj close'] * 100.0
            self.features = pd.concat(
                [self.features, target.to_frame().rename(columns={'adj close': f"target_{forecast_days}"})], axis=1)

    def _add_meta(self):

        if self.features.empty:
            return

        # add symbol
        if 'symbol' not in self.features.columns:
            self.features.insert(0, 'symbol', self.ticker.ticker)

        # add queryid
        self.features['tag'] = np.random.randint(0, 100, len(self.features))
        self.features['queryid'] = self.features['date'].dt.strftime(
            '%Y-%m-%d---') + self.features['tag'].apply(str)

        for key in ['shortName', 'sector', 'industry']:
            if key.lower() not in self.features.columns:
                if key in self.info:
                    result = self.info[key]
                    if not result:
                        result = 'unknown'
                else:
                    result = 'unknown'
                self.features.insert(len(self.features.columns), key.lower(),
                                     result.replace(' ', '_').lower())

    def split_jobs(self, forecast_only=False) -> dict:

        if self.features.empty:
            if forecast_only:
                return {'forecasting': pd.DataFrame()}
            else:
                return {'training': pd.DataFrame(), 'test': pd.DataFrame(), 'forecasting': pd.DataFrame()}

        # remove first 90 days for burnout
        self.features.drop(self.features.head(
            90+self.max_shift).index, inplace=True)
        self.features.reset_index(drop=True, inplace=True)

        # remove the tail of max_shift in forecasting
        forecast = self.features.tail(1)
        forecast = forecast[(forecast['date'] > self.max_training_date)]
        self.features.drop(self.features.tail(
            self.max_shift).index, inplace=True)

        has_NaN = self.features.isnull().sum().sum()
        assert has_NaN == 0, f"{self.ticker} got {has_NaN} NaN problems!"

        # split by 'max_training_date', print out training/test length
        forecast = forecast[(forecast['date'] > self.max_training_date)]
        test = self.features[(self.features['date'] > self.max_training_date)]
        training = self.features[(
            self.features['date'] <= self.max_training_date)]

        if test.empty and forecast.empty:
            logging.warning(f"{self.ticker.ticker}: no longer on listing, skip")
            if not training.empty:
                training.drop(training.index, inplace=True)
        else:
            logging.debug(
                f" {self.ticker.ticker} : {len(training)} for training, {len(test)} in test, forecasting {len(forecast)}, with columns {len(self.features.columns)}")

        if forecast_only:
            return {'forecasting': forecast}
        else:
            return {'training': training, 'test': test, 'forecasting': forecast}

    def __len__(self):
        return len(self.features)

    def __str__(self):
        return '\n'.join([super(Stockjob, self).__str__(),
                          f"{str(self.__class__)} : {self.symbol} : {len(self.features)} samples, {len(self.features.columns)} features"])

    def __call__(self,  *args, **kwargs):
        super(Stockjob, self).__call__(*args, **kwargs)
        self.update_features()
