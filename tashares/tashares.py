import datetime
from pathlib import Path
import logging
import pandas as pd
import numpy as np
from catboost import CatBoostRanker, Pool
from tashares.cfg import config
from tashares.wrapper import wrap_stockjobs

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


class Tashares(object):
    """forecast China A-share trend in next 1,2,5 days.
        - Input: file name containing a symbol list. 
        - Output: predictive price trending of next 1,2,5 days. 

    Args:
        symbol_list (string, optional): the file name of symbol list. Default: 'list_of_interest' under the folder 'data'

    Examples:
        >>> from tashares.tashares import Tashares
        >>> tas = Tashares()
        >>> tas()
        >>> tas = Tashares(symbol_list="/absolute/path/to/list_of_ashares")
        >>> tas()
        >>> tas = Tashares("/absolute/path/to/list_of_ashares")
        >>> tas()
    """

    models_files = config['ashares']['ModelList'].split(',')
    today = datetime.date.today().strftime('%Y-%m-%d')
    start_from_date = (datetime.date.today() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')

    def __init__(self, *args, **kwargs):

        self.data_dir = Path(__file__).parent / 'data/'
        self.symbol_list = kwargs.get('symbol_list', self.data_dir /
                                      config['ashares']['SymbolsOfInterest']) if len(args) == 0 else args[0]
        self.results_file = kwargs.get('results_to_file', '')
        #self.results_file = f'{self.symbol_list}_{self.today}.csv'

    def forecast(self):

        data = wrap_stockjobs(
            symbols_file=self.symbol_list,
            update_history=True,
            forefast_only=True,
            dump_files=False,
            start_from_date=self.start_from_date,
            data_dir=self.data_dir,
        )

        result = pd.DataFrame()
        forecasting_data = data['forecasting']
        if forecasting_data.empty:
            return result

        forecasting_pool = Pool(
            data=forecasting_data.drop(
                ['symbol', 'date', 'queryid', 'shortname', 'sector', 'industry', 'tag', ], axis=1).values,
            label=forecasting_data['tag'].values,
            group_id=forecasting_data['queryid'].values
        )

        score = np.zeros(len(forecasting_data))
        cb = CatBoostRanker()
        for model_file in self.models_files:
            cb.load_model(self.data_dir / model_file, format="cbm")
            prediction = cb.predict(forecasting_pool)
            result[Path(model_file).stem] = prediction
            score += prediction
        score = score / len(self.models_files)

        forecasting_data.reset_index(drop=False, inplace=True)
        result = pd.concat([forecasting_data[['symbol', 'date']], result], axis=1)
        result['score'] = score
        result = pd.concat([result, forecasting_data['shortname']], axis=1)
        result = result.sort_values(['date', 'score'], ascending=False)
        result.reset_index(drop=True, inplace=True)
        result.insert(0, 'rank', result.index)
        print(result)

        # save prediction
        if self.results_file != '':
            result.to_csv(self.results_file, sep='\t', encoding='utf-8',
                          index=False, float_format='%.5f')
            logging.info(f" today: {self.today}")
            logging.info(f" symbol list: {self.symbol_list}")
            logging.info(f"results of {len(result)} ashares saved in {self.results_file}")

        #from sendemail import send_mail
        #send_mail([f"{self.results_file}", ])

        return result

    def __call__(self,  *args, **kwargs):
        return self.forecast()
