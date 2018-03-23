import csv
from datetime import datetime, date, time

import uuid
import random
import copy

class Trade:
	buy = 0
	currency_buy = 0
	currency_sell = 0
	sell = 0
	date = 0
	sell_value_gbp = 0
	sell_value_btc = 0
	buy_value_gbp = 0
	buy_value_btc = 0
	split = None
	
	def __init__(self):
		self.id = uuid.uuid4()
	
	def exchange_rate(self):
		return amount_in/amount_out

	def __str__(self):
		return "Trade: " + self.buy + self.currency_buy + " -> " + self.sell + self.currency_sell + " | GBP:" + self.sell_value_gbp + ", " + self.date


class TradingHistory:
	trades = []
	def load_trades_from_csv(self,filename="trade-list.csv"):
		try:
			with open( filename ) as f:
				reader = csv.reader(f)     # create a 'csv reader' from the file object
				datalist = list( reader )  # create a list from the reader 
		except Exception as e:
			raise
			datalist = []
		
		return datalist
	def append_cointracking_trade_list(self,datalist):
		datalist.pop(0) #removes first line of data list which is headings
		datalist=datalist[::-1] #inverts data list to put in time order
		
		for trade in datalist:
			tr = Trade()
			tr.buy = float(trade[2])
			tr.currency_buy = trade[3] 
			tr.currency_sell = trade[7]
			tr.sell = float(trade[6]) #these were being messed up by "-" appearing in the "gift" trades so I've changed them to 0 in the csv file
			tr.date = datetime.strptime(trade[13], "%d.%m.%Y %H:%M") 
			tr.sell_value_gbp = float(trade[9])
			tr.sell_value_btc = float(trade[8])
			tr.buy_value_gbp = float(trade[5])
			tr.buy_value_btc = float(trade[4])
			tr.exchange = trade[11]

			self.trades.append(tr)
	
			
trading = TradingHistory()

data = trading.load_trades_from_csv()

trading.append_cointracking_trade_list(data) 


valueofsalepercoin = []
costbasisGBPpercoin = []

for tradenumber in range(0,len(data)):
		costbasisGBPpercoin.append(trading.trades[tradenumber].sell_value_gbp/trading.trades[tradenumber].buy)
		if trading.trades[tradenumber].sell==0:
			valueofsalepercoin.append(0)
		else:
			valueofsalepercoin.append(trading.trades[tradenumber].buy_value_gbp/trading.trades[tradenumber].sell)

def averagecostbasisuptotrade(x):
	t=0
	q=0
	for y in range(0,x):
		if trading.trades[y].currency_buy==trading.trades[x].currency_sell:
		
			t=t+costbasisGBPpercoin[y]*trading.trades[y].buy
			q=q+trading.trades[y].buy
	return t/q

def averagegain(x):
	return trading.trades[x].buy_value_gbp - averagecostbasisuptotrade(x)*trading.trades[x].sell

def taxyearstart(taxyear):
	return datetime(taxyear,4,6)

def taxyearend(taxyear):
	return datetime(taxyear+1,4,5)


fifototal=0

def gainpair(x,y,amountsellcurrency): #Given a pair of trades, returns the capital gain
	return trading.trades[x].buy_value_gbp*amountsellcurrency/trading.trades[x].sell - costbasisGBPpercoin[y]*amountsellcurrency

def fifoyear(taxyear):
	fifototal=0

	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="": #if selling an asset
			
			for y in range(0,len(data)): #begins checking trades from start
		
				
				if trading.trades[y].buy!=0 and trading.trades[y].currency_buy==trading.trades[x].currency_sell: #if there is currency to be matched with and the sell currency of x is the same as buy currency of y
					if trading.trades[y].buy>=trading.trades[x].sell:	# if there's more of the buy currency in y than sell in x it is simpler, we can just add the gain to total and reduce the amounts in y sell and x buy
						if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear): # this is so that only gains in a particular year are added
						
							fifototal=fifototal+gainpair(x,y,trading.trades[x].sell) #adds gain to total
							trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell #updates trade amounts
							trading.trades[x].sell=0 #updates trade amounts
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

							break
						else:
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts
							trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell #updates trade amounts
							trading.trades[x].sell=0 #updates trade amounts

							break
					
					elif taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):  # this is so that only gains in a particular year are added
						fifototal=fifototal+gainpair(x,y,trading.trades[y].buy) #adds gain to total
					
						
						trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy #updates trade amounts
					
						trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts
						trading.trades[y].buy=0 #updates trade amounts

					else:
						trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy #updates trade amounts
					
					
						trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts
						trading.trades[y].buy=0 #updates trade amounts
				

	return(fifototal)






