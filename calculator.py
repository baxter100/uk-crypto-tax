#   Overview
#
# read in history from csv
# convert into some internal data structre of trades
#
# go through all trades (in datetime order) where sell currency is not base fiat currency (GBP or EUR)
#
#    work out profit on that trade
#       determine whether to use FIFO or average
#
#
#
# add up profits
#
# work out final taxable amount
#
# output results
#

# Test Ideas
#   * Badly formatted CSV => errors
#   * Random date order CSV => chronological order
#   * correct date order CSV => chronological order
#   * gifts
#   * disposal with no corresponding buy --- should be costbasis of 0

# TODO: work out for Gift/Tips
# TODO: work out other currencies
# TODO: calculate samples by hand to compare
# TODO: compare methods here with strategy in README and update/note differences
# TODO: check tax strategy

import sys
import csv
import logging
from datetime import datetime, timedelta
from enum import IntEnum

from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


class TradeColumn(IntEnum):
    BUY_AMOUNT = 2
    BUY_CURRENCY = 3
    BUY_VALUE_BTC = 4
    BUY_VALUE_GBP = 5
    SELL_AMOUNT = 6
    SELL_CURRENCY = 7
    SELL_VALUE_BTC = 8
    SELL_VALUE_GBP = 9
    SPREAD = 10
    EXCHANGE = 11
    DATE = 13


DATE_FORMAT = "%d.%m.%Y %H:%M"
BASE_FIAT_CURRENCY = "GBP"
#### List of possible fiat currencies (currently just GBP)
fiat_list = ["GBP"]


class Trade:

    def __init__(self, buy_amount, buy_currency, buy_value_gbp, sell_amount, sell_currency, sell_value_gbp, date,
                 exchange):
        self.buy_amount = buy_amount
        self.buy_currency = buy_currency
        self.buy_value_gbp = buy_value_gbp
        self.sell_amount = sell_amount
        self.sell_currency = sell_currency
        self.sell_value_gbp = sell_value_gbp
        self.date = date
        self.exchange = exchange

        # QUESTION: What if you sell something you bought last tax year? 100% profit?
        self.trade_is_buy = self.buy_currency != BASE_FIAT_CURRENCY
        self.amount_accounted = 0

        #
        if self.buy_amount == 0:
            self.costbasisGBPpercoin = 0
        else:
            self.costbasisGBPpercoin = self.sell_value_gbp / self.buy_amount

    @staticmethod
    def from_csv(row):
        return Trade(float(row[TradeColumn.BUY_AMOUNT]),
                     row[TradeColumn.BUY_CURRENCY],
                     float(row[TradeColumn.BUY_VALUE_GBP]),
                     float(row[TradeColumn.SELL_AMOUNT]),
                     row[TradeColumn.SELL_CURRENCY],
                     float(row[TradeColumn.SELL_VALUE_GBP]),
                     datetime.strptime(row[TradeColumn.DATE], DATE_FORMAT),
                     row[TradeColumn.EXCHANGE])


