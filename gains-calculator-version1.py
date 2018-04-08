
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
			for x in [6,8,9]: #"-" in gift trades weren't able to be converted in floats so was messing things up
				if trade[x]=="-":
					trade[x]=0
			tr = Trade()
			tr.buy = float(trade[2])
			tr.currency_buy = trade[3] 
			tr.currency_sell = trade[7]
			tr.sell = float(trade[6]) 
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

### Populate list of values and cost basis prior to editing list
valueofsalepercoin = []
costbasisGBPpercoin = []

for tradenumber in range(0,len(data)):
		costbasisGBPpercoin.append(trading.trades[tradenumber].sell_value_gbp/trading.trades[tradenumber].buy)
		if trading.trades[tradenumber].sell==0:
			valueofsalepercoin.append(0)
		else:
			valueofsalepercoin.append(trading.trades[tradenumber].buy_value_gbp/trading.trades[tradenumber].sell)

### Populate list of cryptos used
crypto_list = []
for tradenumber in range(0,len(data)):
		
		if trading.trades[tradenumber].currency_buy not in crypto_list and trading.trades[tradenumber].currency_buy !="GBP" :
			crypto_list.append(trading.trades[tradenumber].currency_buy)
		if trading.trades[tradenumber].currency_sell not in crypto_list and trading.trades[tradenumber].currency_sell !="GBP" :
			crypto_list.append(trading.trades[tradenumber].currency_sell)



##### Tax Facts

def annualallowance(taxyear):
	if taxyear==2015:
		 return 11000
	if taxyear==2016:
		 return 11100
	if taxyear==2017:
		 return 11100
	if taxyear==2018:
		 return 11300
	if taxyear==2019:
		 return 11700

taxpercentage = float(input('Enter the percentage of tax you pay on captial gains: '))

taxyear = int(input('Enter the year you want to calculate tax for (e.g. 2018 for 2017/2018): '))

### 2018 taxyear is 2017/18 taxyear
def taxyearstart(taxyear):
	return datetime(taxyear-1,4,6)

def taxyearend(taxyear):
	return datetime(taxyear,4,6) #This needs to be 6 as 05.06.2018 < 05.06.2018 12:31


### Calculate gain when two trades have been matched
def gainpair(x,y,amountsellcurrency): #Given a pair of trades, returns the capital gain
	return trading.trades[x].buy_value_gbp*amountsellcurrency/trading.trades[x].sell - costbasisGBPpercoin[y]*amountsellcurrency



### Calculate gains on sameday trades using fifo
def fifodays(taxyear):
	fifodaytotal=0
	for x in range(0,len(data)):
		
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="": #if selling an asset

			for y in range(0,len(data)): #begins checking trades to match with from start
		
				if trading.trades[x].currency_sell==trading.trades[y].currency_buy and trading.trades[x].date.day == trading.trades[y].date.day and trading.trades[x].date.month == trading.trades[y].date.month and trading.trades[x].date.year == trading.trades[y].date.year: #if the days are the same, there must be a better way!
					
				
					if trading.trades[y].buy!=0 and trading.trades[y].currency_buy==trading.trades[x].currency_sell: #if there is currency to be matched with and the sell currency of x is the same as buy currency of y
						if trading.trades[y].buy>=trading.trades[x].sell: # if there's more of the buy currency in y than sell in x it is simpler, we can just add the gain to total and reduce the amounts in y sell and x buy
							if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear): # this is so that only gains in a particular year are added
						
							
								fifodaytotal=fifodaytotal+gainpair(x,y,trading.trades[x].sell) #adds gain to total
								#print("Sale of ",trading.trades[x].sell, trading.trades[x].currency_sell, "for", trading.trades[x].buy,trading.trades[x].currency_buy, "at", trading.trades[x].exchange )
								#print("In sale",x,trading.trades[x].sell, trading.trades[x].currency_sell,"was sold for",trading.trades[x].currency_buy,"with a total value of", trading.trades[x].buy_value_gbp, "and total cost basis of", costbasisGBPpercoin[y]*trading.trades[x].sell)
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

### Calculate gains on bnb trades using fifo
def fifobnb(taxyear):
	fifobnbtotal=0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell!="GBP" and trading.trades[x].currency_sell!="" and trading.trades[x].sell!=0:

			for y in range(x-1,len(data)):
		
			
				if trading.trades[y].date>trading.trades[x].date and trading.trades[y].date-timedelta(days=30)<=trading.trades[x].date: #May need to adjust this
					
				
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


### Calculate gains on trades using 404 holdings rule
def averagecostbasisuptotrade(x,countervalue,counteramount):
	t=0
	q=0
	for y in range(0,x):
		if trading.trades[y].currency_buy==trading.trades[x].currency_sell:
		
			t=t+costbasisGBPpercoin[y]*trading.trades[y].buy
			q=q+trading.trades[y].buy
	if q - counteramount == 0:
		return 0
	else:	
		return (t- countervalue)/(q - counteramount)


def averagegain(x):
	return trading.trades[x].buy_value_gbp - averagecostbasisuptotrade(x)*trading.trades[x].sell

	

def average_asset(taxyear,asset):
	averagetotal = 0
	countervalue = 0
	counteramount = 0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell==asset and trading.trades[x].sell!=0:
			
			costbasis = averagecostbasisuptotrade(x,countervalue,counteramount)*trading.trades[x].sell
			if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
			
				averagetotal=averagetotal+ trading.trades[x].buy_value_gbp - costbasis

			countervalue = countervalue + costbasis
			counteramount = counteramount + trading.trades[x].sell

	return averagetotal


def average(taxyear):
	averagetotal=0
	for asset in crypto_list:
		averagetotal =averagetotal + average_asset(taxyear,asset)
		
	return averagetotal


		



def totalgain(taxyear):
	for x in range(0,len(data)): ### Print warning to contact HMRC
		if trading.trades[x].sell_value_gbp >= 4*annualallowance(taxyear) and taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
			print("Sale:",x," has a sale value of more than four times the annual allowance. If you sell more than four times the annual allowance (£45,200 for 2017/18) of crypto-assets, even if you make a profit of less than the allowance, you have to report this sale to HMRC. You can do this either by registering and reporting through Self Assessment, or by writing to them at: PAYE and Self Assessment, HM Revenue and Customs, BX9 1AS, United Kingdom")
		
	days = round(fifodays(taxyear), 2)
	bnb = round(fifobnb(taxyear), 2)
	avg = round(average(taxyear), 2)
	
	taxablegain = round(days + bnb +avg - annualallowance(taxyear), 2)
	
	print("Gain from days: £",days,". Gain from bed and breakfasting: £ ",bnb,". Gain from 404 Holdings: £ ",avg, "Total Capital Gains for ",taxyear-1,"/",taxyear,": £",round(days+bnb+avg, 2))
	print("Total Taxable Gain for ",taxyear-1,"/",taxyear," for normal people: £",taxablegain)
	return days + bnb +avg

def taxablegain(taxyear):
	return totalgain(taxyear) -annualallowance(taxyear)

def totaltax(taxyear):
	total = totalgain(taxyear)
	print("Total tax owed at",taxpercentage,"% tax rate: £",round((total-annualallowance(taxyear))*taxpercentage/100, 2))
	





totaltax(taxyear)
