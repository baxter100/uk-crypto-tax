# This code is licensed under the GNU General Public License v3.0. Please leave this notice in the code if you choose to redistibute this file redistribute this file.

import os

import csv
from datetime import datetime, timedelta

import uuid
import copy

import json

with open("config.json") as json_data_file:
    configs = json.load(json_data_file)

trade_csv = configs["tradelist_filename"]
fee_csv = configs["fee_list_filename"]
trade_indices = configs["trade_csv_indices"]
fee_indices = configs["fee_csv_indices"]
trade_floats = configs["trade_floats"]
trade_strings = configs["trade_strings"]

##### Tax Facts

annual_untaxable_allowance = {2015: 11000, 2016: 11100, 2017: 11100, 2018: 11300, 2019: 11700, 2020: 12300}


def taxyearstart(taxyear):
    ### Get's beginning of tax year e.g.
    ### 2018 taxyear is 2017/18 taxyear and starts 06/04/2017
    return datetime(taxyear - 1, 4, 6)


def taxyearend(taxyear):
    return datetime(taxyear, 4, 6)  # This needs to be 6 as 05.06.2018 < 05.06.2018 12:31


def taxdatecheck(trade, taxyear):
    ### Checks trade is in correct year
    if taxyearstart(taxyear) <= trade.date <= taxyearend(taxyear):
        return True


# # TODO: Trades are specified by their trade number and then recovered from their position in trading list
# # TODO: and then the index is used to determine stuff, but we should just use trades --- all this trading.trades[x] should just be x.


#### List of possible fiat currencies
fiat_list = ["GBP", "EUR"]


##### Fifo calculations


def gainpair(first_trade, second_trade):
    ### Calculate gain when two trades have been matched
    # This should be in trading class I think.  x and y should be changed to trades rather than indexes of the trades
    # Given a pair of trades, returns the capital gain
    if second_trade.buy >= first_trade.sell:
        if first_trade.buy_value_gbp == 0:  # necessary because of gifts/tips
            return first_trade.sell_value_gbp - second_trade.native_cost_per_coin * first_trade.sell
        else:
            return first_trade.buy_value_gbp - second_trade.native_cost_per_coin * first_trade.sell

    else:
        if first_trade.buy_value_gbp == 0:  # necessary because of gifts/tips
            return first_trade.sell_value_gbp * second_trade.buy / first_trade.sell - \
                   second_trade.native_cost_per_coin * second_trade.buy
        else:
            return first_trade.buy_value_gbp * second_trade.buy / first_trade.sell - \
                   second_trade.native_cost_per_coin * second_trade.buy


def addgainsfifo(x, y, taxyear):  # adds gains from pair to total if tax year is correct
    if taxdatecheck(x, taxyear):
        return gainpair(x, y)
    else:
        return 0


def fifoupdatetradelist(disposal, corresponding_buy):  # updates trade amounts
    if corresponding_buy.buy >= disposal.sell:

        corresponding_buy.buy = corresponding_buy.buy - disposal.sell
        disposal.sell = 0
        disposal.buy_value_gbp = disposal.buy_value_gbp - (
                disposal.valueofsalepercoin * corresponding_buy.buy)
    else:

        disposal.sell = disposal.sell - corresponding_buy.buy
        disposal.buy_value_gbp = disposal.buy_value_gbp - (
                disposal.valueofsalepercoin * corresponding_buy.buy)
        corresponding_buy.buy = 0


### Matching conditions

def datematch(x, y):
    if x.date.day == y.date.day and x.date.month == y.date.month and x.date.year == y.date.year:  # if the days are the same, there must be a better way!:
        return True


def currencymatch(trade, buy_trade):
    # Matches if proceeds from trade come from buy_trade
    if trade.currency_sell == buy_trade.currency_buy and buy_trade.buy != 0:
        return True


def viablesellcurrency(trade):
    if trade.currency_sell not in fiat_list and trade.currency_sell != "" and trade.sell != 0:
        return True


