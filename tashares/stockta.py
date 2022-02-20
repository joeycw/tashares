# -*- coding: utf-8 -*-
from talib import abstract, get_function_groups
import pandas as pd
import logging
from tashares.stockhist import Stockhist

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


class Stockta(Stockhist):
    """Generate all TA indicators on the fly
    """

    def __init__(self, *args, **kwargs):
        super(Stockta, self).__init__(*args, **kwargs)
        self.ta = self.load_talib()

    def load_talib(self) -> pd.DataFrame:

        if self.history.empty:
            return pd.DataFrame()

        if self.update_history == True:
            assert self.ticker.ticker == self.symbol

        ta = self.history  # hard copy of history
        # drop NaN rows and date index, and lowercase column names
        ta = ta.dropna()
        ta.reset_index(drop=False, inplace=True)
        ta.columns = ta.columns.str.lower()

        data = {
            'open': ta['open'].to_numpy(dtype='double', na_value=0),
            'high': ta['high'].to_numpy(dtype='double', na_value=0),
            'low': ta['low'].to_numpy(dtype='double', na_value=0),
            'close': ta['close'].to_numpy(dtype='double', na_value=0),
            'volume': ta['volume'].to_numpy(dtype='double', na_value=0)
        }

        for group, funcs in get_function_groups().items():

            if group in ['Math Operators', 'Math Transform']:
                continue

            for func in funcs:

                ta_func = abstract.Function(func)

                # skip the following
                if ta_func.info['name'] in ['MAVP', 'MINMAXINDEX']:
                    continue

                result = ta_func(data)

                if isinstance(result, list):  # multiple outputs
                    for index, output in enumerate(ta_func.info['output_names']):
                        ta = pd.concat([ta, pd.DataFrame(result[index], columns=[
                                       ta_func.info['name'].lower() + '_' + output.lower()])], axis=1)
                else:
                    ta = pd.concat([ta, pd.DataFrame(result, columns=[ta_func.info['name'].lower()])], axis=1)

        logging.info(f" {self.symbol} : {len(ta)} samples, {len(ta.columns)} ta features")

        return ta

    def __len__(self):
        return len(self.ta)

    def __str__(self):
        return '\n'.join([super(Stockta, self).__str__(),
                          f"{str(self.__class__)} : {self.symbol} : {len(self.ta)} samples, {len(self.ta.columns)} ta features"])

    def __call__(self,  *args, **kwargs):
        super(Stockta, self).__call__(*args, **kwargs)
        self.ta = self.load_talib()
