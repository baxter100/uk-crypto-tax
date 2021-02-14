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
#   * disposal with no corresponding buy --- should be costbasis of 0
#   * A BnB check with edge cases (29 days, 30 days, 31 days)

# TODO: work out for Gift/Tips
# TODO: Fix importing with "-" and gifts/tips etc.
# TODO: work out other currencies
# TODO: compare methods here with strategy in README and update/note differences
# TODO: check tax strategy
import json
import sys
import csv
import logging
from datetime import datetime, timedelta
from enum import IntEnum, Enum

from typing import List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO: Have config option of logging location
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

with open("config.json") as json_data_file:
    configs = json.load(json_data_file)


class GainType(Enum):
    FIFO = 1
    AVERAGE = 2


# TODO: Load these better
class TradeColumn(IntEnum):
    BUY_AMOUNT = configs["TRADE_CSV_INDICES"]["BUY_AMOUNT"]
    BUY_CURRENCY = configs["TRADE_CSV_INDICES"]["BUY_CURRENCY"]
    BUY_VALUE_BTC = configs["TRADE_CSV_INDICES"]["BUY_VALUE_BTC"]
    BUY_VALUE_GBP = configs["TRADE_CSV_INDICES"]["BUY_VALUE_GBP"]
    SELL_AMOUNT = configs["TRADE_CSV_INDICES"]["SELL_AMOUNT"]
    SELL_CURRENCY = configs["TRADE_CSV_INDICES"]["SELL_CURRENCY"]
    SELL_VALUE_BTC = configs["TRADE_CSV_INDICES"]["SELL_VALUE_BTC"]
    SELL_VALUE_GBP = configs["TRADE_CSV_INDICES"]["SELL_VALUE_GBP"]
    SPREAD = configs["TRADE_CSV_INDICES"]["SPREAD"]
    EXCHANGE = configs["TRADE_CSV_INDICES"]["EXCHANGE"]
    DATE = configs["TRADE_CSV_INDICES"]["DATE"]


# TODO: Load these better
class FeeColumn(IntEnum):
    FEE_AMOUNT = configs["FEE_CSV_INDICES"]["FEE_AMOUNT"]
    FEE_CURRENCY = configs["FEE_CSV_INDICES"]["FEE_CURRENCY"]
    FEE_VALUE_GBP_THEN = configs["FEE_CSV_INDICES"]["FEE_VALUE_GBP_THEN"]
    FEE_VALUE_GBP_NOW = configs["FEE_CSV_INDICES"]["FEE_VALUE_GBP_NOW"]
    TRADE_BUY_AMOUNT = configs["FEE_CSV_INDICES"]["TRADE_BUY_AMOUNT"]
    TRADE_BUY_CURRENCY = configs["FEE_CSV_INDICES"]["TRADE_BUY_CURRENCY"]
    TRADE_SELL_AMOUNT = configs["FEE_CSV_INDICES"]["TRADE_SELL_AMOUNT"]
    TRADE_SELL_CURRENCY = configs["FEE_CSV_INDICES"]["TRADE_SELL_CURRENCY"]
    EXCHANGE = configs["FEE_CSV_INDICES"]["EXCHANGE"]
    DATE = configs["FEE_CSV_INDICES"]["DATE"]


BNB_TIME_DURATION = timedelta(days=configs["BNB_TIME_DURATION"])
DATE_FORMAT = configs["DATE_FORMAT"]
NATIVE_CURRENCY = configs["NATIVE_CURRENCY"]
TAX_YEAR = configs["TAX_YEAR"]
UNTAXABLE_ALLOWANCE = configs["ANNUAL_UNTAXABLE_ALLOWANCE"][str(TAX_YEAR)]
TRADE_CSV = configs["TRADE_CSV"]
FEE_CSV = configs["FEE_CSV"]


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
        self.fee = None  # Set later from fee datafile

        self.native_value_per_coin = 0
        self.native_cost_per_coin = 0
        if self.buy_amount != 0:
            self.native_cost_per_coin = self.sell_value_gbp / self.buy_amount
            self.native_value_per_coin = self.buy_value_gbp / self.buy_amount

        self.unaccounted_buy_amount = self.buy_amount
        self.unaccounted_sell_amount = self.sell_amount

    @staticmethod
    def from_csv(row):
        for ind, val in enumerate(row):
            if val == "-":
                row[ind] = 0
        return Trade(float(row[TradeColumn.BUY_AMOUNT]),
                     row[TradeColumn.BUY_CURRENCY],
                     float(row[TradeColumn.BUY_VALUE_GBP]),
                     float(row[TradeColumn.SELL_AMOUNT]),
                     row[TradeColumn.SELL_CURRENCY],
                     float(row[TradeColumn.SELL_VALUE_GBP]),
                     datetime.strptime(row[TradeColumn.DATE], DATE_FORMAT),
                     row[TradeColumn.EXCHANGE])

    def get_current_cost(self):
        if self.buy_amount == 0:
            portion = 1
        else:
            portion = self.unaccounted_buy_amount / self.buy_amount
        if self.fee is not None:
            raw_cost = self.sell_value_gbp + self.fee.fee_value_gbp_at_trade
        else:
            raw_cost = self.sell_value_gbp

        cost = portion * raw_cost

        return cost

    def get_current_disposal_value(self):
        portion = self.unaccounted_sell_amount / self.sell_amount

        cost = portion * self.buy_value_gbp

        return cost

    def is_viable_sell(self):
        return self.unaccounted_sell_amount > 0 and self.sell_currency != NATIVE_CURRENCY and self.sell_currency != ""

    def __repr__(self):
        return f"<Trade {self.date} :: {self.buy_amount} {self.buy_currency} ({self.buy_value_gbp} GBP) <- " \
               f"{self.sell_amount} {self.sell_currency} ({self.sell_value_gbp} GBP)>"


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
        print(self)
    @staticmethod
    def from_csv(row):
        for ind, val in enumerate(row):
            if val == "-" or " ":
                row[ind] = 0

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

    def __repr__(self):
        return f"<Fee {self.date} :: {self.fee_amount} {self.fee_currency}"