def viabledaymatch(x, y):
    return datematch(x, y) and currencymatch(x, y)


def viablebnbmatch(x, y):
    if currencymatch(x, y) and y.date > x.date >= y.date - timedelta(
            days=30):  # May need to adjust this
        return True


#### Tax Reporting Part


class Trade:
    split = None

    def __init__(self, trade_row, trade_number
                 ):

        self.id = uuid.uuid4()

        for x in trade_floats:  # "-" in gift trades weren't able to be converted in floats so was messing things up
            if trade_row[trade_indices[x]] == "-":
                trade_row[trade_indices[x]] = 0

        self.buy = float(trade_row[trade_indices["buy"]])
        self.currency_buy = trade_row[trade_indices["currency_buy"]]
        self.currency_sell = trade_row[trade_indices["currency_sell"]]
        self.sell = float(trade_row[trade_indices["sell"]])
        self.date = datetime.strptime(trade_row[trade_indices["date"]], "%d.%m.%Y %H:%M")
        self.sell_value_gbp = float(trade_row[trade_indices["sell_value_gbp"]])
        self.sell_value_btc = float(trade_row[trade_indices["sell_value_btc"]])
        self.buy_value_gbp = float(trade_row[trade_indices["buy_value_gbp"]])
        self.buy_value_btc = float(trade_row[trade_indices["buy_value_btc"]])
        self.exchange = trade_row[trade_indices["exchange"]]
        self.trade_number = trade_number

        for attr in trade_floats:
            if type(getattr(self, attr)) is not float:
                raise ValueError(attr + " should be float")
        for attr in trade_strings:
            if type(getattr(self, attr)) is not str:
                raise ValueError(attr + " should be string")

        if self.buy == 0:
            self.costbasisGBPpercoin = 0
        else:
            self.costbasisGBPpercoin = self.sell_value_gbp / self.buy
        if self.sell == 0:
            self.valueofsalepercoin = 0
        else:
            self.valueofsalepercoin = self.buy_value_gbp / self.sell

    def __str__(self):
        return "Trade: " + str(self.buy) + str(self.currency_buy) + " -> " + str(self.sell) + str(
            self.currency_sell) + " | GBP:" + str(self.sell_value_gbp) + ", " + str(self.date)


class TradingHistory:

    def __init__(self, trade_csv, fee_csv=None):

        self.trade_csv = trade_csv
        self.fee_csv = fee_csv

        self.unmodified_trades = []  # unmodified list of trades
        self.modified_trades = []  # copy that gets modified as calculation runs
        self.crypto_list = []  # list of cryptos involved in trade

        with open(self.trade_csv, encoding='utf-8') as f:
            reader = csv.reader(f)  # create a 'csv reader' from the file object
            datalist = list(reader)  # create a list from the reader

            datalist.pop(0)  # removes first line of data list which is headings
            datalist = datalist[::-1]  # inverts data list to put in time order

            self.datalist = datalist

        self.append_trades()
        self.populate_crypto_list()

    def populate_crypto_list(self):
        for trade in self.unmodified_trades:

            if trade.currency_buy not in self.crypto_list and trade.currency_buy not in fiat_list:
                self.crypto_list.append(trade.currency_buy)
            if trade.currency_sell not in self.crypto_list and trade.currency_sell not in fiat_list:
                self.crypto_list.append(trade.currency_sell)

    def append_trades(self):

        for trade_row in self.datalist:
            trade_number = self.datalist.index(trade_row)
            tr = Trade(trade_row, trade_number)

            self.unmodified_trades.append(tr)

        if self.fee_csv is not None:
            with open(self.fee_csv, encoding='utf-8') as fees:
                reader = csv.reader(fees)  # create a 'csv reader' from the file object
                feelist = list(reader)  # create a list from the reader

            feelist.pop(0)  # removes first line of data list which is headings
            feelist = feelist[::-1]  # inverts data list to put in time order

            for fee in feelist:
                for trade in self.unmodified_trades:
                    if trade.date == datetime.strptime(fee[fee_indices["date"]],
                                                       "%d.%m.%Y %H:%M") and trade.buy == float(
                        fee[fee_indices["buy"]]) and trade.sell == float(fee[fee_indices["sell"]]):
                        trade.fee_value_gbp = float(fee[fee_indices["fee_value_gbp"]])
                        trade.currency_fee = fee[fee_indices["currency_fee"]]
                        trade.fee = float(fee_indices["fee"])
                        break

        # Finally make a copy
        self.modified_trades = copy.deepcopy(self.unmodified_trades)  # self.tradelist is the unmodified copy


