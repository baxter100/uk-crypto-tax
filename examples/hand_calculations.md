## Calculations of sample lists to compare

First we will label the trades in chronological order (e.g. 1 is the first trade and 5 is the most recent)

### Day matches
First for any disposal we look for corresponding buys on the same day.

This occurs in the ETH disposal in trade 1 (working from the bottom), with a same-day buy in trade 2.

All of the disposed ETH is accounted for in the accompanying same-day buy, so the proceeds are the total proceeds:
proceeds = £400

The cost basis is the amount it cost to buy the 0.5 disposed ETH.
cost basis =  (417+0.2/0.6) x 0.5 = £347.667 Note the fee is also included here as we are buying using GBP.

[comment]: <> (There is also a fee for this buy which we should add to the cost basis &#40;in proportion to the amount of the buy allocated&#41;:)

[comment]: <> (Fee to add = &#40;0.2/0.6&#41; x 0.5 = £0.16666667)

[comment]: <> (When we make a disposal into the native currency &#40;GBP&#41; we also add the fee from the disposal to the cost:)

[comment]: <> (Fee to add = £1.20)

There is also a fee for this sale of £1.20 (which is fully included as the disposal is fully accounted for).

[comment]: <> (Gain from this pair of trades is 400 - 347.5 - 0.16666667 - 1.20 = £51.13333333)

Gain from this pair of trades is 400 - 347.667 - 1.20 = £51.13

There are no other day matches.
Total gains from same day trades = £51.13

### BNB matches
Next for any unaccounted for disposal we look for corresponding buys within the next 30 days.

This occurs in the ETH disposal in trade 4, with a bnb buy in trade 5.

Only a portion of the disposed ETH is accounted for in the accompanying buy, so the proceeds are a portion of the total:
proceeds = (1/1.01)*560.75 = £555.1980198

The cost basis is the amount it cost to buy the 1 disposed ETH.
cost basis =  £580

There is also a portion of the fee to account for when disposing of the ETH
fee = (1/1.01)* 0.1 = 0.099

Gain from this pair of trades is 555.1980198 - 580 - 0.099 = -£24.90

Note: there is still 0.01 ETH unaccounted for in this disposal.

There are no other bnb matches.
Total gains from bnb trades = -£24.90

### 104 Holdings

Next for any unaccounted for disposal we look for the average cost basis from previous corresponding unaccounted for buys.

Trade 4 has 0.01 unaccounted for disposed ETH and trade 5 has 802 unaccounted for disposed USDT.

For trade 4, the avg cost per coin is:
((417 + 0.2/0.6)x0.1 + (325/0.49) x 0.49)/ (0.1 + 0.49) = 668.700565

This is from the leftover 0.1 ETH bought in trade 2 (plus the corresponding fee) and the ETH bought in trade 3.

so the cost basis for the 0.01 disposed ETH is:
668.700565 * 0.01 = 6.68700565



Proceeds from this 0.01 ETH are:
(0.01/1.01)*560.75 = 5.551980198

The associated fee is:
(0.01/1.01)*0.1 = 0.00099

The gain from trade 4 here is then:
5.551980198 - 6.68700565 - 0.00099= -£1.136015

For trade 5, the avg cost per coin is just from acquiring USDT in trade 4:
502.11/900

And the cost basis for the disposed 802 USDT is therefore:
(502.11/900) x 802 = 447.4358

Proceeds from this 802 USDT are:
575.73

The gain from trade 5 here is then:
575.73 - 447.4358 = £128.2942

Total gains from avg trades = -£1.136015 + £128.2942 = £127.15818

### Total

Total capital gains are therefore:

£51.1333 - £24.90 + £127.15818 = £153.39


Note: Look how long this takes for four trades... This is why we automate things