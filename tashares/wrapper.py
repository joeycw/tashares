from concurrent import futures
import multiprocessing
import logging
from pathlib import Path
import pandas as pd
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


def dump_stockjobs(jobname, data_dir: Path, **data):

    if not data_dir.is_dir():
        logging.warning(f"{data_dir} doesn't exist")
    else:
        for key in data.keys():
            filename = data_dir / f"{key}_{jobname}.csv"
            if filename.exists():
                logging.warning(f"{filename} already exists, skip dumping")
                continue
            data[key].to_csv(filename, sep='\t', encoding='utf-8', index=False, float_format='%.4f',
                             header=not filename.exists())
            logging.info(f"{key} {len(data[key])} samples saved in {filename}")


def dump_datafiles(symbol_list='', data_dir=''):
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
        symbol_list = Path(__file__).parent / 'data/' / config['ashares']['SymbolList']
    for section in config.sections():
        data = wrap_stockjobs(
            symbol_list,
            data_dir=data_dir,
            start_from_date=config['DEFAULT']['StartFromDate'],
            max_training_date=config['DEFAULT']['MaxTrainingDate'],
            forefast_only=False,
            dump_files=False,
            update_history=True,
        )
        dump_stockjobs(section, Path(data_dir), **data,)


if __name__ == '__main__':
    dump_datafiles()