############


class Gain:

    def __init__(self, trade):

        self.amount = trade.sell
        self.currency = trade.currency_sell
        self.date_acquired = datetime.strptime("01.01.0001 00:00", "%d.%m.%Y %H:%M")
        self.date_sold = trade.date
        self.bought_location = "?"
        self.sold_location = trade.exchange
        if trade.buy_value_gbp == 0:  # It is necessary to use sell value when calculating gains on gifts
            self.proceeds = trade.sell_value_gbp
        else:
            self.proceeds = trade.buy_value_gbp  # Proceeds are always calculated here using buy value!
        # These values begin at 0 but will be updated
        self.cost_basis = 0
        self.gain_loss = 0
        self.sell_number = trade.trade_number
        if hasattr(trade, "fee_value_gbp"):
            self.fee = trade.fee_value_gbp
        else:
            self.fee = 0

    def __str__(self):
        return "Amount: " + str(self.amount) + " Currency: " + str(self.currency) + " Date Acquired: " + str(
            self.date_acquired.strftime("%d.%m.%Y %H:%M")) + " Date Sold: " + str(
            self.date_sold.strftime("%d.%m.%Y %H:%M")) + " Location of buy: " + str(
            self.bought_location) + " Location of sell: " + str(self.sold_location) + " Proceeds in GBP: " + str(
            self.proceeds) + " Cost Basis in GBP: " + str(self.cost_basis) + " Fee in GBP: " + str(
            self.fee) + " Gain/Loss in GBP: " + str(self.gain_loss)

    def __repr__(self):
        return str(self)

    def print_gain_html(self):
        return '    </td><td>' + str(self.proceeds) + '    </td><td>' + str(self.cost_basis) + '    </td><td>' + str(
            self.fee) + '    </td><td>' + str(self.gain_loss) + '    </td><td>' + str(
            self.date_sold.strftime("%d.%m.%Y %H:%M")) + '    </td><td>' + str(self.currency) + '    </td><td>' + str(
            self.amount) + '    </td><td>' + str(self.sold_location) + '    </td><td>' + str(self.sell_number)


