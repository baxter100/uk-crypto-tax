# uk-crypto-tax
Prototype Tool written in Python for calculating Capital Gains Tax on cryptocurrency trades in UK

**THIS IS STILL NOT FULLY FUNCTIONING, CHANGES STILL NEED MAKING AND IT NEEDS TESTING**

# Disclaimer
You use this code at your own discretion. We offer no guarantee that this will calculate tax exactly as HMRC requires. A fundamental reason for adopting open source methods in this project is so that people from all backgrounds can contribute, spot errors and help improve the system.

# Tax Model
This tool aims to follow the guidlines from HMRC on crypto taxes. Most of this has been based on the helpful site https://cryptotax.uk/ and some independent research. The model so far works roughly as follows:
1. Same Day Rule. The tool first checks for occurences of sales of assets where there is a corresponding buy of the same asset on the same day, using FIFO on that day to match assets
2. Bed & Breakfasting Rule. The tool then checks using the 'bread and breakfasting' rule to check for occurences of sales of assets where there is a corresponding buy of the same asset within 30 days in the future (inclusive). Again using FIFO to match assets.
3. Section 104 Holding. Finally the program calculates gains from remaining assets by working out the average price paid for the remaining unmatched assets up until the sale.

At each stage the tool adds the gains made to the captial gains total where the sale has occured in the given tax year.

# Getting Started
Currently **the program requires a csv file formatted in a specific way including all trades with GBP values**. We used https://cointracking.info/ to obtain the necessary csv file and this is what we recommend at the moment. Go to https://cointracking.info/trade_prices.php and download the csv file from there (if you have an account!).

To run the code, in filename="trade-list.csv" change trade-list.csv to point to the file you downloaded from cointracking.info. Then run `totaltax(taxyear)` where tax year is the year you want to check i.e. 2017 will calculate tax for the 2017/18 tax year.

# Donations
Donations are welcome to support us improve and develop new features for the program
Bitcoin: 1EhkbRMf3hHxWeXYyFQPf62x6q5ZyLak3T


# Future Developments
* Take input from different sources directly like Poloniex, Localbitcoin, kraken etc.. so cointracking isn't required
* Make a nice user interface
* Output a proper report
