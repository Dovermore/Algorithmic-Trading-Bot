#This is to draft the logic for our bot, starting off very simply and then we can build a more complex bot

-----Reactive-----
When buyer:
	if (DS_REWARD_CHARGE > Ask price):
		execute order for ask price

When seller:
	if (DS_REWARD_CHARGE < Bid price):
		execture order for bid price


-----Market Maker-----
"""While we are a market maker, we can still only have 1 pending order at a time.
We want our order to have priority, while still making the max profit."
We might want to set a threshold for depth at best bid/ask for when we want to decrease the spread to have 
first priority for the trade. eg: we are a buyer and current best bid is $5.10, but the depth is only 1 we could 
send a buy order for $5.10, but if the depth is very high then we could outbid and set bid of ($5.10 + tick)."""


When buyer:
	price < DS_REWARD_CHARGE
	price = CURRENT_BEST_BID + tick
	
When seller:
	price > DS_REWARD_CHARGE
	price = CURRENT_BEST_ASK - tick



 