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
# TODO: Explain fees
# TODO: Fix poloniex fee exporting (they are getting fee currency incorrect)
import json
import sys
import csv
import logging
from datetime import datetime, timedelta
from enum import IntEnum, Enum

from typing import List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# TODO: Have config option of logging location
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

with open("config.json") as json_data_file:
    configs = json.load(json_data_file)


class GainType(Enum):
    DAY_FIFO = 1
    BNB_FIFO = 2
    AVERAGE = 3
    FUTURE_FIFO = 4
    UNACCOUNTED = 5


# TODO: Load these better
class TradeColumn(IntEnum):
    TRADE_TYPE = configs["TRADE_CSV_INDICES"]["TRADE_TYPE"]
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
    TRADE_TYPE = configs["FEE_CSV_INDICES"]["TRADE_TYPE"]
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
TRADE_TYPES_TO_IMPORT = configs["TRADE_TYPES_TO_IMPORT"]
FEE_TYPES_TO_IMPORT = configs["FEE_TYPES_TO_IMPORT"]
NATIVE_CURRENCY = configs["NATIVE_CURRENCY"]
TAX_YEAR = configs["TAX_YEAR"]
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
            self.native_value_per_coin = self.buy_value_gbp / self.buy_amount

            self.native_cost_per_coin = self.sell_value_gbp / self.buy_amount

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
                     datetime.strptime(row[TradeColumn.DATE],DATE_FORMAT),
                     row[TradeColumn.EXCHANGE])

    def account_for_fee_in_cost(self):
        self.native_cost_per_coin = 0
        if self.buy_amount != 0:
            self.native_cost_per_coin = (self.sell_value_gbp + self.fee.fee_value_gbp_at_trade) / self.buy_amount

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

    def is_possible_duplicate(self, trade):
        return self.buy_amount == trade.buy_amount and self.buy_currency == trade.buy_currency and self.buy_value_gbp == trade.buy_value_gbp and self.sell_amount == trade.sell_amount and self.sell_currency == trade.sell_currency and self.sell_value_gbp == trade.sell_value_gbp and self.date == trade.date and self.exchange == trade.exchange

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

    def is_possible_duplicate(self, fee):
        return self.fee_amount == fee.fee_amount and self.fee_currency == fee.fee_currency and self.fee_value_gbp_at_trade == fee.fee_value_gbp_at_trade and self.fee_value_gbp_now == fee.fee_value_gbp_now and self.trade_buy_amount == fee.trade_buy_amount and self.trade_buy_currency == fee.trade_buy_currency and self.trade_sell_amount == fee.trade_sell_amount and self.trade_sell_currency == fee.trade_sell_currency and self.date == fee.date and self.exchange == fee.exchange

    @staticmethod
    def from_csv(row):

        for ind, val in enumerate(row):
            if val == "-" or val == " ":
                row[ind] = 0

        return Fee(float(row[FeeColumn.FEE_AMOUNT]),
                   row[FeeColumn.FEE_CURRENCY],
                   float(row[FeeColumn.FEE_VALUE_GBP_THEN]),
                   float(row[FeeColumn.FEE_VALUE_GBP_NOW]),
                   float(row[FeeColumn.TRADE_BUY_AMOUNT]),
                   row[FeeColumn.TRADE_BUY_CURRENCY],
                   float(row[FeeColumn.TRADE_SELL_AMOUNT]),
                   row[FeeColumn.TRADE_SELL_CURRENCY],
                   datetime.strptime(row[FeeColumn.DATE], DATE_FORMAT),
                   row[FeeColumn.EXCHANGE])

    def __repr__(self):
        return f"<Fee {self.date} :: {self.fee_amount} {self.fee_currency}"


