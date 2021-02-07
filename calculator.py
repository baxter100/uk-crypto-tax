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

# Assumptions
#   * All dates are UTC

# Test Ideas
#   * Badly formatted CSV => errors
#   * Random date order CSV => chronological order
#   * correct date order CSV => chronological order
#   * gifts
#   * A BnB check with edge cases (29 days, 30 days, 31 days)

# TODO: work out for Gift/Tips
# TODO: work out other currencies
# TODO: calculate samples by hand to compare
# TODO: compare methods here with strategy in README and update/note differences
# TODO: check tax strategy

import sys
import csv
import logging
from datetime import datetime, timedelta
from enum import IntEnum, Enum

from typing import List

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO: Have config option of logging location
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


# TODO: Load this in from config file (but maybe still have as enum)
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


# TODO: Load this in from config file (but maybe still have as enum)
class FeeColumn(IntEnum):
    FEE_AMOUNT = 2
    FEE_CURRENCY = 3
    FEE_VALUE_GBP_THEN = 4
    FEE_VALUE_GBP_NOW = 5
    TRADE_BUY_AMOUNT = 6
    TRADE_BUY_CURRENCY = 7
    TRADE_SELL_AMOUNT = 8
    TRADE_SELL_CURRENCY = 9
    EXCHANGE = 10
    DATE = 11


class GainType(Enum):
    FIFO = 1
    AVERAGE = 2


# TODO: Have all of these be loaded in from config file
BNB_TIME_DURATION = timedelta(days=30)
DATE_FORMAT = "%d.%m.%Y %H:%M"
NATIVE_CURRENCY = "GBP"
TAX_YEAR = 2020
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
        self.fee = None # Set later from fee datafile
        self.is_viable_sell = self.sell_currency != NATIVE_CURRENCY and \
                           self.sell_currency != "" and \
                           self.sell_amount > 0


        self.native_value_per_coin = 0
        if self.buy_amount != 0:
            self.native_value_per_coin = self.sell_value_gbp / self.buy_amount

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


class Fee:

    def __init__(self, fee_amount, fee_currency, fee_value_gbp_at_trade, fee_value_gbp_now, trade_buy_amount, 
                 trade_buy_currency, trade_sell_amount, trade_sell_currency, date, exchange):
        self.fee_amount = fee_amount
        self.fee_currency = fee_currency
        self.fee_value_gbp_at_trade = fee_value_gbp_at_trade
        self.fee_value_gbp_now = fee_value_gbp_now
        self.trade_buy_amount = trade_buy_amount
        self.trade_buy_currency = trade_buy_currency
        self.trade_sell_amount = trade_sell_amount
        self.trade_sell_currency = trade_sell_currency
        self.date = date
        self.exchange = exchange

    @staticmethod
    def from_csv(row):
        return Fee(float(row[FeeColumn.FEE_AMOUNT]),
                   row[FeeColumn.FEE_CURRENCY],
                   float(row[FeeColumn.FEE_VALUE_GBP_THEN]),
                   float(row[FeeColumn.FEE_VALUE_GBP_NOW]),
                   float(row[FeeColumn.TRADE_BUY_AMOUNT]),
                   row[FeeColumn.TRADE_BUY_CURRENCY],
                   float(row[FeeColumn.TRADE_SELL_AMOUNT]),
                   row[FeeColumn.TRADE_SELL_CURRENCY],
                   row[FeeColumn.DATE],
                   row[FeeColumn.EXCHANGE])

class Gain:
    # Gain is a pair of whole or partially matched trades where proceeds and costbasis have been calculated.
    def __init__(self, gain_type: GainType, disposal_amount, proceeds, cost_basis, disposal: Trade, 
                 corresponding_buy: Trade = None):

        self.gain_type = gain_type
        self.currency = disposal.sell_currency
        self.date_sold = disposal.date

        self.sold_location = disposal.exchange
        self.corresponding_buy = corresponding_buy
        self.disposal_trade = disposal

        # amount of disposal currency accounted for
        self.disposal_amount = disposal_amount
        # gbp value of disposal amount
        self.proceeds = proceeds
        # cost of acquiring disposed currency
        self.cost_basis = cost_basis
        # gain doesn't account for fees
        self.native_currency_gain_value = self.proceeds - self.cost_basis

        self.fee_value_gbp = 0
        if disposal.fee:
            self.fee_value_gbp = disposal.fee.fee_value_gbp_at_trade

    def __str__(self):
        return "Amount: " + str(self.disposal_amount) + " Currency: " + str(self.currency) + " Date Acquired: " + str(
            self.date_acquired.strftime("%d.%m.%Y %H:%M")) + " Date Sold: " + str(
            self.date_sold.strftime("%d.%m.%Y %H:%M")) + " Location of buy: " + str(
            self.bought_location) + " Location of sell: " + str(self.sold_location) + " Proceeds in GBP: " + str(
            self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
            self.fee) + " Gain/Loss in GBP: " + str(self.native_currency_gain_value)

    def __repr__(self):
        return str(self)



