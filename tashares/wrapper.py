from concurrent import futures
import multiprocessing
import logging
from pathlib import Path
import pandas as pd
from catboost.utils import eval_metric
from tashares.cfg import config
from tashares.stockjob import Stockjob

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')

MAX_WORKERS = max(multiprocessing.cpu_count()-1, 1)

wrapper_parameters = {
    'data_dir': '',
    'forecast_only': False,
    'dump_files': False,
    'start_from_date': '2015-01-01',
    'max_training_date': '2020-01-01',
    'update_history': False,
}


def get_stockjob(symbol):
    return Stockjob(symbol=symbol.strip(),
                    data_dir=wrapper_parameters['data_dir'],
                    update_history=wrapper_parameters['update_history'],
                    start_from_date=wrapper_parameters['start_from_date'],
                    dump_files=wrapper_parameters['dump_files'],
                    ).split_jobs(forecast_only=wrapper_parameters['forecast_only'])


def wrap_stockjobs(symbols_file: str, **kwargs):
    '''generate training/test/forecasting data files
        - Input: a file of stock symbol list.
        - Output: a dictionary of three pandas dataframes for training/test/forecasting data respectively.
    Args:
        symbols_file (string, required): the file of stock symbol list.
        data_dir (string, required): the directory for data files which needs exist already.
        forefast_only (bool, optional): only generate forecasting data if 'forefast_only=True'. Default: False
        dump_files (bool, optional): save data into files if 'force_dump=True' and data_dir exists. Default: False
        max_training_date (string, optional): the stopping date for training, to control training/test split. Default: '2021-01-01'
        stack_features (int, optional): the number of days for stacking in feature engineering. Default: 1
        update_history (bool, optional): download the latest history if 'update=True', otherwise use history saved under data_dir. Default: False
        forecast_days (int, optional): the day in future for forecasting. Default: 1, i.e. predict tomorrow's
    '''
    wrapper_parameters.update(kwargs)

    logging.debug(f"wrapper_parameters {wrapper_parameters}")

    data = {}

    with open(symbols_file, encoding='utf8') as f:
        job_list = (symbol.strip() for symbol in f)
        with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            to_do: list[futures.Future] = []
            for symbol in job_list:
                future = executor.submit(get_stockjob, symbol)
                to_do.append(future)
                logging.debug(f'Scheduled for {symbol}: {future}')

            for count, future in enumerate(futures.as_completed(to_do), 1):
                res: dict = future.result()
                for key, value in res.items():
                    if key not in data.keys():
                        data[key] = pd.DataFrame()
                    if not value.empty:
                        data[key] = pd.concat([data[key], value], axis=0)

    logging.debug(f" {count} futures as completed")

    def sort_queryid(df):
        if not df.empty:
            df = df.sort_values(['date', 'queryid'])
            df.reset_index(drop=True, inplace=True)
        return df

    for key in data.keys():
        data[key] = sort_queryid(data[key])
        logging.debug(f" {key} samples {len(data[key])}")

    return data


def dump_stockjobs(task_type, data_dir: Path, **data):

    if not data_dir.is_dir():
        logging.warning(f"{data_dir} doesn't exist")
    else:
        for key in data.keys():
            filename = data_dir / f"{key}_{task_type}.csv"
            if filename.exists():
                logging.warning(f"{filename} already exists, skip dumping")
                continue
            data[key].to_csv(filename, sep='\t', encoding='utf-8', index=False, float_format='%.4f',
                             header=not filename.exists())
            logging.info(f"{key} {len(data[key])} samples saved in {filename}")


def dump_datafiles(symbol_list='', data_dir='', task_type='ashares'):
    '''save training/test/forecasting data into files
        - Input: a file of stock symbol list.
        - Output: three csv files for training/test/forecasting data respectively under the folder data_dir.
    Args:
        symbol_list (string, optional): the file of stock symbol list. Default: 'SymbolList' in cfg.ini
        data_dir (string, optional): the directory to save files. Default: current working directory
    '''

    if data_dir == '':
        data_dir = Path.cwd()
    if symbol_list == '':
        symbol_list = Path(__file__).parent / 'data/ashares/' / config['ashares']['SymbolList']

    data = wrap_stockjobs(
        symbol_list,
        data_dir=data_dir,
        start_from_date=config['DEFAULT']['StartFromDate'],
        max_training_date=config['DEFAULT']['MaxTrainingDate'],
        forefast_only=False,
        dump_files=False,
        update_history=True,)
    dump_stockjobs(task_type, Path(data_dir), **data,)


def load_data(data_file, queryid='date'):
    try:
        tp = pd.read_csv(data_file, sep='\t', iterator=True, chunksize=10000, dtype={
            "date": "category", "symbol": "category", "queryid": "category"})
        data = pd.concat(tp, ignore_index=True)
        data = data.sort_values([queryid, 'queryid'])
        data.reset_index(drop=True, inplace=True)
        # encode categorical features
        cols = ['date', 'symbol', 'queryid', 'sector', 'industry', 'shortname']
        for col in cols:
            data[col] = data[col].astype("category").cat.codes + 1
        logging.info(f"{data_file} loaded")
    except:
        logging.critical(f"loading {data_file} failed")
        data = pd.DataFrame()
    return data


def upgrade_targets(data, forecast_job='1', threshold=10):

    if data.empty:
        return data

    targets = [c for c in data.columns if c.lower()[:6] == 'target']
    assert len(targets) > 0
    data['target'] = data[f"target_{forecast_job}"]
    data['binary_label'] = data['target'].transform(
        lambda x: 1 if x >= 0 else 0)
    return data


def compute_metrics(labels, y_pred, queryid='date'):

    result = [eval_metric(labels['binary_label'], y_pred, 'PrecisionAt:top=5', group_id=labels[queryid]),
              eval_metric(labels['binary_label'], y_pred, 'PrecisionAt:top=10', group_id=labels[queryid]),
              eval_metric(labels['binary_label'], y_pred, 'PrecisionAt:top=20', group_id=labels[queryid]),
              eval_metric(labels['binary_label'], y_pred, 'PrecisionAt:top=50', group_id=labels[queryid]), ]
    return result


if __name__ == '__main__':
    dump_datafiles()