class GainHistory:

    def __init__(self, trade_history, taxyear):
        self.trade_history = trade_history
        self.taxyear = taxyear

        self.gain_list = []
        self.sortedgainlist = []  # only include gains in tax year, is rounded and then sorted in chronological order

    def append_gain_list(self):

        # for x in range(0, len(self.trade_history.datalist)):
        #### Use the unmodified copy here to avoid future complication
        for trade in self.trade_history.unmodified_trades:
            if viablesellcurrency(trade):
                ga = Gain(trade)
                self.gain_list.append(ga)

    def __repr__(self):
        return str(self)

    def updatetaxcostbasis(self, trade1, trade2):
        # x is from modified trades, and probably y?
        # :TODO change indexing to actual trades (then in method call)
        #   costbasisGBPpercoin should be a trade attribute?
        #  :TODO where trades are used in methods, check they come from correct lists (probably modififed trades)

        gain1 = self.mapfromtradetogain(trade1)

        if trade2.buy >= trade1.sell:
            gain1.cost_basis += trade2.native_cost_per_coin * trade1.sell
        else:
            gain1.cost_basis += trade2.native_cost_per_coin * trade2.buy

    def addgainvalues(self):
        for gain in self.gain_list:
            gain.gain_loss = gain.proceeds - gain.cost_basis

    def mapfromtradetogain(self, trade):
        for gain in self.gain_list:
            if gain.sell_number == trade.trade_number:
                return gain

    def updatetaxcostbasisavg(self, trade, costbasis):
        self.mapfromtradetogain(trade).cost_basis += costbasis

    def append_sortedgainlist(self):

        for gain in self.gain_list:
            if taxyearstart(self.taxyear) <= gain.date_sold <= taxyearend(self.taxyear):
                for attr, value in gain.__dict__.items():
                    if type(value) is float and attr != "amount":
                        setattr(gain, attr, round(value, 2))

                self.sortedgainlist.append(gain)

        self.sortedgainlist = sorted(self.sortedgainlist, key=lambda gain_list: gain_list.date_sold)

    @staticmethod
    def print_tableheading_html():
        headinglist = ["Proceeds", "Cost Basis", "Fee", "Gain/Loss", "Date Sold", "Currency", "Amount Sold",
                       "Location of Sale", "Number of Sell Trade"]
        a = ''
        for x in headinglist:  ### Makes first line of table the headings

            a += '    </td><td>' + str(x)
        return a

    ### Create tax report list


class DetailedCalculation():
    amount = 0
    currency = 0
    date_acquired = 0
    date_sold = 0
    bought_location = 0
    sold_location = 0
    proceeds = 0
    cost_basis = 0
    gain_loss = 0
    sell_number = 0
    buy_number = 0
    fee = 0
    match_type = 0

    def print_gain_html(self):
        if type(self.date_acquired) == str:
            return '    </td><td>' + str(self.match_type) + '    </td><td>' + str(
                self.proceeds) + '    </td><td>' + str(self.cost_basis) + '    </td><td>' + str(
                self.fee) + '    </td><td>' + str(self.gain_loss) + '    </td><td>' + str(
                self.date_sold.strftime("%d.%m.%Y %H:%M")) + '    </td><td>' + str(
                self.currency) + '    </td><td>' + str(self.amount) + '    </td><td>' + str(
                self.sold_location) + '    </td><td>' + str(self.sell_number) + '    </td><td>' + str(
                self.date_acquired) + '    </td><td>' + str(self.bought_location) + '    </td><td>' + str(
                self.buy_number)
        else:
            return '    </td><td>' + str(self.match_type) + '    </td><td>' + str(
                self.proceeds) + '    </td><td>' + str(self.cost_basis) + '    </td><td>' + str(
                self.fee) + '    </td><td>' + str(self.gain_loss) + '    </td><td>' + str(
                self.date_sold.strftime("%d.%m.%Y %H:%M")) + '    </td><td>' + str(
                self.currency) + '    </td><td>' + str(self.amount) + '    </td><td>' + str(
                self.sold_location) + '    </td><td>' + str(self.sell_number) + '    </td><td>' + str(
                self.date_acquired.strftime("%d.%m.%Y %H:%M")) + '    </td><td>' + str(
                self.bought_location) + '    </td><td>' + str(self.buy_number)