class Gain:
    heading = "<th>Match Type</th>" \
              "<th>Amount</th>" \
              "<th>Currency</th>" \
              "<th>Date Acquired</th>" \
              "<th>Date Sold</th>" \
              "<th>Proceeds</th>" \
              "<th>Cost basis</th>" \
              "<th>Gain Loss</th>"

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
        elif average_cost is not None:
            self.cost_basis = average_cost * self.disposal_amount_accounted

        elif self.gain_type == GainType.UNACCOUNTED:
            self.cost_basis = 0
        self.disposal_trade = disposal

        proportion_accounted_for = self.disposal_amount_accounted / disposal.sell_amount

        # NOTE: profit uses disposal.buy_value_gbp, not disposal.sell_value_gbp
        self.proceeds = disposal.buy_value_gbp * proportion_accounted_for
        self.native_currency_gain_value = self.proceeds - self.cost_basis

        self.fee_value_gbp = 0
        if self.disposal_trade.buy_currency == NATIVE_CURRENCY:

            if disposal.fee is not None:
                self.fee_value_gbp = disposal.fee.fee_value_gbp_at_trade * proportion_accounted_for
            self.native_currency_gain_value -= self.fee_value_gbp

    def html_format(self):

        corresponding_buy_date = ""
        if self.corresponding_buy is not None:
            corresponding_buy_date = self.corresponding_buy.date.strftime(DATE_FORMAT)

        disposal_date = self.date_sold.strftime(DATE_FORMAT)
        proceeds = round(self.proceeds,2)
        cost_basis = round(self.cost_basis,2)
        native_currency_gain_value = round(self.native_currency_gain_value,2)
        gain_type = ""
        if self.gain_type == GainType.DAY_FIFO:
            gain_type = "Same Day"
        if self.gain_type == GainType.BNB_FIFO:
            gain_type = "BNB Day"
        if self.gain_type == GainType.AVERAGE:
            gain_type = "104"
        if self.gain_type == GainType.FUTURE_FIFO:
            gain_type = "FIFO (future)"
        if self.gain_type == GainType.UNACCOUNTED:
            gain_type = "Unaccounted"
        return f"<tr><td>{gain_type}</td> <td>{self.disposal_amount_accounted}</td> <td>{self.currency}</td> <td>{corresponding_buy_date}</td>  <td>{disposal_date}</td> <td>{proceeds}</td> <td> {cost_basis}</td> <td>{native_currency_gain_value}</td></tr>"


    def __str__(self):
        if self.corresponding_buy is not None:
            return f"Type:{self.gain_type} Amount: {self.disposal_amount_accounted} Currency: {self.currency}" + " Date Acquired: " + str(
                self.corresponding_buy.date.strftime(DATE_FORMAT)) + " Date Sold: " + str(
                self.date_sold.strftime(DATE_FORMAT)) + " Location of buy: " + str(
                self.corresponding_buy.exchange) + " Location of sell: " + str(
                self.sold_location) + " Proceeds in GBP: " + str(
                self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
                self.fee_value_gbp) + " Gain/Loss in GBP: " + str(self.native_currency_gain_value)
        else:
            return f"Type:{self.gain_type} Amount: {self.disposal_amount_accounted} Currency: {self.currency}" + " Date Acquired: " + " Date Sold: " + str(
                self.date_sold.strftime(DATE_FORMAT)) + " Location of buy: " + " Location of sell: " + str(
                self.sold_location) + " Proceeds in GBP: " + str(
                self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
                self.fee_value_gbp) + " Gain/Loss in GBP: " + str(self.native_currency_gain_value)


