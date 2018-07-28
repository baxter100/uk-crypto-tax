## Uk Capital Gains Calculator for Cryptocurrency Trades

### Table of Contents
1. [Introduction](#introduction)
2. [Disclaimer](#disclaimer)
3. [Tax Model](#tax-model)
4. [Getting Started](#getting-started)
5. [Troubleshooting](#troubleshooting)
6. [Donations](#donations)
7. [Future Developments](#future-developments)
8. [Contact](#contact)

### Introduction
Tool written in Python for calculating Capital Gains Tax on cryptocurrency trades in UK

The easiest way to get started is by uploading your trades to https://cointracking.info/ and then downloading the trade list from https://cointracking.info/trade_prices.php

For general crypto-related tax questions see: https://bettingbitcoin.io/cryptocurrency-uk-tax-treatments/ or https://cryptotax.uk/

**We have two seperate versions to help noticing errors. If you find any discrepancies in the versions please let us know**

**Also, note that version 2 currently recognizes gifts/hardforks as taxable events.**

### Disclaimer
You use this code at your own discretion. We offer no guarantee that this will calculate tax exactly as HMRC requires. A fundamental reason for adopting open source methods in this project is so that people from all backgrounds can contribute, spot errors and help improve the system.

### Tax Model
This tool aims to follow the guidlines from HMRC on crypto taxes. Most of this has been based on the helpful sites https://bettingbitcoin.io/ and https://cryptotax.uk/ and some independent research looking at the HMRC internal manual for crytpocurrencies: https://www.gov.uk/hmrc-internal-manuals/capital-gains-manual/cg12100. The model so far works roughly as follows:
1. Same Day Rule. The tool first checks for occurences of sales of assets where there is a corresponding buy of the same asset on the same day, using FIFO on that day to match assets
2. Bed & Breakfasting Rule. The tool then checks using the 'bread and breakfasting' rule to check for occurences of sales of assets where there is a corresponding buy of the same asset within 30 days in the future (inclusive). Again using FIFO to match assets.
3. Section 104 Holding. Finally the program calculates gains from remaining assets by working out the average price paid for the remaining unmatched assets up until the sale.

At each stage the tool adds the gains made to the captial gains total where the sale has occured in the given tax year.

#### Ambiguities around strategies
There are various ambiguities around specifics of how gain should be calculated and we highlight them here. If you have any experience here or advice, please get in touch (https://www.reddit.com/user/uk-crypto-tax/).

1. The current model uses a FIFO strategy for the same day rule and the bread and breakfast rule stage. We are not sure however that this is strictly correct

2. The current model works out the gain on a trade as value_of_trade-cost_basis. However, how to calculate the value of a trade appears to be ambiguous. This can either be the value of the assets acquired or the value of the assets sold (in GBP). The current model uses "Counterpart" pricing for this valuation as this appears most intuitive, though there are different methods of doing this i.e. "Best" and "Transaction" prices. (The same issue may also apply to calculating the cost basis). The counterpart pricing (what we use) uses the value of the obtained assett.

3. Regarding bed and breakfasting we need to clarify if the 30 days is inclusive

4. We unsure whether gifts of coins/coins gained from hard forks are taxable events with costbasis 0 or not. At the moment, **version 1 does not consider this taxable** while **version 2 does**. **WARNING: This can make big differences to overall calculated gain**

5. Version 1 treats any outgoings such as gifts you give to people and tips as taxable --- calculating the gain by working out the cost basis and subtracting that from the value of the crypto you gave away. See https://www.gov.uk/capital-gains-tax/gifts for more information on gifts

### Getting Started
There are basically four steps to getting this running:
1. Creating an appropriate trade list
2. Installing python3 (this code is not python v.2 compatible)
3. Downloading one of the gainscalculator files and making minor edits
4. Executing the file

#### Creating an appropriate trade list

Currently **the program requires a csv file formatted in a specific way including all trades with GBP values --- see sample-trade-list.csv**. We used https://cointracking.info/ to obtain the necessary csv file and this is what we recommend at the moment. Go to https://cointracking.info/trade_prices.php and download the csv file from there (if you have an account!). **Make sure you rename the file to trade-list.csv**. If you are stitching multiple lists together, make sure the trades are still in chronological order.

#### Installing python3
Installing Python is generally easy, and nowadays many Linux and UNIX distributions include a recent Python. Even some Windows computers (notably those from HP) now come with Python already installed.

For guidance installing python3 on your machine see https://wiki.python.org/moin/BeginnersGuide/Download

#### Making minor edits

Currently we have two separately created versions. This is helping us identify problems and mistakes. The two versions are more or less the same, though currently version two considers gifting/hard forks as a taxable event. Further, version two is likely the structure we will use in the end as it will be easier to incorporate a tax report.

##### Version 1
To run the code first make sure your csv file is in the same folder as the python file and change the name of your csv file to "trade-list.csv" (Or, alternatively on line 16 change trade-list.csv to point to the file you downloaded from cointracking.info). Then run the python file. You will be asked to input your rate of tax and the tax year you want to calculate gains for.

If you would like to include fees in the calculation, you can do this by downloading the 'Trading Fees' list as a csv from cointracking and editing a bit of the code. What you need to do is download the feelist to the same folder as the python script and save it as fee-calculation.csv. Then in the python file uncomment the line `trading.append_fees(feelist)`.

Version 1 currently outputs a two lists of gains calculations as a html file which you will be able to view with your browser. Explained below:

##### Simple Report
The simple report contains a list of all sales of cryptocurrency assets including 
* Proceeds: The GBP value of proceeds of the sale. This is calculated as the GBP value of the assets acquired at the time of the sale
* Cost basis: The GBP value of the cost basis for that sale
* Fee: The GBP value of fee paid for that sale. 
* Gain/loss: The GBP value of gain/loss
* Date sold. 
* Currency: The abbreviation of the crytocurrency that was sold.
* Amount sold: The amount of the cryptocurrency sold
* Location of sale: Which exchange the sale was made on
* Number of sell trade: The buys/sells are ordered by number, 1 being the first buy/sell

##### Detailed Report
The detailed report gives a list of sales which are broken down to show how they have been matched. The columns are as follows:
* Match Type: This indicates which rule was used to match the asset in the sale/how the cost-basis is calculated. “avg” indicates the cost basis is calculated from the value of the holdings. “bnb” indicates the cost basis is calculated from a correspending buy within 30 days. “day” indicates the cost basis is calculated from a corresponding buy on the same day
* Proceeds: The GBP value of proceeds of the relevant portion of the sale. This is calculated using the GBP value of the assets acquired at the time of the sale.
* Cost basis: The GBP value of the cost basis for the relevant portion of the sale
* Fee: The GBP value of fee paid for that sale. NOTE: These are duplicated over split trades
* Gain/loss: The GBP value of gain/loss for the relevant portion of the sale
* Date sold. 
* Currency: The abbreviation of the crytocurrency that was sold
* Amount sold: The amount of the cryptocurrency sold for the relevant portion of the sale
* Location of sale: Which exchange the sale was made on
* Number of sell trade: The buys/sells are ordered by number, 1 being the first buy/sell
Then, if possible (i.e. a ‘day’ or ‘bnb’ match) the details of the corresponding buy are also given:
* Date acquired: The date on which the cryptocurrency was bought
* Location of Buy: which exchange the cryptocurrency was bought on
* Number of matched buy trade: This indicates which buy trade the sell trade has been matched with

##### Version 2
On line 327, `trading.append_cointrackingcsv_trade_list("trade-list.csv")`. change trade-list.csv to point to your trade list and run `print("new ",tax_calculator.calculateUKTax(2018))`

### Troubleshooting
#### Getting strange results? 

* Have you checked both version 1 and 2? Gifts are added to your gains in v2 so this may be giving you a larger figure than expected
* How did you obtain your csv file? The formatting is very specific. In particular, the first line automatically gets deleted to remove column headers, so this must not contain any important information. Also, the columns need to remain exactly as they are from cointracking. See sample trade list.
* Which fiat currencies have you been trading in? The program currently only considers GBP as fiat, so if you have trades in other fiat currencies you're likely to get strange results.
* Ideally trades should have the same buy and sell value and in most cases the discrepancy is negligible. However, if there is a large difference i.e. the spread is large, as can sometimes be the case, then the choice of which value to use when calculating gains or losses can make a significant difference.
* Sometimes fees are baked into trades so can be counted twice (see last comment here: https://github.com/baxter100/uk-crypto-tax/issues/1)

#### Errors? 

* Are you getting a UnicodeDecodeError? In the load_trades_from_csv function in the TradingHistory class, where it says open( filename ). If you change this to open( filename, encoding='utf-8' ) this should solve your problem. 
* SyntaxError: Non-ASCII character '\xc2'. Which version of python are you using? You need to be using version 3!
* How did you obtain your csv file? The formatting is very specific. In particular, the first line automatically gets deleted to remove column headers, so this must not contain any important information. Also, the columns need to remain exactly as they are from cointracking. See sample trade list.
* ValueError: could not convert string to float. It may be that your trade list is not correctly formatted, see https://github.com/baxter100/uk-crypto-tax/blob/master/sample-trade-list.csv.

If you get any error messages when running the code and can't figure out what's going on, get in touch!


### Donations
Donations are welcome to support us with improving the code and develop new features - see below!

We've set up addresses for most of your favourite coins ;)

ETH: 0xff2250aa872c77d2670af18c1d5081195ed499f8

Bitcoin: 19TB1Wz5JRVeLfD1KmP7zpyH9hK7S52UVK

BitcoinCash: 13fx3xWuff3Vt7GVZhqEPZaFeHetJLDjtT

DASH: XhN5yPWhfu5Q4Jwieip9xRVfNiWJWgEujK

LTC: LUSD4xWL2RgvCCUDtwhecm89BjuH4hPR1Q

ZCASH: t1V46YHSApsYod1U5jX5Szd8Zs5stkCxL1C

DOGE: DNnSJKMoTRSKw2iq52jRPt5pVh4LytWJoM

BAT: 0xff2250aa872c77d2670af18c1d5081195ed499f8

EOS: 0xff2250aa872c77d2670af18c1d5081195ed499f8

NANO (XRB): xrb_1rxyjpdo7wnbab813eisg1bdfaihzymod4tmuqafhch89j7heuapypyjj3sj

ETC: 0x5e7a73447cce4978c2a1fdde1b9c7e6e5dc84be8


### Future Developments
* Improve the program to output a more comprehensive tax report
* Create a nicer user interface
* Take input from different sources directly like Poloniex, Localbitcoin, kraken etc.. so cointracking isn't required

### Contact
https://www.reddit.com/user/uk-crypto-tax/