class DetailedHistory:
    gain_list = []
    sortedgainlist = []

    def __init__(self, trade_history, taxyear):
        self.trade_history = trade_history
        self.taxyear = taxyear

    def append_detailed_list(self, x, y):

        d = DetailedCalculation()
        if y.buy >= x.sell:
            d.amount = x.sell
        else:
            d.amount = y.buy
        d.currency = x.currency_sell
        d.date_acquired = y.date
        d.date_sold = x.date
        d.bought_location = y.exchange
        d.sold_location = x.exchange
        if x.buy_value_gbp == 0:
            d.proceeds = x.sell_value_gbp * d.amount / x.sell  # Proceeds are always calculated here using buy value unless the buy value is 0 i.e. for a gift
        else:
            d.proceeds = x.buy_value_gbp * d.amount / x.sell  # Proceeds are always calculated here using buy value!
        if y.buy >= x.sell:
            d.cost_basis = y.native_cost_per_coin * x.sell
        else:
            d.cost_basis = y.native_cost_per_coin * y.buy
        d.gain_loss = d.proceeds - d.cost_basis
        d.buy_number = y
        d.sell_number = x
        d.fee = x.fee_value_gbp
        if viabledaymatch(x, y):
            d.match_type = "day"
        elif viablebnbmatch(x, y):
            d.match_type = "bnb"
        else:
            d.match_type = "?"

        self.gain_list.append(d)

    def append_detailed_list_avg(self, x, costbasis):

        d = DetailedCalculation()
        d.match_type = "avg"
        d.amount = x.sell
        d.currency = x.currency_sell
        d.date_acquired = "N/A"
        d.date_sold = x.date
        d.bought_location = "N/A"
        d.sold_location = x.exchange
        if x.buy_value_gbp == 0:
            d.proceeds = x.sell_value_gbp
        else:
            d.proceeds = self.trade_history.modified_trades[
                x].buy_value_gbp  # Proceeds are always calculated here using buy value!
        d.cost_basis = costbasis
        d.gain_loss = d.proceeds - d.cost_basis
        d.buy_number = "N/A"
        d.sell_number = x
        d.fee = x.fee_value_gbp

        self.gain_list.append(d)

    def append_sortedgainlist(self):

        for z in self.gain_list:
            if taxyearstart(self.taxyear) <= z.date_sold <= taxyearend(self.taxyear):
                for attr, value in z.__dict__.items():
                    if type(value) is float and attr != "amount":
                        setattr(z, attr, round(value, 2))

                self.sortedgainlist.append(z)

        self.sortedgainlist = sorted(self.sortedgainlist, key=lambda gain_list: gain_list.date_sold)

    def print_tableheading_html(self):
        headinglist = ["Match Type", "Proceeds", "Cost Basis", "Fee", "Gain/Loss", "Date Sold", "Currency",
                       "Amount Sold", "Location of Sale", "Number of Sell Trade", "Date Acquired", "Location of Buy",
                       "Number of Matched Buy Trade"]
        a = ''
        for x in headinglist:  ### Makes first line of table the headings

            a += '    </td><td>' + str(x)
        return a


### Calculate gains on day trades using fifo

def fifodays(trade_history, taxyear, gainhistory):
    fifodaytotal = 0
    for trade in trade_history.modified_trades:

        if trade.sell > 0 and viablesellcurrency(trade):
            for earlier_trade in trade_history.modified_trades:
                # begins checking trades to match with from start
                if earlier_trade.trade_number < trade.trade_number:

                    if viabledaymatch(trade, earlier_trade):  # if dates and currencies match appropriately

                        fifodaytotal += addgainsfifo(trade, earlier_trade, taxyear)  # adds gain from this pair to total
                        gainhistory.updatetaxcostbasis(trade, earlier_trade)
                        detailed_tax_list.append_detailed_list(trade, earlier_trade)
                        fifoupdatetradelist(trade, earlier_trade)

    return (fifodaytotal)


### Calculate gains on bnb trades using fifo

def fifobnb(trade_history, gain_history, taxyear):
    fifobnbtotal = 0
    for trade in trade_history.modified_trades:

        if trade.sell > 0 and viablesellcurrency(trade):
            for later_trade in trade_history.modified_trades:
                if later_trade.trade_number > trade.trade_number:
                    if viablebnbmatch(trade, later_trade):
                        fifobnbtotal += addgainsfifo(trade, later_trade,taxyear)  # adds gain from this pair to total
                        gain_history.updatetaxcostbasis(trade, later_trade)
                        detailed_tax_list.append_detailed_list(trade, later_trade)
                        fifoupdatetradelist(trade, later_trade)

    return (fifobnbtotal)


