## uk-crypto-tax
Prototype Tool written in Python for calculating Capital Gains Tax on cryptocurrency trades in UK

**THIS IS STILL NOT FULLY FUNCTIONING, CHANGES STILL NEED MAKING AND IT NEEDS TESTING**

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

### Getting Started
Currently **the program requires a csv file formatted in a specific way including all trades with GBP values**. We used https://cointracking.info/ to obtain the necessary csv file and this is what we recommend at the moment. Go to https://cointracking.info/trade_prices.php and download the csv file from there (if you have an account!). If you are stitching multiple lists together, make sure the trades are still in chronological order.

To run the code, in filename="trade-list.csv" change trade-list.csv to point to the file you downloaded from cointracking.info. Then run `totaltax(taxyear)` where tax year is the year you want to check i.e. 2018 will calculate tax for the 2017/18 tax year.

### Donations
Donations are welcome to support us with improving the code and develop new features - see below!

We've set up addresses for most of your favourite coins ;)

ETH: 0xff2250aa872c77d2670af18c1d5081195ed499f8
Bitcoin: 19TB1Wz5JRVeLfD1KmP7zpyH9hK7S52UVK
DASH: XhN5yPWhfu5Q4Jwieip9xRVfNiWJWgEujK
LTC: LUSD4xWL2RgvCCUDtwhecm89BjuH4hPR1Q
ZCASH: t1V46YHSApsYod1U5jX5Szd8Zs5stkCxL1C
DOGE: DNnSJKMoTRSKw2iq52jRPt5pVh4LytWJoM
BitcoinCash: 13fx3xWuff3Vt7GVZhqEPZaFeHetJLDjtT
BAT: 0xff2250aa872c77d2670af18c1d5081195ed499f8
EOS: 0xff2250aa872c77d2670af18c1d5081195ed499f8
ETC: 0x5e7a73447cce4978c2a1fdde1b9c7e6e5dc84be8

### Future Developments
* Take input from different sources directly like Poloniex, Localbitcoin, kraken etc.. so cointracking isn't required
* Make a nice user interface
* Output a proper report
