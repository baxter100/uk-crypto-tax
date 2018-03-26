import csv
from datetime import datetime, date, time

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
	def append_cointrackingcsv_trade_list(self,filename="trade-list.csv"):
		datalist = self.load_trades_from_csv(filename)
		datalist.pop(0) #removes first line of data list which is headings
		datalist=datalist[::-1] #inverts data list to put in time order
		
		for t in datalist:
			bexrate = 0 if float(t[2])==0 else float(t[5])/float(t[2])
			sexrate = 0 if float(t[6])==0 else float(t[9])/float(t[6])
			self.trades.append(Trade(float(t[2]), t[3], float(t[6]), t[7], datetime.strptime(t[13], "%d.%m.%Y %H:%M"), bexrate, sexrate, t[11]))

	def averagecostbasisuptotrade(self, x):
		t=0
		q=0
		for y in range(0,x):
			if self.trades[y].currency_buy==self.trades[x].currency_sell:
			
				t+=self.trades[y].costbasisGBPpercoin()*self.trades[y].buy
				q+=self.trades[y].buy
		return t/q

	def count(self):
		return len(self.trades)

class taxSellBuyPair:
	def __init__(self, buyTrade, sellTrade, matchType):
		self.id = uuid.uuid4()
		self.bTrade = buyTrade
		self.sTrade = sellTrade
		self.matchType = matchType
		self.bTrade.bmatched = True
		self.sTrade.smatched = True


	def gainpair(self): #Given a pair of trades, returns the capital gain
		return self.sTrade.buy_value_gbp() - self.bTrade.costbasisGBPpercoin()* self.bTrade.buy
	def taxable(self, taxyear):
		return self.gainpair() if taxyearstart(taxyear)<=self.sTrade.date<= taxyearend(taxyear) else 0
	def __str__(self):
		return "PAIR \n -" + str(self.sTrade) +" \n -" +  str(self.bTrade) +" \n - Gain pair " +  str(self.taxable(2017))


class FIFOStrategy:
	def __init__(self, trades):
		self.trades = trades
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

class CurrencyHoldings:
	def __init__(self, currency):
		self.currency = currency
		self.holdings = 0
		self.averageValue = 0

	def addCoins(trade):
		totalCurrentValue = self.holdings * self.averageValue
		totalCurrentValue += trade.buy_value_gbp()
		self.holdings += trade.buy
		self.averageValue = totalCurrentValue/self.stack

	def __str__(self):
		return self.currency + " HOLDINGS:\nHoldings " + str(self.holdings) + "    Average Value: " + str(self.averageValue)


class TaxCalculator:
	def __init__(self, tradingHistory):
		self.th = tradingHistory
		self.matches = []
		self.trades = copy.deepcopy(self.th.trades)
		self.strategy = FIFOStrategy(self.trades)

	def matchList(self,taxyear):
		total=0
		it = 0

		while not self.strategy.done:
			sTrade = self.strategy.current()[0] ### before x
			bTrade = self.strategy.current()[1] ### before y
			
			if self.strategy.matchable():	
				print("MATCHINGG \n" + self.strategy.currentPrint())
				self.matchPair(bTrade,sTrade,"year")
				self.strategy.nextSell()
			else:
				self.strategy.next()

		for elem in self.matches:
			print(elem)
			total += elem.taxable(taxyear)
			
		return(total)

	def matchPair(self, bTrade, sTrade, matchType):
		if bTrade.buy > sTrade.sell: 
			bTrade = self.splitTrade(bTrade, sTrade.sell, "buy")
		if sTrade.sell > bTrade.buy: 
			sTrade =  self.splitTrade(sTrade, bTrade.buy, "sell")
		pair = taxSellBuyPair(bTrade,sTrade,matchType)
		
		self.matches.append(pair)
		return pair.gainpair()

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

		print("Splitting " + str(trade) + "\n - " + str(requested) + "\n - " + str(leftOver) )

		### We finally remove the original trade from the list of the tax calculator and replace it in the same
		### position with the copies
		position = self.trades.index(trade)
		self.trades.remove(trade)
		self.trades.insert(position, leftOver)
		self.trades.insert(position, requested)

		print("CURRENT LIST")
		for trade in self.trades:
			print(str(trade))

		return requested

def taxyearstart(taxyear):
	return datetime(taxyear,4,6)

def taxyearend(taxyear):
	return datetime(taxyear+1,4,5)





	
			
trading = TradingHistory()
trading.append_cointrackingcsv_trade_list() 
tax_calculator = TaxCalculator(trading)
print("new ",tax_calculator.matchList(2017))









