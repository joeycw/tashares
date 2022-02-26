import unittest
from pathlib import Path
import numpy as np
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

    def test_ashares_class(self):
        tas = Tashares()
        results = tas()
        print(results)
        self.assertGreater(len(results), 0)
        tas.dump_forecast_data()
        self.assertFalse(tas.forecasting_data.empty)

    def test_ashares_models(self):
        data_dir = Path(__file__).parent
        test_file = data_dir / 'test_asharesofinterest.csv'
        tas = Tashares(load_data_from=test_file)
        result = tas()
        ground = [[0.5373540856031128], [0.5227626459143966], [0.5112533278722097], [0.5112533278722097]]
        print(result)
        print(ground)
        print(np.sum(ground))
        self.assertAlmostEqual(np.sum(np.array(result)), np.sum(ground), places=7)

    def test_symbols_models(self):
        data_dir = Path(__file__).parent
        test_file = data_dir / 'test_symbolsofinterest.csv'
        tas = Tashares(task_type='stocks', load_data_from=test_file)
        result = tas()
        ground = [[0.5630597014925377], [0.558582089552239], [0.5523320895522392], [0.5411567164179102]]
        print(result)
        print(ground)
        print(np.sum(ground))
        self.assertAlmostEqual(np.sum(np.array(result)), np.sum(ground), places=7)
