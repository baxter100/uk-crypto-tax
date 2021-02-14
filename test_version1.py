import unittest
from calculator import *

sample_csv = "examples/sample-trade-list.csv"


# check that things that should be floats are float and strings are strings

def bnb_match(disposal, corresponding_buy):
    return disposal.date.date() < corresponding_buy.date.date() <= (disposal.date + BNB_TIME_DURATION).date()


class Test(unittest.TestCase):
    def test_csv_loading(self):
        trade_list = read_csv_into_trade_list(sample_csv)

        self.assertIsInstance(trade_list[0], Trade)
        self.assertIsInstance(trade_list[0], Trade)

        trade_one = trade_list[1]
        self.assertEqual(trade_one.buy_amount, 0.6)
        self.assertEqual(trade_one.buy_currency, "ETH")
        self.assertEqual(trade_one.native_cost_per_coin, 417 / 0.6)

        # trade list should be in chrono order
        for x in range(0, len(trade_list)):
            print(trade_list[x].date)
            for y in range(0, len(trade_list)):
                if x < y:
                    self.assertLess(trade_list[x].date, trade_list[y].date)

    def test_matching_edge_cases(self):
        disposal_date = datetime.strptime("15.03.2021 18:13", DATE_FORMAT)
        disposal = Trade(0.1, "ETH", 0.1, 0.1, "BTC", 0.1, disposal_date,
                         "exchange")

        buy1 = Trade(0.1, "BTC", 0.1, 0.1, "ETH", 0.1, disposal_date,
                     "exchange")

        self.assertFalse(bnb_match(disposal, buy1))

        buy2_date = datetime.strptime("15.04.2021 18:13", DATE_FORMAT)
        buy2 = Trade(0.1, "BTC", 0.1, 0.1, "ETH", 0.1, buy2_date,
                     "exchange")

        self.assertFalse(bnb_match(disposal, buy2))

        buy3_date = datetime.strptime("15.04.2021 00:00", DATE_FORMAT)
        buy3 = Trade(0.1, "BTC", 0.1, 0.1, "ETH", 0.1, buy3_date,
                     "exchange")

        self.assertFalse(bnb_match(disposal, buy3))

        buy4_date = datetime.strptime("16.04.2021 18:13", DATE_FORMAT)
        buy4 = Trade(0.1, "BTC", 0.1, 0.1, "ETH", 0.1, buy4_date,
                     "exchange")

        self.assertFalse(bnb_match(disposal, buy4))

        buy5_date = datetime.strptime("14.04.2021 19:13", DATE_FORMAT)
        buy5 = Trade(0.1, "BTC", 0.1, 0.1, "ETH", 0.1, buy5_date,
                     "exchange")

        self.assertTrue(bnb_match(disposal, buy5))

    def test_gains(self):
        day_gains = 52.5
        bnb_gains = -24.8019802
        avg_gains = 127.1597395
        total_gains = 154.8577593
        tax_year = 2018

        trade_list = read_csv_into_trade_list(sample_csv)

        calculated_day = calculate_day_gains_fifo(trade_list)
        relevant_day_gains = sum(
            [g.native_currency_gain_value for g in calculated_day if within_tax_year(g.disposal_trade, tax_year)])
        
        self.assertAlmostEqual(day_gains, relevant_day_gains,4)
        calculated_bnb = calculate_bnb_gains_fifo(trade_list)
        relevant_bnb_gains = sum(
            [g.native_currency_gain_value for g in calculated_bnb if within_tax_year(g.disposal_trade, tax_year)])
        self.assertAlmostEqual(bnb_gains, relevant_bnb_gains,4)
        calculated_avg = calculate_104_holding_gains(trade_list)
        relevant_104_gains = sum(
            [g.native_currency_gain_value for g in calculated_avg if within_tax_year(g.disposal_trade, tax_year)])

        # calculated_total = calculate_capital_gain(trade_list)



        self.assertAlmostEqual(avg_gains, relevant_104_gains,4)
        # self.assertEqual(total_gains,calculated_total)


if __name__ == '__main__':
    unittest.main()
