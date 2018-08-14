"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import time

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price"}

# ------ Add a variable called DS_REWARD_CHARGE -----
# Dependent on actual task
DS_REWARD_CHARGE = 500


# Enum for the roles of the bot
class Role(Enum):
    BUYER = 0
    SELLER = 1


# Let us define another enumeration to deal with the type of bot
class BotType(Enum):
    MARKET_MAKER = 0
    REACTIVE = 1


class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id, name="DSBot")
        self._market_id = -1
        self._role = Role(0)
        self._bot_type = BotType(0)
        self._all_markets = []

    def run(self):
        self.initialise()
        self.start()

    def initialised(self):
        for market_id, market_dict in self.markets.items():
            self._all_markets.append(MyMarkets(market_dict, self))
            self.inform("Added market")
        self.inform("Finished Adding markets, the current list of markets are: " + repr(self._all_markets))
        pass
    # ------ End of Constructor and initialisation methods -----

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        pass

    def received_marketplace_info(self, marketplace_info):
        pass

    def received_completed_orders(self, orders, market_id=None):
        pass

    def received_holdings(self, holdings):
        pass

    # ------ Helper and trivial methods -----
    def role(self):
        return self._role

    def order_accepted(self, order):
        pass

    def order_rejected(self, info, order):
        pass

    def _print_trade_opportunity(self, other_order):
        self.inform("[" + str(self.role()) + str(other_order))
    # ------ End of Helper and trivial methods -----


class MyOrder(Order):
    """
    This class should be implemented to have a better storage of current and past orders. And packing and sending
    orders will also be better implemented in this class, also interact with MyMarkets class
    """
    pass


class MyMarkets:
    """
    Market class that can parse market from dictionary form to a class form and provide extra-functionality to support
    putting orders into market.
    """
    def __init__(self, market_dict, logger_agent = None):
        if logger_agent:
            logger_agent.inform("Start converting market")
            logger_agent.inform("Currently logging market: "+repr(list(market_dict.items())))
        self.dict = market_dict
        self._time = time.time()
        self._id = market_dict["id"]
        self._min = market_dict["minimum"]
        self._max = market_dict["maximum"]
        self._tick = market_dict["tick"]
        self._name = market_dict["name"]
        self._item = market_dict["item"]
        self._description = market_dict["description"]

    @property
    def time(self):
        return self._time

    @property
    def id(self):
        return self._id

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def tick(self):
        return self._tick

    @property
    def name(self):
        return self._name

    @property
    def item(self):
        return self._item

    @property
    def description(self):
        return self._description

    def verify_order(self, order):
        pass

if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"
    FM_EMAIL = "z.huang51@student.unimelb.edu.au"
    FM_PASSWORD = "908525"
    MARKETPLACE_ID = 328  # replace this with the marketplace id

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    ds_bot.run()