def read_csv_into_trade_list(csv_filename):
    try:
        with open(csv_filename, encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Ignore Header Row
            trades = [Trade.from_csv(row) for row in list(reader) if
                      row[TradeColumn.TRADE_TYPE] in TRADE_TYPES_TO_IMPORT]
            trades.sort(key=lambda trade: trade.date)

            for i in range(0, len(trades)):
                trade = trades[i]
                [logger.warning(f"TRADE Warning  - Possible Duplicates:{trade} and {trade2}.") for trade2 in trades if
                 trade.is_possible_duplicate(trade2) and trades.index(trade2) != i]

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

            fees = [Fee.from_csv(row) for row in list(reader) if row[FeeColumn.TRADE_TYPE] in FEE_TYPES_TO_IMPORT]
            fees.sort(key=lambda fee: fee.date)
            logger.debug(f"Loaded {len(fees)} fees from {csv_filename}.")

            for i in range(0, len(fees)):
                fee = fees[i]
                [logger.warning(f"FEE Warning - Possible Duplicates:{fee} and {fee2}.") for fee2 in fees if
                 fee.is_possible_duplicate(fee2) and fees.index(fee2) != i]

            [logger.warning(f"Unusual large fee amount of {fee.fee_value_gbp_at_trade} in fee: {fee}") for fee in fees
             if fee.fee_value_gbp_at_trade > 99]

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


def assign_fees_to_trades(trades: List[Trade], fees: List[Fee]):
    for fee in fees:
        matching_trades = [t for t in trades if fee_matches_trade(fee, t)]
        if len(matching_trades) == 0:
            logger.warning(f"Could not find trade for fee {fee}.")
        elif len(matching_trades) > 1:
            logger.error(f"Found multiple trades for fee {fee}.")
            trade = matching_trades[0]
            trade.fee = fee
            trade.account_for_fee_in_cost()
        else:
            trade = matching_trades[0]
            trade.fee = fee
            trade.account_for_fee_in_cost()


def within_tax_year(trade, tax_year):
    tax_year_start = datetime(tax_year - 1, 4, 6)  # 2018 taxyear is 2017/18 taxyear and starts 06/04/2017
    tax_year_end = datetime(tax_year, 4, 6)  # This needs to be 6 as 05.06.2018 < 05.06.2018 12:31
    return tax_year_start <= trade.date < tax_year_end


def currency_match(disposal, corresponding_buy):
    return disposal.sell_currency == corresponding_buy.buy_currency


def gain_from_pair(disposal, corresponding_buy, gain_type):
    uncapped_amount = corresponding_buy.unaccounted_buy_amount / disposal.unaccounted_sell_amount
    disposal_amount_accounted_for = min(corresponding_buy.unaccounted_buy_amount, disposal.unaccounted_sell_amount)
    logger.debug(
        f"Matched {disposal_amount_accounted_for * 100 / disposal.unaccounted_sell_amount}% of \n\t{disposal} with \n\t{corresponding_buy}.")
    gain = Gain(gain_type, disposal_amount_accounted_for, disposal, corresponding_buy)
    disposal.unaccounted_sell_amount -= disposal_amount_accounted_for
    corresponding_buy.unaccounted_buy_amount -= disposal_amount_accounted_for
    return gain


def calculate_day_gains_fifo(trade_list):
    condition = lambda disposal, corresponding_buy: \
        disposal.date.date() == corresponding_buy.date.date()
    return calculate_fifo_gains(trade_list, condition, GainType.DAY_FIFO)


def bnb_condition(disposal, corresponding_buy):
    return disposal.date.date() < corresponding_buy.date.date() <= (disposal.date + BNB_TIME_DURATION).date()


def calculate_bnb_gains_fifo(trade_list):
    return calculate_fifo_gains(trade_list, bnb_condition, GainType.BNB_FIFO)


def calculate_future_gains_fifo(trade_list):
    condition = lambda disposal, corresponding_buy: \
        disposal.date.date() < corresponding_buy.date.date()
    return calculate_fifo_gains(trade_list, condition, GainType.FUTURE_FIFO)


def calculate_fifo_gains(trade_list, trade_within_date_range, gain_type):
    gains = []
    for disposal in trade_list:
        if disposal.is_viable_sell():
            for corresponding_buy in trade_list:
                if currency_match(disposal,
                                  corresponding_buy) and corresponding_buy.unaccounted_buy_amount > 0 and trade_within_date_range(
                    disposal, corresponding_buy) and disposal.is_viable_sell():
                    calculated_gain = gain_from_pair(disposal, corresponding_buy, gain_type)
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

            if number_of_shares_in_pool != 0:
                average_cost = pool_of_actual_cost / number_of_shares_in_pool

                gain = Gain(GainType.AVERAGE, number_of_shares_to_sell, trade, average_cost=average_cost)
                gain_list.append(gain)
                # then update holding
                number_of_shares_in_pool -= number_of_shares_to_sell
                pool_of_actual_cost -= gain.cost_basis

                trade.unaccounted_sell_amount = unaccounted_for_amount

    return gain_list


def calculate_104_holding_gains(trade_list: List[Trade]):
    non_native_asset_list = []
    for trade in trade_list:
        if trade.sell_currency not in non_native_asset_list and trade.sell_currency is not NATIVE_CURRENCY:
            non_native_asset_list.append(trade.sell_currency)

    gains = []
    for asset in non_native_asset_list:
        gains.extend(calculate_104_gains_for_asset(asset, trade_list))

    return gains


def calculate_unaccounted_disposal_gains(trade_list: List[Trade]):
    gains = []
    for trade in trade_list:
        if trade.sell_currency != NATIVE_CURRENCY and trade.unaccounted_sell_amount != 0:
            logger.warning(
                f"Trade: {trade} has unaccounted disposal of {trade.unaccounted_sell_amount} {trade.sell_currency}  which will be given cost basis 0")
            g = Gain(GainType.UNACCOUNTED, trade.unaccounted_sell_amount, trade)
            gains.append(g)

    return gains


def calculate_capital_gain(trade_list: List[Trade]):
    gains = []
    gains.extend(calculate_day_gains_fifo(trade_list))
    gains.extend(calculate_bnb_gains_fifo(trade_list))
    gains.extend(calculate_104_holding_gains(trade_list))

    # Where disposal is not fully accounted for, need to do FIFO on later trades(after all 104 holdings have been done)
    #   see https://bettingbitcoin.io/cryptocurrency-uk-tax-treatments

    gains.extend(calculate_future_gains_fifo(trade_list))
    gains.extend(calculate_unaccounted_disposal_gains(trade_list))

    return gains


def output_to_html(gains: List[Gain], template_file, html_output_filename):

    relevant_capital_gains = [g for g in gains if within_tax_year(g.disposal_trade, TAX_YEAR)]
    relevant_capital_gains.sort(key=lambda g: g.date_sold)
    relevant_trades = []
    [relevant_trades.append(g.disposal_trade) for g in gains if within_tax_year(g.disposal_trade,
                                                                                TAX_YEAR) and g.disposal_trade not in relevant_trades]

    day_gains = [g for g in relevant_capital_gains if g.gain_type == GainType.DAY_FIFO]
    DAY_GAINS = sum([g.native_currency_gain_value for g in day_gains])
    bnb_gains = [g for g in relevant_capital_gains if g.gain_type == GainType.BNB_FIFO]
    BNB_GAINS = sum([g.native_currency_gain_value for g in bnb_gains])
    avg_gains = [g for g in relevant_capital_gains if g.gain_type == GainType.AVERAGE]
    AVG_GAINS = sum([g.native_currency_gain_value for g in avg_gains])
    future_gains = [g for g in relevant_capital_gains if g.gain_type == GainType.FUTURE_FIFO]
    FUTURE_GAINS = sum([g.native_currency_gain_value for g in future_gains])
    unaccounted_gains = [g for g in relevant_capital_gains if g.gain_type == GainType.UNACCOUNTED]
    UNACCOUNTED_GAINS = sum([g.native_currency_gain_value for g in unaccounted_gains])

    TOTAL_PROCEEDS = sum([g.proceeds for g in relevant_capital_gains])
    TOTAL_COSTS = sum([g.cost_basis for g in relevant_capital_gains])
    TOTAL_GAINS = sum([g.native_currency_gain_value for g in relevant_capital_gains])
    DISPOSAL_FEE_VALUE = sum([g.fee_value_gbp for g in relevant_capital_gains])



    print(f"Total gain for tax year {TAX_YEAR}: {TOTAL_GAINS}.")

    fin = open(template_file)
    contents = fin.read()

    fin.close()

    GAINS = ""
    for gain in relevant_capital_gains:
        GAINS += (gain.html_format())

    out = contents.format(TAX_YEAR_START=TAX_YEAR - 1,
                          TAX_YEAR_END=TAX_YEAR,
                          NATIVE_CURRENCY=NATIVE_CURRENCY,
                          INPUT_TRADE_CSV=TRADE_CSV,
                          NUMBER_OF_DISPOSALS=len(relevant_trades),
                          DAY_GAINS=DAY_GAINS,
                          BNB_GAINS=BNB_GAINS,
                          AVG_GAINS=AVG_GAINS,
                          FUTURE_GAINS=FUTURE_GAINS,
                          UNACCOUNTED_GAINS=UNACCOUNTED_GAINS,
                          DISPOSAL_FEE_VALUE=DISPOSAL_FEE_VALUE,
                          TOTAL_PROCEEDS=TOTAL_PROCEEDS,
                          TOTAL_COSTS=TOTAL_COSTS,

                          TOTAL_GAINS=TOTAL_GAINS,


                          GAINS_HEADING=Gain.heading,
                          GAINS=GAINS)
    print(out)
    file = open(html_output_filename, "w+")
    file.write(out)


def main():
    trades = read_csv_into_trade_list(TRADE_CSV)
    fees = read_csv_into_fee_list(FEE_CSV)
    assign_fees_to_trades(trades, fees)
    total_gains = calculate_capital_gain(trades)

    output_to_html(total_gains, "output_template.html", "tax-report.html")


if __name__ == "__main__":
    main()
