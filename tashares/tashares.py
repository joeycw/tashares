import datetime
from pathlib import Path
import logging
import pandas as pd
import numpy as np
from catboost import CatBoostRanker, Pool
from tashares.cfg import config
from tashares.wrapper import wrap_stockjobs, load_data, upgrade_targets, compute_metrics

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


class Tashares(object):
    """forecast China A-share trend in next 1,2,5 days.
        - Input: file name containing a symbol list.
        - Output: predictive price trending of next 1,2,5 days.

    Args:
        symbol_list (string, optional): the file name of symbol list. Default: 'list_of_interest' under the folder 'data'
        task_type (string, optional): China 'ashares' or US 'stocks' according to section names in cfg.ini. Default: 'ashares'
        results_to_file (string, optional): the file to save results. Default: '' don't dump results

    Examples:
        >>> from tashares.tashares import Tashares
        >>> tas = Tashares()
        >>> tas()
        >>> tas = Tashares(symbol_list="/absolute/path/to/list_of_ashares")
        >>> tas()
        >>> tas = Tashares("/absolute/path/to/list_of_ashares")
        >>> tas()
    """

    def __init__(self, *args, **kwargs):

        self.task_type = kwargs.get('task_type', 'ashares')
        self.results_file = kwargs.get('results_to_file', '')

        self.data_dir = Path(__file__).parent / 'data/' / self.task_type
        self.models_files = config[self.task_type]['ModelList'].split(',')
        self.symbol_list = kwargs.get('symbol_list', self.data_dir /
                                      config[self.task_type]['SymbolsOfInterest']) if len(args) == 0 else args[0]

        # test purpose
        self.dump_data_to = kwargs.get('dump_data_to', self.data_dir / 'forecast.data')
        self.load_data_from = kwargs.get('load_data_from', '')
        if self.load_data_from != '':
            self.forecasting_data = load_data(self.load_data_from, queryid='date')
            self.forecasting_data = upgrade_targets(self.forecasting_data)
        else:
            self.forecasting_data = pd.DataFrame()

    def dump_forecast_data(self):

        if self.forecasting_data.empty == False:
            self.forecasting_data.to_csv(Path(self.dump_data_to), sep='\t', encoding='utf-8',
                                         index=False, float_format='%.6f', header=True, )

    def forecast(self):

        if self.forecasting_data.empty:

            data = wrap_stockjobs(
                symbols_file=self.symbol_list,
                data_dir=self.data_dir,
                update_history=True,
                forefast_only=True,
                dump_files=False,
            )
            self.forecasting_data = data['forecasting']

        forecasting_data = self.forecasting_data

        if self.task_type == 'ashares':
            drop_list = ['symbol', 'date', 'queryid', 'sector', 'industry', 'shortname', 'tag', ] + \
                [c for c in forecasting_data.columns if c.lower()[:6] == 'target' or c.lower()[:6] == '_label']
        else:
            drop_list = ['symbol', 'date', 'queryid', 'sector', 'industry', 'shortname', 'tag', 'adj close'] + \
                [c for c in forecasting_data.columns if c.lower()[:6] == 'target' or c.lower()[:6] == '_label']

        forecasting_pool = Pool(
            data=forecasting_data.drop(drop_list, axis=1).values,
            label=forecasting_data['tag'].values,
            group_id=forecasting_data['queryid'].values
        )

        result = pd.DataFrame()
        score = np.zeros(len(forecasting_data))
        cb = CatBoostRanker()
        for model_file in self.models_files:
            cb.load_model(self.data_dir / model_file, format="cbm")
            prediction = cb.predict(forecasting_pool)
            result[Path(model_file).stem] = prediction
            score += prediction
            # run compute metrics for test case
            if self.load_data_from != '':
                return compute_metrics(forecasting_data, prediction)
        score = score / len(self.models_files)

        #forecasting_data.reset_index(drop=False, inplace=True)
        result = pd.concat([forecasting_data[['symbol', 'date']], result], axis=1)
        result['score'] = score
        result = pd.concat([result, forecasting_data['shortname']], axis=1)
        result = pd.concat([result, forecasting_data['sector']], axis=1)
        result = result.sort_values(['date', 'score'], ascending=False)
        result.reset_index(drop=True, inplace=True)
        result.insert(0, 'rank', result.index)

        # save prediction
        if self.results_file != '':
            result.to_csv(self.results_file, sep='\t', encoding='utf-8',
                          index=False, float_format='%.5f')
            logging.info(f" today: {datetime.date.today().strftime('%Y-%m-%d')}")
            logging.info(f" symbol list: {self.symbol_list}")
            logging.info(f"results of {len(result)} ashares saved in {self.results_file}")

        # from sendemail import send_mail
        # send_mail([f"{self.results_file}", ])

        return result

    def __call__(self,  *args, **kwargs):
        return self.forecast()
