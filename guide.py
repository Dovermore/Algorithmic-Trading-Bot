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


# Defining enumeration for the status of the bot
class BotStatus(Enum):
    UNABLE_UNITS_MAX = -1
    UNABLE_CASH_NONE = 0
    ACTIVE = 1


# Defining another enumeration for the status of orders
class OrderStatus(Enum):
    ACTIVE = 1     # ORDER IS IN THE ORDER BOOK
    INACTIVE = 0   # ORDER IS NOT IN THE ORDER BOOK


# Dictionary to store letters in representation of a certain OrderType and OrderSide for reference of orders
ORDER_TYPE_TO_CHAR = {OrderType.LIMIT: "L", OrderType.CANCEL: "M"}
ORDER_SIDE_TO_CHAR = {OrderSide.BUY: "B", OrderSide.SELL: "S"}
SEPARATION = "-"  # for most string separation
TIME_FORMATTER = "%y" + SEPARATION + "%m" + SEPARATION + "%d" + \
                 SEPARATION + "%H" + SEPARATION + "%M" + SEPARATION + "%S"


class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id, name="DSBot")
        self._market_id = -1
        self._bot_type = BotType(0)
        # For storing all markets available
        self._all_markets = {}
        self.order_status = OrderStatus["INACTIVE"]
        self.bot_status = BotStatus["ACTIVE"]

    def run(self):
        self.initialise()
        self.start()

    def initialised(self):
        for market_id, market_dict in self.markets.items():
            self._all_markets[market_id] = (MyMarkets(market_dict, self))
            self._market_id = market_id
            self.inform("Added market with id %d" % market_id)
        self.inform("Finished Adding markets, the current list of markets are: " + repr(self._all_markets))

        self._role = self.role()
        self.inform(self._bot_type)

    # ------ End of Constructor and initialisation methods -----

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        self.inform("received order book from %d" % market_id)

        # Task spec specify bot need to be either reactive or market maker, not both
        # depending on the type of bot, make orders when appropriate.
        # When the bid-ask spread is large, print can buy at Lowest sell price or sell at highest buy price

        best_ask = None
        best_bid = None
        my_order_price = None

        # Variable used to check whether our order was completed
        order_currently_pending = False

        for order in order_book:
            if order.mine:
                order_currently_pending = True
                self.order_status = OrderStatus["ACTIVE"]
                my_order_price = order.price

            price = order.price
            units = order.units

            if order.side == OrderSide.SELL:
                # determine which is lowest ASK price
                if best_ask is None:
                    best_ask = (price, units)
                else:
                    if price < best_ask[0]:
                        best_ask = (price, units)

            elif order.side == OrderSide.BUY:
                # determine which is highest BID price
                if best_bid is None:
                    best_bid = (price, units)
                else:
                    if price > best_bid[0]:
                        best_bid = (price, units)

        # If our order was not in the order book, but it was on the last iteration (therefore complete or cancelled)
        if not order_currently_pending and self.order_status == OrderStatus["ACTIVE"]:
            self.order_status = OrderStatus["INACTIVE"]
            self.inform("Order was completed in market " + str(self._market_id))

        try:
            bid_ask_spread = best_ask[0] - best_bid[0]
            self.inform("Spread is: " + str(bid_ask_spread))
        except TypeError:
            self.inform("no bid ask spread available")

        # Bot is a market maker
        if self._bot_type == BotType["MARKET_MAKER"]:
            # Check that no order is currently pending
            if self.order_status == OrderStatus["INACTIVE"]:
                self.inform("We can make a market maker order")
                self._market_maker_orders(best_ask, best_bid)

        # Bot is a reactive
        elif self._bot_type == BotType["REACTIVE"]:
            self._reactive_orders(best_ask, best_bid, my_order_price)

        self.inform(str(self.order_status) + " in market " + str(self._market_id))

    def received_marketplace_info(self, marketplace_info):
        pass

    # --- start nico ---
    def received_completed_orders(self, orders, market_id=None):
        pass

    def received_holdings(self, holdings):
        """
        Read current holdings of account to make sure trade is possible
        :param holdings: Holdings of the account (Cash, Available Cash, Units, Available units)
        :return: return holdings of account
        """
        cash_holdings = holdings["cash"]
        self.inform("Total cash: " + str(cash_holdings["cash"]) +
                    " available cash: " + str(cash_holdings["available_cash"]))
        for market_id, market_holding in holdings["markets"].items():
            self.inform("Market ID " + str(market_id) + ": total units: " +
                        str(market_holding["units"]) + ", available units: " + str(market_holding["available_units"]))


    # ------ Helper and trivial methods -----
    def role(self):
        cash_info = self.holdings["cash"]
        units_info = self.holdings["markets"][self._market_id]
        self.inform(cash_info)
        self.inform(units_info)
        if cash_info["cash"] == 0:
            self.inform("Bot is a seller")
            return Role(1)
        else:
            self.inform("Bot is a buyer")
            return Role(0)

    def order_accepted(self, order):
        self.inform("Order was accepted in market " + str(self._market_id))
        self.order_status = OrderStatus["ACTIVE"]
        pass

    def order_rejected(self, info, order):
        self.inform("Order was rejected in market " + str(self._market_id))
        self.order_status = OrderStatus["INACTIVE"]
        pass

    def _print_trade_opportunity(self, other_order):
        """
        Depending on our role and our bottype, print trade opportunity accordingly
        :param other_order: trade opportunities seen
        :return: self.inform() - let user know there is a good trade opportunity
        """
        if self.bot_status == BotStatus["ACTIVE"]:
            return self.inform("My Role is " + str(self._role) + ". Current best trade opportunity would be buying at $"
                               + str(other_order / 100))
        elif self.bot_status == BotStatus["UNABLE_UNITS_MAX"] or self.bot_status == BotStatus["UNABLE_CASH_ZERO"]:
            if self._role == Role["BUYER"]:
                if self.bot_status == BotStatus["UNABLE_UNITS_MAX"]:
                    status = "Buyer has already bought 5 units."
                elif self.bot_status == BotStatus["UNABLE_CASH_ZERO"]:
                    status = "Buyer has no more available cash left."
            elif self._role == Role["SELLER"]:
                status = "Seller has no more available units left."
            return self.inform("My Role is " + str(self._role) + ". Current best trade opportunity would be buying at $"
                               + str(other_order / 100) + ". " + status)

    def _market_maker_orders(self, best_ask, best_bid):
        """
        When bot is set to market maker, this function creates the appropriate order
        :param best_ask: Best ask price by the market
        :param best_bid: Best bid price by the market
        :return: no return
        """
        self.inform("best ask is: " + str(best_ask))
        self.inform("best bid is: " + str(best_bid))
        tick_size = self._all_markets[self._market_id]._tick

        order_price = None
        order_side = None

        # Bot is a buyer
        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            if best_bid is None:
                order_price = int(DS_REWARD_CHARGE/2)
            # Check if we can set a bid which beats the current best bid
            elif best_bid[0] + tick_size < DS_REWARD_CHARGE:
                order_price = best_bid[0] + tick_size
            # Check if current best bid is profitable, but increasing the bid makes it unprofitable
            elif best_bid[0] < DS_REWARD_CHARGE:
                order_price = best_bid[0]
            # Best buy price is 1 tick less than DS_REWARD_CHARGE
            else:
                order_price = DS_REWARD_CHARGE - tick_size

        # Bot is a seller
        elif self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            if best_ask is None:
                order_price = int(DS_REWARD_CHARGE * 1.5)
            # Check if we can set an ask which beats the current best ask
            elif best_ask[0] - tick_size > DS_REWARD_CHARGE:
                order_price = best_ask[0] - tick_size
            # Check if current best ask is profitable, but decreasing the ask makes it unprofitable
            elif best_ask[0] > DS_REWARD_CHARGE:
                order_price = best_ask[0]
            # Best ask price is 1 tick more than DS_REWARD_CHARGE
            else:
                order_price = DS_REWARD_CHARGE + tick_size

        self._print_trade_opportunity(order_price)
        if self.bot_status == BotStatus["ACTIVE"] and order_price:
            my_order = MyOrder(order_price, 1, OrderType.LIMIT, order_side, self._market_id)
            my_order.send_order(self)

    def _reactive_orders(self, best_ask, best_bid, my_order_price):
        """
        When bot is set to reactive, make orders using this
        :param best_ask: Best ask price by the market
        :param best_bid: Best bid price by the market
        :return: makes order according to role
        """
        self.inform("best ask is: " + str(best_ask))
        self.inform("best bid is: " + str(best_bid))

        order_price = None
        order_side = None

        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            if best_ask is None:
                self.inform("No ask price to trade with")
            elif best_ask[0] < DS_REWARD_CHARGE:
                order_price = best_ask[0]

            try:
                if order_price > my_order_price:
                    order_price = None
                    self.inform("Opportunity found not better")
            except TypeError:
                pass

        elif self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            if best_bid is None:
                self.inform("No bid price to trade with")
            elif best_bid[0] > DS_REWARD_CHARGE:
                order_price = best_bid[0]

            try:
                if order_price < my_order_price:
                    order_price = None
                    self.inform("Opportunity found not better")
            except TypeError:
                pass

        if order_price:
            self._print_trade_opportunity(order_price)

        if self.bot_status == BotStatus["ACTIVE"] and order_price:
            my_order = MyOrder(order_price, 1, OrderType.LIMIT, order_side, self._market_id)
            my_order.send_order(self)


