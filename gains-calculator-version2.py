import csv
from datetime import datetime, date, time, timedelta

import uuid
import random
import copy

class Trade:	
	def __init__(self, buy, cbuy, sell, csell, date, bexrate, sexrate,ex):
		self.id = uuid.uuid4()
		self.smatched = False
		self.bmatched = False
		self.split = None
		self.buy = buy
		self.currency_buy = cbuy
		self.currency_sell = csell
		self.sell = sell #these were being messed up by "-" appearing in the "gift" trades so I've changed them to 0 in the csv file
		self.date = date
		self.buy_ex_rate_gbp = bexrate
		self.sell_ex_rate_gbp = sexrate
		self.exchange = ex
	
	def buy_value_gbp(self):
		return self.buy * self.buy_ex_rate_gbp

	def sell_value_gbp(self):
		return self.sell * self.sell_ex_rate_gbp 

	def costbasisGBPpercoin(self):
		return self.sell_value_gbp()/self.buy if self.buy else 0

	def valueofsalepercoin(self):
		return self.buy_value_gbp()/self.sell if self.sell else 0

	def __str__(self):
		return "Trade: " + str(self.buy) + self.currency_buy + " <- " + str(self.sell) + self.currency_sell + " SVGBP " + str(self.sell_value_gbp()) +  " BVGBP " + str(self.buy_value_gbp()) +  " CBPC " + str(self.costbasisGBPpercoin()) +  " VSPC " + str(self.valueofsalepercoin())  +  " srate " + str(self.sell_ex_rate_gbp) +  " srate " + str(self.buy_ex_rate_gbp)


class TradingHistory:
	trades = []
	def load_trades_from_csv(self,filename):
		try:
			with open( filename ) as f:
				reader = csv.reader(f)     # create a 'csv reader' from the file object
				datalist = list( reader )  # create a list from the reader 
		except Exception as e:
			raise
			datalist = []
		return datalist
	def append_cointrackingcsv_trade_list(self,filename="fifo-day-test.csv"):
		datalist = self.load_trades_from_csv(filename)
		datalist.pop(0) #removes first line of data list which is headings
		datalist=datalist[::-1] #inverts data list to put in time order
		
		for t in datalist:
			for x in [6,8,9]: #"-" in gift trades weren't able to be converted in floats so was messing things up
				if t[x]=="-":
					t[x]=0

			bexrate = 0 if float(t[2])==0 else float(t[5])/float(t[2])
			sexrate = 0 if float(t[6])==0 else float(t[9])/float(t[6])
			self.trades.append(Trade(float(t[2]), t[3], float(t[6]), t[7], datetime.strptime(t[13], "%d.%m.%Y %H:%M"), bexrate, sexrate, t[11]))

	def count(self):
		return len(self.trades)


class TaxItem:
	def __init__(self, sellTrade, matchType):
		self.id = uuid.uuid4()
		self.sTrade = sellTrade
		self.matchType = matchType
		self.sTrade.smatched = True

	def taxyearstart(self, taxyear):
		return datetime(taxyear-1,4,6)

	def taxyearend(self, taxyear):
		return datetime(taxyear,4,5)

	def taxable(self, taxyear):
		return self.gain() if self.taxyearstart(taxyear)<=self.sTrade.date<= self.taxyearend(taxyear) else 0

class TaxSellBuyPair(TaxItem):
	def __init__(self, buyTrade, sellTrade, matchType):
		super().__init__(sellTrade, matchType)

		#### bTrade.buy and sTrade.sell are equal for all the taxSellBuyPairs
		self.bTrade = buyTrade
		self.bTrade.bmatched = True
        
	def gain(self): #Given a pair of trades, returns the capital gain
		#### bTrade.buy and sTrade.sell are equal for all the taxSellBuyPairs
		return self.sTrade.buy_value_gbp() - self.bTrade.costbasisGBPpercoin()* self.bTrade.buy
	
	def __str__(self):
		return self.matchType + " PAIR \n -" + str(self.sTrade) +" \n -" +  str(self.bTrade) +" \n - Gain pair " +  str(self.taxable(2017))