### Calculate gains on trades using 404 holdings rule
def averagecostbasisuptotrade(trade, countervalue, counteramount,trade_history):
    t = 0
    q = 0
    for earlier_trade in trade_history.modified_trades:
        if earlier_trade.trade_number < trade.trade_number:

            if currencymatch(trade, earlier_trade):
                t += earlier_trade.native_cost_per_coin * earlier_trade.buy
                q += earlier_trade.buy
    if q - counteramount == 0:
        return 0
    else:
        return (t - countervalue) / (q - counteramount)


def average_asset(taxyear, asset, trade_history):
    averagetotal = 0
    countervalue = 0
    counteramount = 0
    for trade in trade_history.modified_trades:
        if trade.currency_sell == asset and viablesellcurrency(trade):

            costbasis = averagecostbasisuptotrade(trade, countervalue, counteramount, trade_history) * trade.sell
            taxgains.updatetaxcostbasisavg(trade, costbasis)
            if taxdatecheck(trade,taxyear):
                if trade.buy_value_gbp == 0:  ## Necessary to add this to deal with gifts/tips
                    averagetotal += trade.sell_value_gbp - costbasis
                else:
                    averagetotal += trade.buy_value_gbp - costbasis
                detailed_tax_list.append_detailed_list_avg(trade, costbasis)

            countervalue += costbasis
            counteramount += trade.sell

    return averagetotal


def average(taxyear, trade_history):
    averagetotal = 0
    for asset in trading.crypto_list:
        averagetotal += average_asset(taxyear, asset,trade_history)

    return averagetotal


def sumfees(taxyear,trade_history):
    feetotal = 0
    for trade in trade_history.modified_trades:
        if taxdatecheck(trade, taxyear):
            feetotal += trade.fee_value_gbp

    return feetotal


########## Reporting Section
def printinfo(taxyear,taxpercentage, trade_history):
    annualallowance = annual_untaxable_allowance[taxyear]
    for trade in trade_history.modified_trades:  ### Print warning to contact HMRC
        if trade.sell_value_gbp >= 4 * annualallowance and taxdatecheck(trade, taxyear):
            print("Sale:", trade,
                  " has a sale value of more than four times the annual allowance. If you sell more than four times the annual allowance (£46,800 for 2018/19) of crypto-assets, even if you make a profit of less than the allowance, you have to report this sale to HMRC. You can do this either by registering and reporting through Self Assessment, or by writing to them at: PAYE and Self Assessment, HM Revenue and Customs, BX9 1AS, United Kingdom")

    print("Gain from days: £ ", days, ". Gain from bed and breakfasting: £ ", bnb, ". Gain from 404 Holdings: £ ", avg,
          "Total value of fees paid in GBP: £ ", feetotal, "Total Capital Gains for ", taxyear - 1, "/", taxyear,
          ": £ ", round(days + bnb + avg - feetotal, 2))
    if taxablegain > 0:
        print("Total Taxable Gain for ", taxyear - 1, "/", taxyear, " for 'normal' people: £ ", taxablegain)
    else:
        print("Total Taxable Gain for ", taxyear - 1, "/", taxyear, " for 'normal' people: £ ", 0)

    if totaltax > 0:
        print("Total tax owed at ", taxpercentage, "% tax rate: £ ", totaltax)
    else:
        print("Total tax owed at ", taxpercentage, "% tax rate: £ ", 0)


######### Facts needed for self-assesment
def taxyeardisposalscount(taxyear,gain_history):
    x = 0
    sells = []
    for gain in gain_history.gain_list:
        if taxyearstart(taxyear) <= gain.date_sold <= taxyearend(taxyear) and gain.sell_number not in sells:
            x += 1
            sells.append(gain.sell_number)
    return x


