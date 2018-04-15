
#This code is licensed under the GNU General Public License v3.0. Please leave this notice in the code if you choose to redistibute this file redistribute this file.


import csv
from datetime import datetime, date, time, timedelta

import uuid
import random
import copy

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

def taxdatecheck(x):
	if taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
		return True




##### Fifo calculations

### Calculate gain when two trades have been matched
def gainpair(x,y): #Given a pair of trades, returns the capital gain
	if trading.trades[y].buy>=trading.trades[x].sell:

		return trading.trades[x].buy_value_gbp*trading.trades[x].sell/trading.trades[x].sell - costbasisGBPpercoin[y]*trading.trades[x].sell
		
	else:

		return trading.trades[x].buy_value_gbp*trading.trades[y].buy/trading.trades[x].sell - costbasisGBPpercoin[y]*trading.trades[y].buy

def addgainsfifo(x,y): #adds gains from pair to total if tax year is correct
	if taxdatecheck(x):
		return gainpair(x,y)
	else:
		return 0



def fifoupdatetradelist(x,y): #updates trade amounts
	if trading.trades[y].buy>=trading.trades[x].sell:

		trading.trades[y].buy=trading.trades[y].buy-trading.trades[x].sell
		trading.trades[x].sell=0
		trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy) 
	else:

		trading.trades[x].sell=trading.trades[x].sell-trading.trades[y].buy
		trading.trades[x].buy_value_gbp = trading.trades[x].buy_value_gbp - (valueofsalepercoin[x]*trading.trades[y].buy)
		trading.trades[y].buy=0

### Matching conditions

def datematch(x,y):
	if trading.trades[x].date.day == trading.trades[y].date.day and trading.trades[x].date.month == trading.trades[y].date.month and trading.trades[x].date.year == trading.trades[y].date.year: #if the days are the same, there must be a better way!:
		return True
									
def currencymatch(x,y):
	if trading.trades[x].currency_sell==trading.trades[y].currency_buy and trading.trades[y].buy!=0:
		return True

def viablesellcurrency(x):
	if trading.trades[x].currency_sell not in fiat_list and trading.trades[x].currency_sell!="" and trading.trades[x].sell!=0:
		return True


def viabledaymatch(x,y):
	return datematch(x,y) and currencymatch(x,y)

def viablebnbmatch(x,y):
	if currencymatch(x,y) and trading.trades[y].date>trading.trades[x].date and trading.trades[y].date-timedelta(days=30)<=trading.trades[x].date: #May need to adjust this
		return True


#### Tax Reporting Part

def updatetaxcostbasis(x,y):

	if trading.trades[y].buy>=trading.trades[x].sell:
		taxgains.gain_list[mapfromtradetogainlistnumber(x)].cost_basis += costbasisGBPpercoin[y]*trading.trades[x].sell
	else:
		taxgains.gain_list[mapfromtradetogainlistnumber(x)].cost_basis += costbasisGBPpercoin[y]*trading.trades[y].buy

def addgainvalues():
	for z in range(0,len(taxgains.gain_list)):
		taxgains.gain_list[z].gain_loss = taxgains.gain_list[z].proceeds - taxgains.gain_list[z].cost_basis


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
	fee =  0
	currency_fee = 0
	fee_value_gbp = 0
	
	def __init__(self):
		self.id = uuid.uuid4()
	
	def exchange_rate(self):
		return amount_in/amount_out

	def __str__(self):
		return "Trade: " + self.buy + self.currency_buy + " -> " + self.sell + self.currency_sell + " | GBP:" + self.sell_value_gbp + ", " + self.date


class TradingHistory:
	tradelist = []
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
		

			self.tradelist.append(tr)
			self.trades = copy.deepcopy(self.tradelist) #self.tradelist is the unmodified copy

	# def load_fees_from_csv(self,filename="fee-calculation.csv"):
	# 	try:
	# 		with open( filename ) as f:
	# 			reader = csv.reader(f)     # create a 'csv reader' from the file object
	# 			feelist = list( reader )  # create a list from the reader 
	# 	except Exception as e:
	# 		raise
	# 		feelist = []
	# 	return feelist

	# def append_fees(self,feelist):
	# 	feelist.pop(0) #removes first line of data list which is headings
	# 	feelist=feelist[::-1] #inverts data list to put in time order

	# 	for trade in feelist:
	# 		for tr in self.trades:
	# 			if  tr.date == datetime.strptime(trade[11], "%d.%m.%Y %H:%M") and tr.buy == float(trade[6]) and tr.sell == float(trade[8]):
	# 				tr.fee_value_gbp = float(trade[4])
	# 				tr.currency_fee = trade[3]
	# 				tr.fee = float(trade[2])
	# 				break
		
	# 	for trade in feelist:
	# 		for tr in self.tradelist:
	# 			if  tr.date == datetime.strptime(trade[11], "%d.%m.%Y %H:%M") and tr.buy == float(trade[6]) and tr.sell == float(trade[8]):
	# 				tr.fee_value_gbp = float(trade[4])
	# 				tr.currency_fee = trade[3]
	# 				tr.fee = float(trade[2])
	# 				break