class Gain:

    def __init__(self, gain_type: GainType, disposal_amount, disposal: Trade,
                 corresponding_buy: Optional[Trade] = None, average_cost=None):

        self.gain_type = gain_type
        self.currency = disposal.sell_currency
        self.date_sold = disposal.date
        self.disposal_amount_accounted = disposal_amount

        self.sold_location = disposal.exchange
        self.corresponding_buy = corresponding_buy
        if corresponding_buy is not None:
            self.cost_basis = corresponding_buy.native_cost_per_coin * self.disposal_amount_accounted
        else:
            self.cost_basis = average_cost * self.disposal_amount_accounted
        self.disposal_trade = disposal

        # NOTE: profit uses disposal.buy_value_gbp, not disposal.sell_value_gbp
        self.proceeds = disposal.buy_value_gbp * self.disposal_amount_accounted / disposal.sell_amount
        self.native_currency_gain_value = self.proceeds - self.cost_basis  # gain doesn't account for fees

        self.fee_value_gbp = 0
        if disposal.fee:
            self.fee_value_gbp = disposal.fee.fee_value_gbp_at_trade

    def __str__(self):
        if self.corresponding_buy is not None:
            return f"Type:{self.gain_type} Amount: {self.disposal_amount_accounted} Currency: {self.currency}" + " Date Acquired: " + str(
                self.corresponding_buy.date.strftime("%d.%m.%Y %H:%M")) + " Date Sold: " + str(
                self.date_sold.strftime("%d.%m.%Y %H:%M")) + " Location of buy: " + str(
                self.corresponding_buy.exchange) + " Location of sell: " + str(
                self.sold_location) + " Proceeds in GBP: " + str(
                self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
                self.fee_value_gbp) + " Gain/Loss in GBP: " + str(self.native_currency_gain_value)
        else:
            return f"Type:{self.gain_type} Amount: {self.disposal_amount_accounted} Currency: {self.currency}" + " Date Acquired: " + " Date Sold: " + str(
                self.date_sold.strftime("%d.%m.%Y %H:%M")) + " Location of buy: " + " Location of sell: " + str(
                self.sold_location) + " Proceeds in GBP: " + str(
                self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
                self.fee_value_gbp) + " Gain/Loss in GBP: " + str(self.native_currency_gain_value)


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
            next(reader)  # Ignore header row
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
        matching_trades = [t for t in trades if fee_matches_trade(fee, t)]
        if len(matching_trades) == 0:
            logger.warning(f"Could not find trade for fee {fee}.")
        elif len(matching_trades) > 1:
            logger.error(f"Found multiple trades for fee {fee}.")
        else:
            trade = matching_trades[0]
            trade.fee = fee


def within_tax_year(trade, tax_year):
    tax_year_start = datetime(tax_year - 1, 4, 6)  # 2018 taxyear is 2017/18 taxyear and starts 06/04/2017
    tax_year_end = datetime(tax_year, 4, 6)  # This needs to be 6 as 05.06.2018 < 05.06.2018 12:31
    return tax_year_start <= trade.date < tax_year_end


def currency_match(disposal, corresponding_buy):
    return disposal.sell_currency == corresponding_buy.buy_currency


def gain_from_pair(disposal, corresponding_buy):
    uncapped_amount = corresponding_buy.unaccounted_buy_amount / disposal.unaccounted_sell_amount
    disposal_amount_accounted_for = min(corresponding_buy.unaccounted_buy_amount, disposal.unaccounted_sell_amount)
    logger.debug(
        f"Matched {disposal_amount_accounted_for * 100 / disposal.unaccounted_sell_amount}% of \n\t{disposal} with \n\t{corresponding_buy}.")
    gain = Gain(GainType.FIFO, disposal_amount_accounted_for, disposal, corresponding_buy)
    disposal.unaccounted_sell_amount -= disposal_amount_accounted_for
    corresponding_buy.unaccounted_buy_amount -= disposal_amount_accounted_for
    return gain


