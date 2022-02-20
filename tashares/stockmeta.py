# -*- coding: utf-8 -*-
import json
import logging
from tashares.cfg import config
from tashares.stockta import Stockta

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.INFO,
                    datefmt='%m/%d/%Y %I:%M:%S %p')


class Stockmeta(Stockta):
    """load/update stock info, include company name, sector, industry ...
    """

    infofolder = config['DEFAULT']['InfoFolder']

    def __init__(self, *args, **kwargs):
        super(Stockmeta, self).__init__(*args, **kwargs)
        if self.data_dir.is_dir():
            self.info = self.load(self.info_filename)

        if kwargs.get('update_history', False):
            self.update()
        if kwargs.get('dump_files', False):
            self.dump_info_file(self.info_filename)

    def load(self, info_filename) -> dict:
        info = {}
        try:
            with open(info_filename) as d:
                info = json.load(d)
                logging.debug(
                    f" {self.ticker.ticker} : loaded {len(info)} pairs from {info_filename}")
        except:
            logging.debug(f" info file '{info_filename}' nonexistent or broken")
        finally:
            return info

    def update(self) -> None:
        if bool(self.ticker):
            assert self.ticker.ticker == self.symbol
            try:
                self.info = self.ticker.info
                logging.debug(
                    f" {self.ticker.ticker} : downloaded {len(self.info)} pairs")
            except:
                logging.warning(
                    f"{self.ticker.ticker}: info downloading is broken")

    def dump_info_file(self, filename) -> None:
        if filename.parent.is_dir() and len(self.info) > 2:
            with open(filename, 'w') as d:
                d.write(json.dumps(self.info))
                logging.debug(f"{self.symbol}: write {len(self.info)} pairs to {filename}")

    @property
    def info_filename(self):
        return self.data_dir / f"{self.infofolder}/{self.symbol}"

    def __len__(self):
        return len(self.info)

    def __str__(self):
        return '\n'.join([super(Stockmeta, self).__str__(),
                          f"{str(self.__class__)} : {self.symbol} : info {len(self.info)} pairs"])

    def __call__(self,  *args, **kwargs):
        super(Stockmeta, self).__call__(*args, **kwargs)
        self.update()