class TaxHoldings(TaxItem):
	def __init__(self, sellTrade, holdings):
		super().__init__(sellTrade, "taxHoldings")
		self.holdings = copy.deepcopy(holdings)

	def gain(self): #Given a pair of trades, returns the capital gain
		return self.sTrade.buy_value_gbp() - self.holdings.averageValue * self.sTrade.sell
	def __str__(self):
		return "Tax Holdings \n -" + str(self.sTrade) +" \n -" +  str(self.holdings) +" \n - Gain pair " +  str(self.taxable(2017))


class CurrencyHoldings:
	def __init__(self, currency):
		self.currency = currency
		self.holdings = 0
		self.averageValue = 0

	def addCoins(self, trade):
		if trade.currency_buy!=self.currency:
			print("WARNING: Adding coins of the type ", trade.currency_buy, " to the holdings in ", self.currency)
			return
		totalCurrentValue = self.holdings * self.averageValue
		totalCurrentValue += trade.sell_value_gbp()
		self.holdings += trade.buy
		self.averageValue = totalCurrentValue/self.holdings

	def subtractCoins(self, trade):
		if trade.currency_sell!=self.currency:
			print("WARNING: Substracting coins of the type ", trade.currency_sell, " from the holdings in ", self.currency)
			return
		self.holdings -= trade.sell
		if self.holdings < 0:
			print("WARNING: Holdings in ", self.currency, " are in negative numbers")
		return TaxHoldings(trade, self)

	def __str__(self):
		return self.currency + " HOLDINGS:\nHoldings " + str(self.holdings) + "    Average Value: " + str(self.averageValue)

class GlobalHoldings():
	def __init__(self):
		self.holdings = {}
		
	def addCoins(self, trade):
		if trade.currency_buy == "GBP" or trade.bmatched:
			return
		if trade.currency_buy not in self.holdings:
			self.holdings[trade.currency_buy] = CurrencyHoldings(trade.currency_buy)

		self.holdings[trade.currency_buy].addCoins(trade)
	def subtractCoins(self, trade):
		if trade.currency_sell == "GBP" or trade.smatched:
			return None
		if trade.currency_sell not in self.holdings:
			self.holdings[trade.currency_sell] = CurrencyHoldings(trade.currency_sell)

		return self.holdings[trade.currency_sell].subtractCoins(trade)

	def processTrade(self, trade):
		self.addCoins(trade)
		return self.subtractCoins(trade)


class FIFOStrategy:
	def __init__(self, trades):
		self.trades = trades
		self.sTrade = 0
		self.bTrade = 0
		self.done = False
		self.condition = None

	def init(self):
		self.sTrade = 0
		self.bTrade = 0
		self.done = False

	def currentPrint(self):
		return str(self.sTrade) + " - " + str(self.bTrade) + " |\n -" + str(self.trades[self.sTrade]) +" \n -" +  str(self.trades[self.bTrade])

	def current(self):
		return (self.trades[self.sTrade],self.trades[self.bTrade])

	def matchable(self):
		sTrade = self.trades[self.sTrade]
		bTrade = self.trades[self.bTrade]

		if bTrade.bmatched or sTrade.smatched: return False
		if sTrade.currency_sell=="GBP" or sTrade.currency_sell=="": return False  
		if bTrade.buy==0 or bTrade.currency_buy!=sTrade.currency_sell: return False
		if callable(self.condition) and not self.condition(*self.current()): return False 
		return True

	def next(self):
		## Here we calculate the values for the next round
		self.done = self.sTrade==len(self.trades)-1 and self.bTrade==self.sTrade
		if self.bTrade == len(self.trades)-1:
			self.sTrade += 1
			self.bTrade = 0
		else: 
			self.bTrade += 1

	def nextSell(self):
		self.done = self.sTrade>=len(self.trades)-1 and self.sTrade>=len(self.trades)-1 
		self.sTrade += 1
		self.bTrade = 0