def disposalproceeds(taxyear,gain_history):
    x = 0
    for gain in gain_history.gain_list:
        if taxyearstart(taxyear) <= gain.date_sold <= taxyearend(taxyear):
            x += gain.proceeds
    return round(x, 2)


def costs(taxyear,gain_history):  # Note this should include exchange fees!
    x = 0
    for gain in gain_history.gain_list:
        if taxyearstart(taxyear) <= gain.date_sold <= taxyearend(taxyear):
            x += gain.cost_basis
    x += sumfees(taxyear)
    return round(x, 2)


class htmloutput():


    def __init__(self,taxyear,trade_csv,trade_history,tax_percentage):
        self.trade_history =trade_history
        self.taxyear = taxyear
        self.trade_csv = trade_csv
        self.tax_percentage = tax_percentage


    def simpletaxreport(self):
        f = open(str(self.taxyear - 1) + '-' + str(self.taxyear) + '_simpletaxreport.html', 'w')

        message = str(str('\n'.join(self.html_table(taxgains))))

        f.write(message)
        f.close()

    def html_table(self, gain_history):
        annualallowance = annual_untaxable_allowance[self.taxyear]
        yield '<h2>List of sales with calculations </h2>'
        yield '<h3>Values for Proceeds, Cost basis, fee and gain/loss are given in GBP </h3>'
        yield '<h3>Calcuated from file:' + self.trade_csv + '</h3>'
        for trade in self.trade_history.unmodified_trade_list:  ### Print warning to contact HMRC
            if trade.sell_value_gbp >= 4 * annualallowance and taxyearstart(self.taxyear) <= \
                    trade.date <= taxyearend(self.taxyear):
                yield "<h3>Sale:" + str(
                    trade) + " has a sale value of more than four times the annual allowance. If you sell more than four times the annual allowance (&pound45,200 for 2017/18) of crypto-assets, even if you make a profit of less than the allowance, you have to report this sale to HMRC. You can do this either by registering and reporting through Self Assessment, or by writing to them at: PAYE and Self Assessment, HM Revenue and Customs, BX9 1AS, United Kingdom</h3>"
        yield "<h3> Number of Disposals: " + str(number_of_disposals) + ". Disposal Proceeds: " + str(
            disposalproceeds(self.taxyear)) + ". Allowable Costs: " + str(costs(self.taxyear)) + "</h3>"
        yield "<h3>Gain from days: &pound " + str(days) + ". Gain from bed and breakfasting: &pound " + str(
            bnb) + ". Gain from 404 Holdings: &pound " + str(avg) + " Total value of fees paid in GBP: &pound " + str(
            feetotal) + " Total Capital Gains for " + str(self.taxyear - 1) + "/" + str(self.taxyear) + ": &pound " + str(
            round(days + bnb + avg - feetotal, 2)) + "</h3>"
        if taxablegain > 0:
            yield "<h3>Total Taxable Gain for " + str(self.taxyear - 1) + "/" + str(
                self.taxyear) + " for 'normal' people: &pound " + str(taxablegain) + "</h3>"
        else:
            yield "<h3>Total Taxable Gain for " + str(self.taxyear - 1) + "/" + str(
                self.taxyear) + " for 'normal' people: &pound " + str(0) + "</h3>"

        if totaltax > 0:
            yield "<h3>Total tax owed at " + str(self.tax_percentage) + "% tax rate: &pound " + str(totaltax) + "</h3>"
        else:
            yield "<h3>Total tax owed at " + str(self.tax_percentage) + "% tax rate: &pound " + str(0) + "</h3>"
        yield '<p>Note: Where trades are split over multiple entries in the detailed calculations, the fees given are duplicated</p>'

        yield '<table>'
        yield '  <tr><td>'
        yield gain_history.print_tableheading_html()

        for gain in gain_history.sortedgainlist[::-1]:
            yield '  <tr><td>'

            yield gain.print_gain_html()
        yield '</table>'

    def detailedtaxreport(self):
        f = open(str(self.taxyear - 1) + '-' + str(self.taxyear) + '_detailedtaxreport.html', 'w')

        message = str(str('\n'.join(self.html_table(detailed_tax_list))))

        f.write(message)
        f.close()


