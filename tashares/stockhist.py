# -*- coding: utf-8 -*-
import yfinance as yf
import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
from tashares.cfg import config

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


class Stockhist(object):
    """wrap yfinance to download stock history.
        - Input: stock symbol. 
        - Output: save stock price daily history into a file. 
    there are two modes:
    1. load from the local file of stock history (by default)
    2. update from internet server: download from yahoo! up to today, and upon request save history

    Args:
        symbol (string, required): stock symbol. Default: ''
        data_dir (string, optional): the directory of data files. Default: CWD, Currunt Working Directory
        update_history (bool, optional): download history and info if 'update_history=True'. Default: False, load local files only
        start_from_date (string, optional): the date to start downloading stock history. Default. '2015-01-01'
        dump_files (bool, optional): save updated history and info into files if 'dump_files=True'. Default: False, don't write files

    Examples:
        >>> from tashares import Stockhist
        >>> msft = Stockhist("MSFT")
        >>> msft = Stockhist(symbol="MSFT")
        >>> msft = Stockhist("MSFT", update_history=True)
        >>> msft = Stockhist("MSFT", data_dir='/tmp')
        >>> msft = Stockhist("MSFT", update_history=True, start_from_date='2020-01-01')
    """

    start_from_date = config['DEFAULT']['StartFromDate']
    historyfolder = config['DEFAULT']['HistoryFolder']
    history = pd.DataFrame()
    history_start_date: datetime
    history_stop_date: datetime

    def __init__(self, *args, **kwargs):

        self.symbol = kwargs.get('symbol', '') if len(args) == 0 else args[0]
        self.ticker = yf.Ticker(self.symbol)
        self.data_dir = kwargs.get('data_dir', '')
        if self.data_dir.is_dir():
            self.history = self.load_history(self.history_filename)

        if kwargs.get('update_history', False):
            self.start_from_date = kwargs.get('start_from_date', self.start_from_date)
            self.update_history(start_from_date=self.start_from_date)
        if kwargs.get('dump_files', False):
            self.dump_history_file(self.history_filename)

    def load_history(self, filename) -> pd.DataFrame:
        try:
            content = pd.read_csv(filename, sep='\t', parse_dates=True, index_col=[0])
            assert not content.empty
            # sort by date in case that is not ordered
            content = content.sort_index()
            self.history_start_date = content.index.min()
            self.history_stop_date = content.index.max()
            assert datetime.now() >= self.history_start_date
            logging.debug(
                f" {self.symbol} : loaded {len(content)} lines in {filename} from {self.history_start_date} to {self.history_stop_date}")
        except:
            logging.debug(f" history file '{filename}' nonexistent or broken")
            content = pd.DataFrame()
        finally:
            return content

    def update_history(self, start_from_date='2015-01-01', stop_at_date='') -> None:
        if bool(self.ticker):
            assert self.ticker.ticker == self.symbol
            try:
                content = self.ticker.history(
                    start=self.history.index.max() if (not self.history.empty) else datetime.strptime(start_from_date, '%Y-%m-%d'),
                    end=datetime.today() if stop_at_date == '' else datetime.strptime(stop_at_date, '%Y-%m-%d'),
                    auto_adjust=False, back_adjust=False, rounding=True)
                if not content.empty:
                    content = content[pd.notnull(content.index.values)]
                    # merge with history loaded from file
                    #self.history = self.history.append(content)
                    self.history = pd.concat([self.history, content])
                    self.history = self.history[~self.history.index.duplicated(keep='last')]
                    self.history = self.history.sort_index()
                    self.history_start_date = self.history.index.min()
                    self.history_stop_date = self.history.index.max()
                logging.debug(
                    f" {self.symbol} : downloaded history {len(self.history)} days, from {self.history_start_date} to {self.history_stop_date}")
            except:
                logging.critical(f"{self.symbol}: fail to download history")

    def dump_history_file(self, filename) -> None:
        if not self.history.empty and filename.parent.is_dir():
            self.history.to_csv(filename, sep='\t',
                                encoding='utf-8', index=True, float_format='%.5f')
            logging.info(f" {self.symbol} : write {len(self.history)} lines to {filename}")

    @property
    def history_filename(self):
        return self.data_dir / f"{self.historyfolder}/{self.symbol}"

    @property
    def symbol(self):
        return self._symbol

    @symbol.setter
    def symbol(self, value: str):
        if value == '':
            logging.warning(
                f"__init__() missing 1 required positional argument: 'symbol', e.g. Stock('MSFT') or Stock(symbol='MSFT')...")
        self._symbol = value

    @property
    def data_dir(self):
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value: str):
        if not Path(value).is_dir():
            logging.warning(f"data directory {value} does not exist")
        self._data_dir = Path(value)

    def __str__(self):
        return f"{str(self.__class__)} : {self.symbol} : history {len(self.history)} days, {len(self.history.columns)} columns"

    def __len__(self):
        return len(self.history)

    def __call__(self, *args, **kwargs):
        self.update_history()
