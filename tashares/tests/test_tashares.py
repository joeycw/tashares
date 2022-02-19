import unittest
from tashares.tests import tashares_context
from tashares.stockta import Stockta
from tashares.tashares import Tashares
#import tashares_context
#from stockta import Stockta
#from tashares import Tashares


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


# if __name__ == '__main__':
#    unittest.main()
