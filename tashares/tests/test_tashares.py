import unittest
from pathlib import Path
from tashares.stockta import Stockta
from tashares.tashares import Tashares
from tashares.wrapper import dump_datafiles


class TestTashares(unittest.TestCase):

    def test_stockta_ta(self):
        symbol = Stockta('000001.SZ', update_history=True, start_from_date='2021-01-01')
        print(symbol)
        self.assertEqual(symbol._symbol, '000001.SZ')
        self.assertGreater(len(symbol.history), 0)
        self.assertEqual(len(symbol.ta.columns), 155)

    def test_tashares(self):
        tas = Tashares()
        result = tas()
        self.assertGreaterEqual(len(result), 0)

    def test_dumpfiles(self):
        data_dir = Path(__file__).parent.parent
        result = dump_datafiles(data_dir / 'data/list_of_interest')
        self.assertEqual(result, None)