### Create trade list		
trading = TradingHistory()

data = trading.load_trades_from_csv()

trading.append_cointracking_trade_list(data)

# feelist = trading.load_fees_from_csv()

# trading.append_fees(feelist)


### Populate list of values and cost basis prior to editing list, this shouldn't be necessary once deep copying is used
valueofsalepercoin = []
costbasisGBPpercoin = []

for tradenumber in range(0,len(data)):
		costbasisGBPpercoin.append(trading.trades[tradenumber].sell_value_gbp/trading.trades[tradenumber].buy)
		if trading.trades[tradenumber].sell==0:
			valueofsalepercoin.append(0)
		else:
			valueofsalepercoin.append(trading.trades[tradenumber].buy_value_gbp/trading.trades[tradenumber].sell)

#### List of possible fiat currencies
fiat_list = ["GBP", "EUR"]

### Populate list of cryptos used
crypto_list = []
for tradenumber in range(0,len(data)):
		
		if trading.trades[tradenumber].currency_buy not in crypto_list and trading.trades[tradenumber].currency_buy !="GBP" and trading.trades[tradenumber].currency_buy!="EUR" :
			crypto_list.append(trading.trades[tradenumber].currency_buy)
		if trading.trades[tradenumber].currency_sell not in crypto_list and trading.trades[tradenumber].currency_sell !="GBP" and trading.trades[tradenumber].currency_sell!="EUR" :
			crypto_list.append(trading.trades[tradenumber].currency_sell)
#print(crypto_list)



	

class Gain:
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

	def __str__(self):
		return "Amount: " + str(self.amount) +  " Currency: " + str(self.currency) + " Date Acquired: "+ str(self.date_acquired) +" Date Sold: "+ str(self.date_sold)  +  " Location of buy: "+ str(self.bought_location) +  " Location of sell: "+ str(self.sold_location) +  " Proceeds in GBP: " + str(self.proceeds) +  " Cost Basis in GBP: "+ str(self.cost_basis)+ " Fee in GBP: "+ str(self.fee) +  " Gain/Loss in GBP: "+ str(self.gain_loss)

	def __repr__(self):
		return str(self)

class GainHistory:
	gain_list=[]
	def append_gain_list(self):
		
		for x in range(0,len(data)):
			if viablesellcurrency(x): #taxdatecheck(x) and

				ga = Gain()
				ga.amount = trading.tradelist[x].sell #### Use the unmodified copy here to avoid future complication
				ga.currency = trading.tradelist[x].currency_sell
				ga.date_acquired = 0
				ga.date_sold = trading.tradelist[x].date 
				ga.bought_location = 0
				ga.sold_location = trading.tradelist[x].exchange
				ga.proceeds = trading.tradelist[x].buy_value_gbp #Proceeds are always calculated here using buy value!
				ga.cost_basis = 0
				ga.gain_loss = 0
				ga.sell_number = x
				
				self.gain_list.append(ga)
		

def mapfromtradetogainlistnumber(x):
	for z in range(0,len(taxgains.gain_list)):
		if taxgains.gain_list[z].sell_number==x:
			return int(z)
			break



### Create tax report list

taxgains = GainHistory()

taxgains.append_gain_list()



### Calculate gains on day trades using fifo

def fifodays(taxyear):
	fifodaytotal=0
	for x in range(0,len(data)):
		
		if viablesellcurrency(x):
			y=0
			while y < len(data) and trading.trades[x].sell > 0: #begins checking trades to match with from start
		
				if viabledaymatch(x,y): #if dates and currencies match appropriately
					
					fifodaytotal += addgainsfifo(x,y) #adds gain from this pair to total
					updatetaxcostbasis(x,y)
					fifoupdatetradelist(x,y)
				
				y+=1
	return(fifodaytotal)

### Calculate gains on bnb trades using fifo

def fifobnb(taxyear):
	fifobnbtotal=0
	for x in range(0,len(data)):

		if viablesellcurrency(x):
			y=x+1
			while y >= x+1 and y<len(data) and trading.trades[x].sell > 0:
			
				if viablebnbmatch(x,y):

					fifobnbtotal += addgainsfifo(x,y) #adds gain from this pair to total
					updatetaxcostbasis(x,y)
					fifoupdatetradelist(x,y)
				y +=1

	return(fifobnbtotal)


def updatetaxcostbasisavg(x,costbasis):
	taxgains.gain_list[mapfromtradetogainlistnumber(x)].cost_basis += costbasis