class MyOrder:
    """
    This class should be implemented to have a better storage of current and past orders. And packing and sending
    orders will also be better implemented in this class, also interact with MyMarkets class
    """

    # need to use __init__ and super()
    def __init__(self, price, units, order_type, order_side, market_id):
        now = time.strftime(TIME_FORMATTER, time.localtime())  # year-month-day-hour-minute-second
        ref = ORDER_TYPE_TO_CHAR[order_type] + SEPARATION + ORDER_SIDE_TO_CHAR[order_side] + SEPARATION + str(now)
        self.price = price
        self.units = units
        self.order_type = order_type
        self.order_side = order_side
        self.market_id = market_id
        self.ref = ref
        self.sent_order = None
        # self.cancel_order = None

    def test_active(self, agent):
        if agent.order_status == OrderStatus["INACTIVE"]:
            return True

        elif agent.order_status == OrderStatus["ACTIVE"]:
            agent.inform("Cancelling order with ref " + self.ref)
            self.sent_order = self.cancel_sent_order(agent)
            agent.send_order(self.sent_order)
            agent.inform("Cancelled previous order with ref " + self.ref)
            agent.order_status = OrderStatus["INACTIVE"]
            return True

    def make_order(self, agent=None):
        if agent:
            agent.inform("Making Order with ref" + self.ref)
        return Order(self.price, self.units, self.order_type, self.order_side, self.market_id, ref=self.ref)

    def send_order(self, agent):
        if self.test_active(agent):
            agent.order_status = OrderStatus["ACTIVE"]
            self.sent_order = self.make_order(agent)
            agent.inform("Sending Order with ref " + self.ref)
            agent.send_order(self.sent_order)
            agent.inform('Sent Order with ref ' + self.ref)

    def cancel_sent_order(self, agent=None):
        self.order_type = OrderType.CANCEL
        self.sent_order = self.make_order(agent)
        agent.inform("Making cancel order for order with ref " + self.ref)
        return Order(self.price, self.units, self.order_type, self.order_side, self.market_id, ref=self.ref)


class MyMarkets:
    """
    Market class that can parse market from dictionary form to a class form and provide extra-functionality to support
    putting orders into market.
    """

    def __init__(self, market_dict, logger_agent=None):
        if logger_agent:
            logger_agent.inform("Start converting market")
            logger_agent.inform("Currently logging market: " + repr(list(market_dict.items())))
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
    junda = "j.lee161@student.unimelb.edu.au"
    FM_PASSWORD = "908525"
    junda_pass = "888086"
    MARKETPLACE_ID = 352 # replace this with the marketplace id

    ds_bot = DSBot(FM_ACCOUNT, junda, junda_pass, MARKETPLACE_ID)
    ds_bot.run()