def calculate_day_gains_fifo(trade_list):
    condition = lambda disposal, corresponding_buy: \
        disposal.date.date() == corresponding_buy.date.date()
    return calculate_fifo_gains(trade_list, condition)


def bnb_condition(disposal, corresponding_buy):
    return disposal.date.date() < corresponding_buy.date.date() <= (disposal.date + BNB_TIME_DURATION).date()


def calculate_bnb_gains_fifo(trade_list):
    return calculate_fifo_gains(trade_list, bnb_condition)


def calculate_fifo_gains(trade_list, trade_within_date_range):
    gains = []
    for disposal in trade_list:
        if disposal.is_viable_sell():
            for corresponding_buy in trade_list:
                if currency_match(disposal,
                                  corresponding_buy) and corresponding_buy.buy_amount > 0 and trade_within_date_range(
                    disposal, corresponding_buy) and disposal.is_viable_sell():
                    calculated_gain = gain_from_pair(disposal, corresponding_buy)
                    gains.append(calculated_gain)
    return gains


def calculate_104_gains_for_asset(asset, trade_list: List[Trade]):
    number_of_shares_in_pool = 0
    pool_of_actual_cost = 0
    # 104 holdings is calculated for each non-fiat asset.
    gain_list = []



    for trade in trade_list:
        if trade.buy_currency == asset:
            number_of_shares_in_pool += trade.unaccounted_buy_amount
            pool_of_actual_cost += trade.get_current_cost()
            trade.unaccounted_buy_amount = 0

        if trade.sell_currency == asset and trade.is_viable_sell():

            number_of_shares_to_sell = trade.unaccounted_sell_amount
            unaccounted_for_amount = 0
            if number_of_shares_to_sell > number_of_shares_in_pool:
                unaccounted_for_amount = number_of_shares_to_sell - number_of_shares_in_pool
                number_of_shares_to_sell = number_of_shares_in_pool

            average_cost = pool_of_actual_cost / number_of_shares_in_pool

            gain = Gain(GainType.AVERAGE, number_of_shares_to_sell, trade, average_cost=average_cost)
            gain_list.append(gain)
            # then update holding
            number_of_shares_in_pool -= number_of_shares_to_sell
            pool_of_actual_cost -= gain.cost_basis

            trade.unaccounted_sell_amount = unaccounted_for_amount

            if unaccounted_for_amount != 0:
                # Do future FIFO
                # TODO: Where disposal is not fully accounted for, need to do FIFO on later trades(after all 104 holdings have been done)
                #   see https://bettingbitcoin.io/cryptocurrency-uk-tax-treatments
                raise ValueError

    return gain_list


def calculate_104_holding_gains(trade_list: List[Trade]):
    non_native_asset_list = []
    for trade in trade_list:
        if trade.sell_currency not in non_native_asset_list and trade.sell_currency is not NATIVE_CURRENCY:
            non_native_asset_list.append(trade.sell_currency)

    gains = []
    for asset in non_native_asset_list:
        print(asset)
        gains.extend(calculate_104_gains_for_asset(asset, trade_list))

    return gains


def calculate_future_fifo_gains(trade_list: List[Trade]):
    return []
    # TODO: Go through future trades


def calculate_capital_gain(trade_list: List[Trade]):
    gains = []
    gains.extend(calculate_day_gains_fifo(trade_list))
    gains.extend(calculate_bnb_gains_fifo(trade_list))
    gains.extend(calculate_104_holding_gains(trade_list))
    gains.extend(calculate_future_fifo_gains(trade_list))
    return gains


def output_to_html(results, html_filename):
    html_text = "<!DOCTYPE html>"
    # TODO: Have format of this file in config file, and pass values to that formatting string.
    # TODO: Create output html file


def main():
    trades = read_csv_into_trade_list(TRADE_CSV)
    fees = read_csv_into_fee_list(FEE_CSV)
    assign_fees_to_trades(trades, fees)
    capital_gains = calculate_capital_gain(trades)
    relavant_capital_gains = [g for g in capital_gains if within_tax_year(g.disposal_trade, TAX_YEAR)]
    year_gains_sum = sum(
        [g.native_currency_gain_value for g in capital_gains if within_tax_year(g.disposal_trade, TAX_YEAR)])
    taxable_gain = max(0, year_gains_sum - UNTAXABLE_ALLOWANCE)

    print(f"Total gain for tax year {TAX_YEAR}: {year_gains_sum}.")
    print(f"Total taxable gain for tax year: {TAX_YEAR} -  {UNTAXABLE_ALLOWANCE} = {taxable_gain}.")
    output_to_html(capital_gains, "tax-report.html")


if __name__ == "__main__":
    main()