def read_csv_into_trade_list(csv_filename):
    try:
        with open(csv_filename, encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Ignore Header Row
            trades = [Trade.from_csv(row) for row in list(reader)]
            trades.sort(key=lambda trade: trade.date)
            logger.debug(f"Loaded {len(trades)} trades from {csv_filename}.")
            return trades
    except FileNotFoundError as e:
        logger.error(f"Could not find fees csv: '{csv_filename}'.")
        raise
    except Exception as e:
        raise
        # TODO: Test with various wrong csvs and create nice error messages


def read_csv_into_fee_list(csv_filename):
    try:
        with open(csv_filename, encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            next(reader) # Ignore header row
            fees = [Fee.from_csv(row) for row in list(reader)]
            logger.debug(f"Loaded {len(fees)} fees from {csv_filename}.")
            return fees
    except FileNotFoundError as e:
        logger.error(f"Could not find fees csv: '{csv_filename}'.")
        return []
    except Exception as e:
        raise
        # TODO: Test with various wrong csvs and create nice error messages


def fee_matches_trade(fee, trade):
    return trade.date == fee.date and \
           trade.sell_currency == fee.trade_sell_currency and \
           trade.sell_amount == fee.trade_sell_amount and \
           trade.buy_currency == fee.trade_buy_currency and \
           trade.buy_amount == fee.trade_buy_amount



def assign_fees_to_trades(trades, fees):
    for fee in fees:
        trades = [t for t in trades if fee_matches_trade(fee, t)]
        if len(trades) == 0:
            logger.warn(f"Could not find trade for fee {fee}.")
        elif len(trades) > 1:
            logger.error(f"Found multiple trades for fee {fee}.")
        else:
            trades[0].fee = fee


def within_tax_year(trade, tax_year):
    tax_year_start = datetime(tax_year - 1, 4, 6) ### 2018 taxyear is 2017/18 taxyear and starts 06/04/2017
    tax_year_end = datetime(tax_year, 4, 6) # This needs to be 6 as 05.06.2018 < 05.06.2018 12:31
    ### Checks trade is in correct year
    return tax_year_start <= trade.date <= tax_year_end


def date_match(disposal, corresponding_buy):
    # if the days are the same, there must be a better way!:
    return disposal.date.date == corresponding_buy.date.date
    # return disposal.date.day == corresponding_buy.date.day and disposal.date.month == corresponding_buy.date.month and disposal.date.year == corresponding_buy.date.year


def currency_match(disposal, corresponding_buy):
    # Matches if proceeds from trade come from buy_trade
    return disposal.sell_currency == corresponding_buy.buy_currency and corresponding_buy.buy_amount > 0


def gain_from_pair(disposal, corresponding_buy):
    # TODO: Note profit uses disposal.buy_value_gbp, not disposal.sell_value_gbp
    #
    ### Calculate gain when two trades have been matched
    amount_disposal_accounted_for = corresponding_buy.buy_amount
    if corresponding_buy.buy_amount > disposal.sell_amount:
        # limit the amount to the amount sold
        amount_disposal_accounted_for = disposal.sell_amount

    cost_basis = corresponding_buy.native_value_per_coin * amount_disposal_accounted_for
    proceeds = disposal.buy_value_gbp * (amount_disposal_accounted_for / disposal.sell_amount)

    gain = Gain(GainType.FIFO, amount_disposal_accounted_for, proceeds, cost_basis, disposal, corresponding_buy)
    return gain


def update_trade_list_after_fifo_pair():
    pass


def calculate_day_gains_fifo(trade_list):
    condition = lambda disposal, corresponding_buy: \
        currency_match(disposal, corresponding_buy) and \
        date_match(disposal, corresponding_buy)
                                                    
    return calculate_fifo_gains(trade_list, condition)


def calculate_bnb_gains_fifo(trade_list):
    condition = lambda disposal, corresponding_buy: \
        currency_match(disposal, corresponding_buy) and \
        disposal.date < corresponding_buy.date <= (disposal.date + BNB_TIME_DURATION)

    return calculate_fifo_gains(trade_list, condition)


def calculate_fifo_gains(trade_list, trade_match_condition):
    gains = []
    for disposal in [trade for trade in trade_list if trade.is_viable_sell]:
        for corresponding_buy in trade_list:
            # Trades get updated as this iteration happens, to reduce buy_amount of corresponding buy and sell amount of disposal
            if trade_match_condition(disposal, corresponding_buy):
                calculated_gain = gain_from_pair(disposal, corresponding_buy)
                gains.append(calculated_gain)
                update_trade_list_after_fifo_pair()
    return gains


### Calculate gains on trades using 404 holdings rule
def update_trade_list_after_avg_pair():
    pass


def avg_cost_basis_up_to_trade(disposal: Trade, accounted_for_cost_basis, accounted_for_disposal_amount, trade_list):
    cost_basis_sum = 0
    amount_bought_sum = 0
    for earlier_trade in trade_list:
        if earlier_trade.date < disposal.date:

            if currency_match(disposal, earlier_trade):
                cost_basis_sum += earlier_trade.native_value_per_coin * earlier_trade.buy_amount
                amount_bought_sum += earlier_trade.buy_amount
    if amount_bought_sum - accounted_for_disposal_amount == 0:
        return 0
    else:
        return (cost_basis_sum - accounted_for_cost_basis) * disposal.sell_amount / (
                    amount_bought_sum - accounted_for_disposal_amount)


def calculate_average_gains_for_asset(asset, trade_list: List[Trade]):
    # 404 holdings is calculated for each non-fiat asset.
    gains = []
    accounted_for_cost_basis = 0
    accounted_for_disposal_amount = 0
    for disposal in trade_list:
        if disposal.sell_currency == asset and disposal.is_viable_sell:
            # TODO: make sense of this. I think it's correct but it's confusing
            costbasis = avg_cost_basis_up_to_trade(disposal, accounted_for_cost_basis, accounted_for_disposal_amount,
                                                   trade_list)
            accounted_for_cost_basis += costbasis
            accounted_for_disposal_amount += disposal.sell_amount
            gain = None  # TODO: Create Gain object
            # TODO: Set gain object's "gain amount" to what was previously being added to a total_gains number
            # gain.native_currency_gain_value = disposal.buy_value_gbp - costbasis
            # gains.append(gain)

            update_trade_list_after_avg_pair()

    return gains


def calculate_average_gains(trade_list):
    gains = []
    crypto_list = []
    for trade in trade_list:
        if trade.sell_currency not in crypto_list and trade.sell_currency not in fiat_list:
            crypto_list.append(trade.sell_currency)
            gains.extend(calculate_average_gains_for_asset(trade.sell_currency, trade_list))
    return gains


def calculate_capital_gain(trade_list, tax_year):
    gains = []
    # for i, trade in enumerate(trade_list):
        # logger.debug(f"{trade.date} :: {trade.buy_amount} {trade.buy_currency} = {trade.sell_value_gbp} GBP")
    gains.extend(calculate_day_gains_fifo(trade_list))
    gains.extend(calculate_bnb_gains_fifo(trade_list))
    gains.extend(calculate_average_gains(trade_list))
    return [g for g in gains if within_tax_year(g.disposal_trade, tax_year)]


def output_to_html(results, html_filename):
    html_text = "<!DOCTYPE html>"
    # Create html file


def main():
    trades = read_csv_into_trade_list("examples/sample-trade-list.csv")
    fees = read_csv_into_fee_list("examples/sample-fee-list.csv")
    assign_fees_to_trades(trades, fees)
    capital_gains = calculate_capital_gain(trades, TAX_YEAR)
    output_to_html(capital_gains, "tax-report.html")


if __name__ == "__main__":
    main()
