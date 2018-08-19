"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import time

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price", "888086": "Lee Jun Da"}

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


# Defining another enumeration for the status of orders
class OrderStatus(Enum):
    MADE = 1
    PENDING = 2
    ACCEPTED = 3
    COMPLETED = 4
    REJECTED = -1
    CANCEL = 0

# Dictionary to store letters in representation of a certain OrderType and OrderSide for reference of orders
ORDER_TYPE_TO_CHAR = {OrderType.LIMIT: "L", OrderType.CANCEL: "M"}
ORDER_SIDE_TO_CHAR = {OrderSide.BUY: "B", OrderSide.SELL: "S"}
SEPARATION = "-"        # for most string separation
TIME_FORMATTER = "%y" + SEPARATION + "%m" + SEPARATION + "%d" + \
                 SEPARATION + "%H" + SEPARATION + "%M" + SEPARATION + "%S"

class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id, name="DSBot")
        self._market_id = -1
        self._role = Role(0)
        self._bot_type = BotType(0)
        # For storing all markets available
        self._all_markets = {}

    def run(self):
        self.initialise()
        self.start()

    def initialised(self):
        for market_id, market_dict in self.markets.items():
            self._all_markets[market_id] = (MyMarkets(market_dict, self))
            self._market_id = market_id
            self.inform("Added market with id %d" % market_id)
        self.inform("Finished Adding markets, the current list of markets are: " + repr(self._all_markets))

        # --- Role of Bot ----
        cash_info = self.holdings["cash"]
        units_info = self.holdings["markets"][self._market_id]
        self.inform(cash_info)
        self.inform(units_info)
        if cash_info["cash"] == 0:
            self._role = Role(1)
            self.inform("Bot is a seller")
        else:
            self._role = Role(0)
            self.inform("Bot is a buyer")

    # ------ End of Constructor and initialisation methods -----

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        self.inform("received order book from %d" % market_id)

        for order in order_book:
            pass
        pass

    def received_marketplace_info(self, marketplace_info):
        pass

    # --- start nico ---
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
    # --- end nico ---


class MyOrder:
    """
    This class should be implemented to have a better storage of current and past orders. And packing and sending
    orders will also be better implemented in this class, also interact with MyMarkets class
    """
    # need to use __init__ and super()
    def __init__(self, price, units, order_type, order_side, market_id):
        # 1 is too simple, 2 is too complex. The time format should be compact and easy to parse
        # 1: now = time.strftime("%H:%M", time.localtime(time.time()))  e.g. '20:25'
        # 2: now = time.ctime(int(time.time()))                         e.g. 'Tue Aug 14 20:26:43 2018'
        # 3: now = strftime("%H:%M:%S", localtime())
        now = time.strftime(TIME_FORMATTER, time.localtime())  # year-month-day-hour-minute-second
        ref = ORDER_TYPE_TO_CHAR[order_type]+SEPARATION+ORDER_SIDE_TO_CHAR[order_side]+SEPARATION+str(now)
        self.price = price
        self.units = units
        self.order_type = order_type
        self.order_side = order_side
        self.market_id = market_id
        self.ref = ref
        self.status = OrderStatus["MADE"]
        self.sent_order = None
        # self.cancel_order = None

    def make_order(self):
        return Order(self.price, self.units, self.order_type, self.order_side, self.market_id, ref=self.ref)

    def send_order(self):
        if self.status == OrderStatus["MADE"]:
            self.sent_order = self.make_order()
            self.status = OrderStatus["PENDING"]
            self.sent_order.send_order()

        # found a more profitable trade, cancel previous to make new
        elif self.status == OrderStatus["ACCEPTED"]:
            pass  

    def cancel_sent_order(self):
        # if self.status in []
        pass

    def compare_order(self, other_order):
        if self.ref == other_order.ref:
            return True

class MyMarkets:
    """
    Market class that can parse market from dictionary form to a class form and provide extra-functionality to support
    putting orders into market.
    """
    def __init__(self, market_dict, logger_agent = None):
        if logger_agent:
            logger_agent.inform("Start converting market")
            logger_agent.inform("Currently logging market: "+repr(list(market_dict.items())))
        # These are only given property getter no other handles, for they are not supposed to be changed
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
    MARKETPLACE_ID = 352  # replace this with the marketplace id

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    ds_bot.run()