class TaxCalculator:
	def __init__(self, tradingHistory):
		self.th = tradingHistory
		self.matches = []
		self.trades = copy.deepcopy(self.th.trades)
		self.strategy = FIFOStrategy(self.trades)
		self.holdings = GlobalHoldings()

	def sameDay(self, sTrade, bTrade):
		return sTrade.date.date() == bTrade.date.date()
	
	def within30Range(self, sTrade, bTrade):
		return sTrade.date.date() < bTrade.date.date() and bTrade.date <= (sTrade.date + timedelta(days=30))

	def calculateUKTax(self,taxyear):
		######## FIRST WE MATCH THE SAME-DAY TRANSACTIONS
		## set day-transaction condition to the strategy
		self.strategy.condition = self.sameDay
		## match the list of transactions with that strategy
		self.matchListInPairs(taxyear)
		## reinitialise the strategy
		self.strategy.init()
		## set 30 days range as the condition to the strategy
		self.strategy.condition = self.within30Range
		## match the list of transactions with that strategy
		self.matchListInPairs(taxyear)
		
		### march holdings with the rest
		self.matchListInHoldings(taxyear)

		return self.calculateGains(taxyear)

	def matchListInHoldings(self,taxyear):
		holdingsGains = 0
		for trade in self.trades:
			result = self.holdings.processTrade(trade)
			if result :
				self.matches.append(result)

	def matchListInPairs(self,taxyear):

		while not self.strategy.done:
			sTrade = self.strategy.current()[0] ### before x
			bTrade = self.strategy.current()[1] ### before y
			
			if self.strategy.matchable():	
				self.matchPair(bTrade,sTrade,self.strategy.condition.__name__)
				self.strategy.nextSell()
			else:
				self.strategy.next()

	def calculateGains(self, taxyear):
		total=0
		print("---------------------------------------------------")
		print("--------------- TAXABLE EVENTS --------------------")
		print("---------------------------------------------------")
		days=0
		bnb=0
		avg=0
		for elem in self.matches:
			print(elem)
			total += elem.taxable(taxyear)
			if elem.matchType == "taxHoldings":
				avg+= elem.taxable(taxyear)
			elif elem.matchType == "within30Range":
				bnb+=elem.taxable(taxyear)
			else:
				days+=elem.taxable(taxyear)

		print("day gains", days)
		print("bnb gains", bnb)
		print("average gains", avg)
		print("TOTAL GAINS: ",total)
			
		return(total)

	def matchPair(self, bTrade, sTrade, matchType):
		if bTrade.buy > sTrade.sell: 
			bTrade = self.splitTrade(bTrade, sTrade.sell, "buy")
		if sTrade.sell > bTrade.buy: 
			sTrade =  self.splitTrade(sTrade, bTrade.buy, "sell")
		pair = TaxSellBuyPair(bTrade,sTrade,matchType)
		
		self.matches.append(pair)
		return pair.gain()

	def splitTrade(self, trade, cut, param):
					##     2     2.5  sell          2  sell:5  --- buy:10
		
		compParam = "buy" if param=="sell" else "sell"

		### We first create two copies of the trade, the one for the reauested value and the leftOver
		requested = copy.deepcopy(trade)
		leftOver = copy.deepcopy(trade)

		### we get the total value
		total = getattr(trade, param)
		compTotal = getattr(trade, compParam)
		compCut = (cut/ total) * compTotal

		### We then update the appropriate parameter, either buy or rell, to the new split values
		setattr(requested, param, cut)
		setattr(requested, compParam, compCut)
		setattr(leftOver, param, getattr(trade, param) - cut)
		setattr(leftOver, compParam, getattr(trade, compParam) - compCut)


		### And we add the original trade to their property split to be able to trace it if necessary
		requested.split=trade.id
		leftOver.split=trade.id

		### We finally remove the original trade from the list of the tax calculator and replace it in the same
		### position with the copies
		position = self.trades.index(trade)
		self.trades.remove(trade)
		self.trades.insert(position, leftOver)
		self.trades.insert(position, requested)

		return requested
	
			
trading = TradingHistory()
trading.append_cointrackingcsv_trade_list("trade-list.csv") 
tax_calculator = TaxCalculator(trading)
print("new ",tax_calculator.calculateUKTax(2018))