def fifodays(taxyear):
	fifodaytotal=0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="":
			
			for y in range(0,len(data)):
		
			
				if trading.trades[x].date.day== trading.trades[y].date.day and trading.trades[x].date.month== trading.trades[y].date.month and trading.trades[x].date.day== trading.trades[y].date.month: #if the days are the same, there must be a better way!

				
					if trading.trades[y].buy!=0 and trading.trades[y].currency_buy==trading.trades[x].currency_sell:
						if trading.trades[y].buy>=trading.trades[x].sell:
							if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
							
								fifodaytotal=fifodaytotal+gainpair(x,y,trading.trades[x].sell)
								#print("Sale of ",trading.trades[x].sell, trading.trades[x].currency_sell, "for", trading.trades[x].buy,trading.trades[x].currency_buy, "at", trading.trades[x].exchange )
								print("In sale",x,trading.trades[x].sell, trading.trades[x].currency_sell,"was sold for",trading.trades[x].currency_buy,"with a total value of", trading.trades[x].buy_value_gbp, "and total cost basis of", costbasisGBPpercoin[y]*trading.trades[x].sell)
								trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell
								trading.trades[x].sell=0
								trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

								break
							else:
								
								trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell
								trading.trades[x].sell=0
								trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

								break
						
						elif taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
							fifodaytotal=fifodaytotal+gainpair(x,y,trading.trades[y].buy)
						
							
							trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy
						
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy)
							trading.trades[y].buy=0

						else:
							trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy
						
						
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy)
							trading.trades[y].buy=0
					

	return(fifodaytotal)


def fifobnb(taxyear):
	fifobnbtotal=0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="" and trading.trades[x].sell!=0:
			
			for y in range(x-1,len(data)):
		
			
				if y>x and y-x<=30: #May need to adjust

				
					if trading.trades[y].buy!=0 and trading.trades[y].currency_buy==trading.trades[x].currency_sell:
						if trading.trades[y].buy>=trading.trades[x].sell:
							if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
							
								fifobnbtotal=fifobnbtotal+gainpair(x,y,trading.trades[x].sell)
								trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell
								trading.trades[x].sell=0
								trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

								break
							else:
								
								trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell
								trading.trades[x].sell=0
								trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

								break
						
						elif taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
							fifobnbtotal=fifobnbtotal+gainpair(x,y,trading.trades[y].buy)
						
							
							trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy
						
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy)
							trading.trades[y].buy=0

						else:
							trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy
						
						
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy)
							trading.trades[y].buy=0
					

	return(fifobnbtotal)



def average(taxyear):
	averagetotal = 0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="" and trading.trades[x].sell!=0:
						
			if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
			
				averagetotal=averagetotal+averagegain(x)

	return(averagetotal)


def totaltax(taxyear):
	days = fifodays(taxyear)
	bnb = fifobnb(taxyear)
	avg = average(taxyear)
	print("Tax from days: £",days,". Tax from bed and breakfasting: £ ",bnb,". Tax from 404 Holdings: £ ",avg, "Total: £",days+bnb+avg)


totaltax(2017)

class taxSellBuyPair:
	def __init__(self, buyTrade):
		self.id = uuid.uuid4()
		self.buyTrade = buyTrade
		self.sellTrade = None
		self.matchType = None

	def matchSellTrade(sellTrade, matchType):
		self.matchType = matchType
		if(sellTrade.sell==self.buyTrade.buy):
			self.sellTrade = sellTrade
			return {"sell":None, "buy":None}
		elif(sellTrade.sell>self.buyTrade.buy):
			dupSell = copy.deepcopy(sellTrade)
			dupSell.sell -= self.buyTrade.buy
			self.sellTrade = sellTrade
			self.sellTrade.sell = self.buyTrade.buy
			return {"sell":dupSell, "buy":None}
		elif(sellTrade.sell<self.buyTrade.buy):
			dupBuy = copy.deepcopy(self.buyTrade)
			dupBuy.buy -= sellTrade.sell
			self.sellTrade = sellTrade
			self.buyTrade.buy = sellTrade.sell
			return {"sell":None, "buy":dupBuy}


class holdingstack:
	currency=""
	buystacklist = []
	sellstacklist = []


	def __init__(self, currency):
		self.currency = currency

	def buyTrade(self, trade):
		if trade.currency_buy == self.currency:
			
			self.buystacklist.append({"buyDate":trade.date, "buyTrade":trade, "match-type":None, "sell-trade":None})

	def sellTrade(self, sellTrade):
		if sellTrade.currency_sell == self.currency:
			self.sellstacklist.append({"date":trade.date, "sell-trade":sellTrade})

	
	def calculateTaxes(self):		
		### TODO
		## Try case 1: same day trade
		sameDayTrades = [entry for entry in self.stacklist if entry["buyDate"].day() == sellTrade.date.day() and not entry["match-type"]]
		self.processFIFOsell(sameDayTrades)

				

	


	def amount(self):
		total = 0
		for trade in self.stacklist:
			total += trade.buy
		return total

	def totalcost(self):
		total = 0
		for trade in self.stacklist:
			total += trade.sell_value_gbp
		return total

	def avgcost(self):
		return self.totalcost()/self.amount()