### Calculate gains on trades using 404 holdings rule
def averagecostbasisuptotrade(x,countervalue,counteramount):
	t=0
	q=0
	for y in range(0,x):
		if currencymatch(x,y):
		
			t += costbasisGBPpercoin[y]*trading.trades[y].buy
			q += trading.trades[y].buy
	if q - counteramount == 0:
		return 0
	else:	
		return (t- countervalue)/(q - counteramount)


def averagegain(x):
	return trading.trades[x].buy_value_gbp - averagecostbasisuptotrade(x)*trading.trades[x].sell - taxgains.gain_list[x].fee

	

def average_asset(taxyear,asset):
	averagetotal = 0
	countervalue = 0
	counteramount = 0
	for x in range(0,len(data)):
		if trading.trades[x].currency_sell==asset and viablesellcurrency(x):
			
			costbasis = averagecostbasisuptotrade(x,countervalue,counteramount)*trading.trades[x].sell
			updatetaxcostbasisavg(x,costbasis)
			if taxdatecheck(x):
			
				averagetotal += trading.trades[x].buy_value_gbp - costbasis

			countervalue += costbasis
			counteramount += trading.trades[x].sell

	return averagetotal


def average(taxyear):
	averagetotal=0
	for asset in crypto_list:
		averagetotal += average_asset(taxyear,asset)
		
	return averagetotal


def sumfees(taxyear):
	feetotal=0
	for x in range(0,len(data)):
		if taxdatecheck(x):
			feetotal+= trading.trades[x].fee_value_gbp

	return feetotal

		



def totalgain(taxyear):
	for x in range(0,len(data)): ### Print warning to contact HMRC
		if trading.trades[x].sell_value_gbp >= 4*annualallowance(taxyear) and taxyearstart(taxyear)<=trading.trades[x].date<= taxyearend(taxyear):
			print("Sale:",x," has a sale value of more than four times the annual allowance. If you sell more than four times the annual allowance (£45,200 for 2017/18) of crypto-assets, even if you make a profit of less than the allowance, you have to report this sale to HMRC. You can do this either by registering and reporting through Self Assessment, or by writing to them at: PAYE and Self Assessment, HM Revenue and Customs, BX9 1AS, United Kingdom")
		
	days = round(fifodays(taxyear), 2)
	bnb = round(fifobnb(taxyear), 2)
	avg = round(average(taxyear), 2)
	feetotal = round(sumfees(taxyear), 2)
	
	taxablegain = round(days + bnb +avg - feetotal - annualallowance(taxyear), 2)
	
	print("Gain from days: £",days,". Gain from bed and breakfasting: £ ",bnb,". Gain from 404 Holdings: £ ",avg, "Total value of fees paid in GBP: £",feetotal,"Total Capital Gains for ",taxyear-1,"/",taxyear,": £",round(days+bnb+avg-feetotal, 2))
	print("Total Taxable Gain for ",taxyear-1,"/",taxyear," for 'normal' people: £",taxablegain)
	return days + bnb +avg -feetotal

def taxablegain(taxyear):
	return totalgain(taxyear) -annualallowance(taxyear)

def totaltax(taxyear):
	total = totalgain(taxyear)
	print("Total tax owed at",taxpercentage,"% tax rate: £",round((total-annualallowance(taxyear))*taxpercentage/100, 2))
	return total
	





total = totaltax(taxyear)
addgainvalues() #This has to be done after the calculation runs as the costbasis part of th
#print(taxgains.gain_list)

def check(taxyear,total):
	x=0
	for z in range(0,len(taxgains.gain_list)):
		if taxyearstart(taxyear)<=taxgains.gain_list[z].date_sold<= taxyearend(taxyear):
			x+=taxgains.gain_list[z].gain_loss
	if x==total :
		print("Well done!")
	else:
		print("Gain Loss total adds up to ", x, " While the calcuated gain is: ", total)


#check(taxyear,total)

######### Facts needed for self-assesment
def taxyeardisposalscount(taxyear):
	x=0
	for z in range(0,len(taxgains.gain_list)):
		if taxyearstart(taxyear)<=taxgains.gain_list[z].date_sold<= taxyearend(taxyear):
			x+=1
	return x
def disposalproceeds(taxyear):
	x=0
	for z in range(0,len(taxgains.gain_list)):
		if taxyearstart(taxyear)<=taxgains.gain_list[z].date_sold<= taxyearend(taxyear):
			x+=taxgains.gain_list[z].proceeds
	return x
def costs(taxyear): # Note this should include exhange fees!
	x=0
	for z in range(0,len(taxgains.gain_list)):
		if taxyearstart(taxyear)<=taxgains.gain_list[z].date_sold<= taxyearend(taxyear):
			x+=taxgains.gain_list[z].cost_basis
	return x

number_of_disposals = taxyeardisposalscount(taxyear)
print ("Number of Disposals =", number_of_disposals, ". Disposal Proceeds = ", disposalproceeds(taxyear), ". Allowable Costs = ", costs(taxyear))
