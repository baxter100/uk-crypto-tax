## uk-crypto-tax
Tool written in Python for calculating Capital Gains Tax on cryptocurrency trades in UK

**The current versions only output total gains but not yet a proper tax report. We are currently working on adding this**

**We have two seperate versions to help noticing errors. Version 2 is better structured code and likely what we will use in the future. At the moment it seems they both output the same values, except that version 2 recognizes gifts/hardforks as taxable events.**

### Disclaimer
You use this code at your own discretion. We offer no guarantee that this will calculate tax exactly as HMRC requires. A fundamental reason for adopting open source methods in this project is so that people from all backgrounds can contribute, spot errors and help improve the system.

### Tax Model
This tool aims to follow the guidlines from HMRC on crypto taxes. Most of this has been based on the helpful site https://cryptotax.uk/ and some independent research. The model so far works roughly as follows:
1. Same Day Rule. The tool first checks for occurences of sales of assets where there is a corresponding buy of the same asset on the same day, using FIFO on that day to match assets
2. Bed & Breakfasting Rule. The tool then checks using the 'bread and breakfasting' rule to check for occurences of sales of assets where there is a corresponding buy of the same asset within 30 days in the future (inclusive). Again using FIFO to match assets.
3. Section 104 Holding. Finally the program calculates gains from remaining assets by working out the average price paid for the remaining unmatched assets up until the sale.

At each stage the tool adds the gains made to the captial gains total where the sale has occured in the given tax year.

#### Ambiguities around strategies
There are various ambiguities around specifics of how gain should be calculated and we highlight them here. If you have any experience here or advice, please get in touch.

1. The current model uses a FIFO strategy for the same day rule and the bread and breakfast rule stage. We are not sure however that this is strictly correct

2. The current model works out the gain on a trade as value_of_trade-cost_basis. However, how to calculate the value of a trade appears to be ambiguous. This can either be the value of the assets acquired or the value of the assets sold (in GBP). The current model uses "Counterpart" pricing for this valuation as this appears most intuitive, though there are different methods of doing this i.e. "Best" and "Transaction" prices. (The same issue may also apply to calculating the cost basis)

3. Regarding bed and breakfasting we need to clarify if the 30 days is inclusive.

4. We are assuming that gifts of coins/coins gained from hard forks are not taxable events and the costbasis is set at 0.

### Getting Started
There are basically four steps to getting this running:
1. Creating an appropriate trade list
2. Installing python3 (this code is not python v.2 compatible)
3. Downloading one of the gainscalculator files and making minor edits
4. Executing the file

#### Creating an appropriate trade list

Currently **the program requires a csv file formatted in a specific way including all trades with GBP values --- see sample-trade-list.csv**. We used https://cointracking.info/ to obtain the necessary csv file and this is what we recommend at the moment. Go to https://cointracking.info/trade_prices.php and download the csv file from there (if you have an account!). If you are stitching multiple lists together, make sure the trades are still in chronological order.

#### Installing python3
Installing Python is generally easy, and nowadays many Linux and UNIX distributions include a recent Python. Even some Windows computers (notably those from HP) now come with Python already installed.

For guidance installing python3 on your machine see https://wiki.python.org/moin/BeginnersGuide/Download

#### Making minor edits

Currently we have two separately created versions. This is helping us identify problems and mistakes. The two versions are more or less the same, though currently version two considers gifting/hard forks as a taxable event. Further, version two is likely the structure we will use in the end as it will be easier to incorporate a tax report.

##### Version 1
To run the code, in `filename="trade-list.csv"` change trade-list.csv to point to the file you downloaded from cointracking.info. Then run the python file. You will be asked to input your rate of tax and the tax year you want to calculate gains for.

Version 1 currently doesn't output a tax report, but we will be amending this soon.

##### Version 2
On line 327, `trading.append_cointrackingcsv_trade_list("trade-list.csv")`. chanbge trade-list.csv to point to your trade list and run `print("new ",tax_calculator.calculateUKTax(2018))`

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