def read_csv_into_trade_list(csv_filename):
    try:
        with open(csv_filename, encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Ignore Header Row
            datalist = [Trade.from_csv(row) for row in list(reader)]
            datalist.sort(key=lambda trade: trade.date)
            logger.debug(f"Loaded {len(datalist)} trades from {csv_filename}")
            return datalist
    except Exception as e:
        raise
        # TODO: Test with various wrong csvs and create nice error messages


class Gain:
    # Gain is a pair of whole or partially matched trades where proceeds and costbasis have been calculated.
    def __init__(self, disposal_amount, proceeds, cost_basis, disposal: Trade, corresponding_buy: Trade = None):

        self.currency = disposal.sell_currency
        self.date_sold = disposal.date

        self.sold_location = disposal.exchange

        self.date_acquired = corresponding_buy.date
        self.bought_location = corresponding_buy.exchange

        # amount of disposal currency accounted for
        self.disposal_amount = disposal_amount
        # gbp value of disposal amount
        self.proceeds = proceeds
        # cost of acquiring disposed currency
        self.cost_basis = cost_basis
        # gain doesn't account for fees
        self.gain_loss = self.proceeds - self.cost_basis

        if hasattr(disposal, "fee_value_gbp"):
            # TODO change to associated fee, which represents portion of sale
            self.fee = disposal.fee_value_gbp
        else:
            self.fee = 0

    def __str__(self):
        return "Amount: " + str(self.disposal_amount) + " Currency: " + str(self.currency) + " Date Acquired: " + str(
            self.date_acquired.strftime("%d.%m.%Y %H:%M")) + " Date Sold: " + str(
            self.date_sold.strftime("%d.%m.%Y %H:%M")) + " Location of buy: " + str(
            self.bought_location) + " Location of sell: " + str(self.sold_location) + " Proceeds in GBP: " + str(
            self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
            self.fee) + " Gain/Loss in GBP: " + str(self.gain_loss)

    def __repr__(self):
        return str(self)


def read_csv_into_fee_list(csv_filename):
    pass


def taxyearstart(taxyear):
    ### Get's beginning of tax year e.g.
    ### 2018 taxyear is 2017/18 taxyear and starts 06/04/2017
    return datetime(taxyear - 1, 4, 6)


def taxyearend(taxyear):
    return datetime(taxyear, 4, 6)  # This needs to be 6 as 05.06.2018 < 05.06.2018 12:31


def taxdatecheck(trade, taxyear):
    ### Checks trade is in correct year
    return taxyearstart(taxyear) <= trade.date <= taxyearend(taxyear)


def viable_sell(disposal):
    return disposal.sell_currency not in fiat_list and disposal.sell_currency != "" and disposal.sell_amount > 0


def date_match(disposal, corresponding_buy):
    # if the days are the same, there must be a better way!:
    return disposal.date.day == corresponding_buy.date.day and disposal.date.month == corresponding_buy.date.month and disposal.date.year == corresponding_buy.date.year


def currency_match(disposal, corresponding_buy):
    # Matches if proceeds from trade come from buy_trade
    return disposal.sell_currency == corresponding_buy.buy_currency and corresponding_buy.buy_amount > 0


def viable_day_match(disposal, corresponding_buy):
    return date_match(disposal, corresponding_buy) and currency_match(disposal, corresponding_buy)


def viable_bnb_match(disposal, corresponding_buy):
    # This is inclusive of the next 30 days.
    return currency_match(disposal,
                          corresponding_buy) and disposal.date.date() + timedelta(
        days=30) > corresponding_buy.date.date() > disposal.date.date()


def gain_from_pair(disposal, corresponding_buy):
    # TODO: Note profit uses disposal.buy_value_gbp, not disposal.sell_value_gbp
    #
    ### Calculate gain when two trades have been matched
    amount_disposal_accounted_for = corresponding_buy.buy_amount
    if corresponding_buy.buy_amount > disposal.sell_amount:
        # limit the amount to the amount sold
        amount_disposal_accounted_for = disposal.sell_amount

    cost_basis = corresponding_buy.costbasisGBPpercoin * amount_disposal_accounted_for
    proceeds = disposal.buy_value_gbp * (amount_disposal_accounted_for / disposal.sell_amount)

    gain = Gain(amount_disposal_accounted_for, proceeds, cost_basis, disposal, corresponding_buy)
    return gain


def update_trade_list_after_fifo_pair():
    pass


def append_gain_info_to_output():
    pass


def calculate_fifo_gains(trade_list, tax_year, trade_match_condition):
    # TODO: make sure trade list is in chrono order
    fifototal = 0
    for disposal in trade_list:
        if viable_sell(disposal):
            for corresponding_buy in trade_list:
                # begins checking trades to match with from start
                # Trades get updated as this iteration happens, to reduce buy_amount of corresponding buy and sell amount of disposal

                if trade_match_condition(disposal, corresponding_buy):
                    calculated_gain = gain_from_pair(disposal, corresponding_buy)
                    if taxdatecheck(disposal, tax_year):
                        # Only add gains from tax year, but need to go through all trades.
                        fifototal += calculated_gain.gain_loss  # adds gain from this pair to total

                    append_gain_info_to_output()
                    update_trade_list_after_fifo_pair()

    return fifototal


def calculate_day_gains_fifo(trade_list, tax_year):
    return calculate_fifo_gains(trade_list, tax_year, viable_day_match)


def calculate_bnb_gains_fifo(trade_list, tax_year):
    return calculate_fifo_gains(trade_list, tax_year, viable_bnb_match)


### Calculate gains on trades using 404 holdings rule
def update_trade_list_after_avg_pair():
    pass


def avg_cost_basis_up_to_trade(disposal: Trade, accounted_for_cost_basis, accounted_for_disposal_amount, trade_list):
    cost_basis_sum = 0
    amount_bought_sum = 0
    for earlier_trade in trade_list:
        if earlier_trade.date < disposal.date:

            if currency_match(disposal, earlier_trade):
                cost_basis_sum += earlier_trade.costbasisGBPpercoin * earlier_trade.buy_amount
                amount_bought_sum += earlier_trade.buy_amount
    if amount_bought_sum - accounted_for_disposal_amount == 0:
        return 0
    else:
        return (cost_basis_sum - accounted_for_cost_basis) * disposal.sell_amount / (
                    amount_bought_sum - accounted_for_disposal_amount)


def calculate_average_gains_for_asset(taxyear, asset, trade_list: List[Trade]):
    # 404 holdings is calculated for each non-fiat asset.
    total_gain_loss = 0
    accounted_for_cost_basis = 0
    accounted_for_disposal_amount = 0
    for disposal in trade_list:
        if disposal.sell_currency == asset and viable_sell(disposal):
            # TODO: make sense of this. I think it's correct but it's confusing
            costbasis = avg_cost_basis_up_to_trade(disposal, accounted_for_cost_basis, accounted_for_disposal_amount,
                                                   trade_list)
            accounted_for_cost_basis += costbasis
            accounted_for_disposal_amount += disposal.sell_amount

            if taxdatecheck(disposal, taxyear):
                total_gain_loss += disposal.buy_value_gbp - costbasis

            append_gain_info_to_output()
            update_trade_list_after_avg_pair()

    return total_gain_loss


def calculate_average_gains(taxyear, trade_list):
    averagetotal = 0
    crypto_list = []
    for trade in trade_list:
        if trade.sell_currency not in crypto_list and trade.sell_currency not in fiat_list:
            crypto_list.append(trade.sell_currency)
            averagetotal += calculate_average_gains_for_asset(taxyear, trade.sell_currency, trade_list)

    return averagetotal


def calculate_capital_gain(trade_list):
    for i, trade in enumerate(trade_list):
        print(trade.date, "::", trade.buy_amount, trade.buy_currency, "=", trade.sell_value_gbp, "GBP")
    return 10


def output_to_html(results, html_filename):
    html_text = "<!DOCTYPE html>"
    # Create html file


if __name__ == "__main__":
    trades = read_csv_into_trade_list("examples/sample-trade-list.csv")
    capital_gains = calculate_capital_gain(trades)
    output_to_html(capital_gains, "tax-report.html")
