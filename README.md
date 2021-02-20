## UK Capital Gains Calculator for Cryptocurrency Trades

This repo is intended as a cleaner version the original, which seems to be outdated and messy.

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


### Disclaimer
You use this code at your own discretion. We offer no guarantee that this will calculate tax exactly as HMRC requires. A fundamental reason for adopting open source methods in this project is so that people from all backgrounds can contribute, spot errors and help improve the system.

### Tax Model
This tool aims to follow the guidelines from HMRC on crypto taxes. Most of this has been based on the helpful sites https://bettingbitcoin.io/ and https://cryptotax.uk/ and some independent research looking at the HMRC internal manual for crytpocurrencies: https://www.gov.uk/hmrc-internal-manuals/capital-gains-manual/cg12100. The model so far works roughly as follows:
1. Same Day Rule. The tool first checks for occurances of sales of assets where there is a corresponding buy of the same asset on the same day, using FIFO on that day to match assets
2. Bed & Breakfasting Rule. The tool then checks using the 'bread and breakfasting' rule to check for occurences of sales of assets where there is a corresponding buy of the same asset within 30 days in the future (inclusive). Again using FIFO to match assets.
3. Section 104 Holding. The program then calculates gains from remaining assets by working out the average price paid for the remaining unmatched assets up until the sale.
4. Future FIFO. If a disposal is still not fully accounted for, the unaccounted for amount is matched with corresponding bys using FIFO on trades in the future.
5. Unaccounted. If a disposal is still not fully accounted for, the gain is calculated as the proceeds with cost basis of 0.

#### Ambiguities around strategies
There are various ambiguities around specifics of how gain should be calculated and we highlight them here. If you have any experience here or advice, please get in touch (https://www.reddit.com/user/uk-crypto-tax/).

1. The current model uses a FIFO strategy for the same day rule and the bread and breakfast rule stage. We are not sure however that this is strictly correct

2. The current model works out the gain on a trade as value_of_trade-cost_basis. However, how to calculate the value of a trade appears to be ambiguous. This can either be the value of the assets acquired or the value of the assets sold (in GBP). The current model uses "Counterpart" pricing for this valuation as this appears most intuitive, though there are different methods of doing this i.e. "Best" and "Transaction" prices. (The same issue may also apply to calculating the cost basis). The counterpart pricing (what we use) uses the value of the obtained assett.

3. We are unsure whether gifts of coins/coins gained from hard forks are taxable events with costbasis 0 or not. At the moment, the tool doesn't calculate this as a taxable event. **WARNING: This can make big differences to overall calculated gain**

### Getting Started
There are basically four steps to getting this running:
1. Creating an appropriate trade list
2. Installing python3 (this code is not python v.2 compatible)
3. Downloading the repo and making minor edits to the config file
4. Executing the file

#### Creating an appropriate trade list

Currently **the program requires a csv file formatted in a specific way including all trades with GBP values --- see examples/sample-trade-list.csv**. We used https://cointracking.info/ to obtain the necessary csv file and this is what we recommend at the moment. Go to https://cointracking.info/trade_prices.php and download the csv file from there (comma seperated!).

Similarly a list of fees can be downloaded from cointracking using a similar process.

The format changes from time to time so check that the columns are still the same.

#### Installing python3
Installing Python is generally easy, and nowadays many Linux and UNIX distributions include a recent Python. Even some Windows computers (notably those from HP) now come with Python already installed.

For guidance installing python3 on your machine see https://wiki.python.org/moin/BeginnersGuide/Download

#### Making minor edits in the config file

A config.json file is provided so the program can be edited easily.

Most important is to check the trade csv is named the same as your trade csv (as well as the fee list if you have one).
Next change the tax year to calculate gains for the year you would like (2018 taxyear is 2017/18 taxyear and starts 06/04/2017).


#### Running

You need to run calculator.py with Python 3. This will generate a report.

##### Report
The report contains a list of all gains on disposals of cryptocurrency assets including 
* Match Type: This indicates which rule was used to match the asset in the sale/how the cost-basis is calculated.
* Proceeds: The GBP value of proceeds of the sale. This is calculated as the GBP value of the assets acquired at the time of the sale
* Cost basis: The GBP value of the cost basis for that sale
* Fee: The GBP value of fee paid for that sale. 
* Gain/loss: The GBP value of gain/loss
* Date bought (if there was a corresponding buy)
* Date sold. 
* Currency: The abbreviation of the cryptocurrency that was sold.
* Amount sold: The amount of the cryptocurrency sold


### Troubleshooting
#### Getting strange results? 

* How did you obtain your csv file? The formatting is very specific. In particular, the first line automatically gets deleted to remove column headers, so this must not contain any important information. Also, the columns need to remain exactly as they are from cointracking. See sample trade list.
* Which fiat currencies have you been trading in? The program currently only considers GBP as fiat, so if you have trades in other fiat currencies you're likely to get strange results.
* Ideally trades should have the same buy and sell value and in most cases the discrepancy is negligible. However, if there is a large difference i.e. the spread is large, as can sometimes be the case, then the choice of which value to use when calculating gains or losses can make a significant difference.
* Sometimes fees are baked into trades so can be counted twice (see last comment here: https://github.com/baxter100/uk-crypto-tax/issues/1)

#### Errors? 

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