########################## Checksa

def check(taxyear,trade_history,gain_history,total_gain):
    x = 0
    for gain in gain_history.gain_list:
        if taxyearstart(taxyear) <= gain.date_sold <= taxyearend(taxyear):
            x += gain.gain_loss
    x -= sumfees(taxyear,trade_history)
    if round(x, 2) == round(totalgain, 2):
        print("Well done!")
    else:
        print("Gain Loss total adds up to ", x, " While the calcuated gain is: ", totalgain)

    x = 0
    for z in range(0, len(detailed_tax_list.gain_list)):
        if taxyearstart(taxyear) <= detailed_tax_list.gain_list[z].date_sold <= taxyearend(taxyear):
            x += detailed_tax_list.gain_list[z].gain_loss
    x -= sumfees(taxyear,trade_history)
    if round(x, 2) == round(totalgain, 2):
        print("Well done!")
    else:
        print("Detailed Gain Loss total adds up to ", x, " While the calcuated gain is: ", totalgain)


def checkdetailed(taxyear):
    daycheck = 0
    bnbcheck = 0
    avgcheck = 0
    for z in range(0, len(detailed_tax_list.gain_list)):
        if taxyearstart(taxyear) <= detailed_tax_list.gain_list[z].date_sold <= taxyearend(taxyear):
            if detailed_tax_list.gain_list[z].match_type == "day":
                daycheck += detailed_tax_list.gain_list[z].gain_loss
            if detailed_tax_list.gain_list[z].match_type == "bnb":
                bnbcheck += detailed_tax_list.gain_list[z].gain_loss
            if detailed_tax_list.gain_list[z].match_type == "avg":
                avgcheck += detailed_tax_list.gain_list[z].gain_loss
    print("daycheck = ", daycheck, "bnbcheck = ", bnbcheck, "avgcheck = ", avgcheck)


if __name__ == "main":

    inputtaxpercentage = float(
        input('Enter the percentage of tax you pay on capital gains (https://www.gov.uk/capital-gains-tax/rates): '))

    inputtaxyear = int(input('Enter the year you want to calculate tax for (e.g. 2018 for 2017/2018): '))

    ### Create trade list

    if fee_csv in os.listdir(os.getcwd()):
        trading = TradingHistory(trade_csv, fee_csv)
    else:
        trading = TradingHistory(trade_csv)

    # Calculate gains
    taxgains = GainHistory(trading.datalist, inputtaxyear)

    taxgains.append_gain_list()

    detailed_tax_list = DetailedHistory(inputtaxyear)
    ######Calculating Section
    annualallowance = annual_untaxable_allowance[inputtaxyear]
    days = round(fifodays(trading), 2)
    bnb = round(fifobnb(inputtaxyear), 2)
    avg = round(average(inputtaxyear), 2)
    feetotal = round(sumfees(inputtaxyear), 2)
    totalgain = round(days + bnb + avg - feetotal, 2)
    taxablegain = round(totalgain - annualallowance, 2)
    totaltax = taxablegain * inputtaxpercentage / 100

    printinfo(inputtaxyear)
    #
    # ################# These have to be done after calculation runs
    #
    taxgains.addgainvalues()
    detailed_tax_list.append_sortedgainlist()
    taxgains.append_sortedgainlist()
    number_of_disposals = taxyeardisposalscount(inputtaxyear)
    print("Number of Disposals =", number_of_disposals, ". Disposal Proceeds = ", disposalproceeds(inputtaxyear),
          ". Allowable Costs = ", costs(inputtaxyear))

    htmlout = htmloutput()

    htmlout.simpletaxreport()

    htmlout.detailedtaxreport()
    check(inputtaxyear)

    checkdetailed(inputtaxyear)
