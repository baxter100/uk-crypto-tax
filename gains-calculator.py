import csv
from datetime import datetime, date, time, timedelta

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
			for x in range(1,10): #"-" in gift trades weren't able to be converted in floats so was messing things up
				if trade[x]=="-":
					trade[x]=0
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

### 2018 taxyear is 2017/18 taxyear
def taxyearstart(taxyear): 
	return datetime(taxyear-1,4,6)

def taxyearend(taxyear):
	return datetime(taxyear,4,5)



fifototal=0

def gainpair(x,y,amountsellcurrency): #Given a pair of trades, returns the capital gain
	return trading.trades[x].buy_value_gbp*amountsellcurrency/trading.trades[x].sell - costbasisGBPpercoin[y]*amountsellcurrency



def fifodays(taxyear):
	fifodaytotal=0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="": #if selling an asset
			
			for y in range(0,len(data)): #begins checking trades to match with from start
		
			
				if trading.trades[x].date.day== trading.trades[y].date.day and trading.trades[x].date.month== trading.trades[y].date.month and trading.trades[x].date.day== trading.trades[y].date.month: #if the days are the same, there must be a better way!

				
					if trading.trades[y].buy!=0 and trading.trades[y].currency_buy==trading.trades[x].currency_sell: #if there is currency to be matched with and the sell currency of x is the same as buy currency of y
						if trading.trades[y].buy>=trading.trades[x].sell: # if there's more of the buy currency in y than sell in x it is simpler, we can just add the gain to total and reduce the amounts in y sell and x buy
							if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear): # this is so that only gains in a particular year are added
						
							
								fifodaytotal=fifodaytotal+gainpair(x,y,trading.trades[x].sell) #adds gain to total
								#print("Sale of ",trading.trades[x].sell, trading.trades[x].currency_sell, "for", trading.trades[x].buy,trading.trades[x].currency_buy, "at", trading.trades[x].exchange )
								print("In sale",x,trading.trades[x].sell, trading.trades[x].currency_sell,"was sold for",trading.trades[x].currency_buy,"with a total value of", trading.trades[x].buy_value_gbp, "and total cost basis of", costbasisGBPpercoin[y]*trading.trades[x].sell)
								trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell #updates trade amounts
								trading.trades[x].sell=0 #updates trade amounts
								trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

								break
							else:
								
								trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell #updates trade amounts
								trading.trades[x].sell=0 #updates trade amounts
								trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts

								break
						
						elif taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear): # this is so that only gains in a particular year are added
							fifodaytotal=fifodaytotal+gainpair(x,y,trading.trades[y].buy) #adds gain to total
						
							
							trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy #updates trade amounts
						
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts
							trading.trades[y].buy=0 #updates trade amounts

						else:
							trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy #updates trade amounts
						
						
							trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) #updates trade amounts
							trading.trades[y].buy=0 #updates trade amounts
					

	return(fifodaytotal)


def fifobnb(taxyear):
	fifobnbtotal=0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="" and trading.trades[x].sell!=0:
			
			for y in range(x-1,len(data)):
		
			
				if trading.trades[y].date>trading.trades[x].date and trading.trades[y].date-timedelta(days=30)>trading.trades[x].date: #May need to adjust this

				
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






