"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import time

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price",
                 "888086": "Lee Jun Da"}

# ------ Add a variable called DS_REWARD_CHARGE -----
# Dependent on actual task, here set 500cents (5$) as the change
DS_REWARD_CHARGE = 500


# Enum for the roles of the bot
class Role(Enum):
    BUYER  = 0
    SELLER = 1


# Let us define another enumeration to deal with the type of bot
class BotType(Enum):
    MARKET_MAKER = 0
    REACTIVE     = 1


# Defining enumeration for the status of the bot
class BotStatus(Enum):
    UNABLE_UNITS_MAX = -1
    UNABLE_CASH_NONE =  0
    ACTIVE           =  1


# Defining another enumeration for the status of orders
# TODO match the new order status
class OrderStatus(Enum):
     PENDING  =  0   # Order sent but not confirmed
     ACTIVE   =  1   # Order confirmed but not traded
     INACTIVE = -1   # Order Canceled or Rejected


# Dictionary to store letters in representation of a certain OrderType
# and OrderSide for reference of orders
ORDER_TYPE_TO_CHAR = {OrderType.LIMIT: "L", OrderType.CANCEL: "M"}
ORDER_SIDE_TO_CHAR = {OrderSide.BUY: "B", OrderSide.SELL: "S"}
SEPARATION = "-"  # for most string separation
TIME_FORMATTER = "%y" + SEPARATION + "%m" + SEPARATION + "%d" + \
                 SEPARATION + "%H" + SEPARATION + "%M" + SEPARATION + "%S"


class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password,
                         marketplace_id, name="DSBot")
        self._market_id = -1
        self._bot_type = BotType(0)
        # For storing all markets available
        self._all_markets = {}
        # TODO Edit the self.status problem
        self.status = None
        self._role = None
        self._bot_status = BotStatus["ACTIVE"]

    def run(self):
        self.initialise()
        self.start()

    def initialised(self):
        for market_id, market_dict in self.markets.items():
            self._all_markets[market_id] = (MyMarkets(market_dict, self))
            self._market_id = market_id
            self.inform("Added market with id %d" % market_id)
        self.inform("Finished Adding markets, the "
                    "current list of markets are: " + repr(self._all_markets))

        self._role = self.get_role()

    # ------ End of Constructor and initialisation methods -----

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also
        cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        self.inform("Trying to send cancel order on non-existing orders")
        Order(500, 1, OrderType.CANCEL, OrderSide.SELL, )


        self.inform("received order book from %d" % market_id)

        # Task spec specify bot need to be either reactive or market maker,
        # not both depending on the type of bot, make orders when appropriate.
        # When the bid-ask spread is large, print can buy at Lowest sell price
        # or sell at highest buy price

        best_ask = None
        best_bid = None

        # Variable used to check whether our order was completed
        order_currently_pending = False

        self.inform("Printing order book")
        for order in order_book:
            self.inform("order is: %d, %d" % (order.price, order.units))
            if order.mine:
                self.inform("It's own order")
                order_currently_pending = True
                self.status = OrderStatus["PENDING"]

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

        try:
            bid_ask_spread = best_ask[0] - best_bid[0]
            self.inform("Spread is: " + str(bid_ask_spread))
        except TypeError:
            self.inform("no bid ask spread available")

        # If our order was not in the order book, but it was on the last
        # iteration (therefore complete or cancelled)
        if not order_currently_pending:
            # TODO change the order status
            self.status = OrderStatus["COMPLETED"]
            self.inform("Order was completed in market "
                        + str(self._market_id))

        # Bot is a market maker
        if self._bot_type == BotType["MARKET_MAKER"]:
            # Check that no order is currently pending
            if (self.status is None) or self.status != OrderStatus["PENDING"]:
                self.status = OrderStatus["MAKING"]
                self.inform("We can make a market-making order")
                self._market_maker_orders_price(best_ask[0], best_bid[0])
                print(market_id)

        if self._bot_type == BotType["REACTIVE"]:
            if self.status != OrderStatus["PENDING"]:
                self.status = OrderStatus["MAKING"]
                self.inform("We can make a reactive order")
                self._reactive_orders_price(best_bid, best_ask)

        self.inform(self.status)
        # Create bid-ask spread and check for depth of order
        # Depending on role, choose to buy or sell at relevant price

    def received_marketplace_info(self, marketplace_info):
        pass

    # --- start nico ---
    def received_completed_orders(self, orders, market_id=None):
        pass

    def received_holdings(self, holdings):
        """
        Read current holdings of account to make sure trade is possible
        :param holdings: Holdings of the account (Cash, Available Cash,
                         Units, Available units)
        :return: return holdings of account
        """
        cash_holdings = holdings["cash"]
        self.inform("Total cash: " + str(cash_holdings["cash"]) +
                    " available cash: " + str(cash_holdings["available_cash"]))
        for market_id, market_holding in holdings["markets"].items():
            self.inform("Market ID " + str(market_id) + ": total units: " +
                        str(market_holding["units"]) + ", available units: " +
                        str(market_holding["available_units"]))

        if self._role == Role["SELLER"]:
            if market_holding["available_units"] == 0:
                self._bot_status = BotStatus["UNABLE_UNITS_MAX"]
                self.inform("Role-Seller: No more available units, "
                            "unable to continue trade")
            else:
                self._bot_status = BotStatus["ACTIVE"]

        if self._role == Role["BUYER"]:
            if cash_holdings["available_cash"] == 0:
                self._bot_status = BotStatus["UNABLE_CASH_ZERO"]
                self.inform("Role-Buyer: No more available cash, "
                            "unable to continue trade")
            elif market_holding["units"] == 5:
                self._bot_status = BotStatus["UNABLE_UNITS_MAX"]
            else:
                self._bot_status = BotStatus["ACTIVE"]

    # ------ Helper and trivial methods -----
    def get_role(self):
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

    # TODO Edit the order status
    def order_accepted(self, order):
        self.inform("Order was accepted in market " + str(self._market_id))
        self.inform_server_order(order)
        # self.status = OrderStatus["PENDING"]
        pass

    # TODO Edit the order status
    def order_rejected(self, info, order):
        self.inform("Order was rejected in market " + str(self._market_id))
        self.inform_server_order(order)
        # self.status = OrderStatus["REJECTED"]
        pass

    def _print_trade_opportunity(self, other_order):
        """
        Depending on our role and our bot_type, print trade opportunity accordingly
        :param other_order: trade opportunities seen
        :return: self.inform() - let user know there is a good trade opportunity
        """

        self.inform("My Role is " + str(self._role) +
                    ". Current best trade opportunity would be buying at $" +
                    str(other_order / 100))
        if self._bot_status == BotStatus["ACTIVE"] and self.status ==\
                OrderStatus["PENDING"]:
            self.inform("Already have pending order in the Order Book.")
        if self._bot_status == BotStatus["UNABLE_UNITS_MAX"] or \
                self._bot_status == BotStatus["UNABLE_CASH_ZERO"]:
            if self._role == Role["BUYER"]:
                if self._bot_status == BotStatus["UNABLE_UNITS_MAX"]:
                    self.inform("Buyer has already bought 5 units.")
                elif self._bot_status == BotStatus["UNABLE_CASH_ZERO"]:
                    self.inform("Buyer has no more available cash left.")
            elif self._role == Role["SELLER"]:
                self.inform("Seller has no more available units left.")
    # ------ End of Helper and trivial methods -----
    # --- end nico ---

    def _market_maker_orders_price(self, best_ask, best_bid):
        """
        When the bot is a market maker, creates the order with class MyOrder
        """
        order_price = 0
        self.inform("best ask is: " + str(best_ask))
        self.inform("best bid is: " + str(best_bid))
        tick_size = int(self._all_markets[self._market_id]._tick)
        print(tick_size)
        # Bot is a buyer
        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            # Check if we can set a bid which beats the current best bid
            if best_bid + tick_size < DS_REWARD_CHARGE:
                order_price = best_bid + tick_size
            # Check if current best bid is profitable, but increasing the
            # bid makes it unprofitable
            elif best_bid < DS_REWARD_CHARGE:
                order_price = best_bid
            # Best buy price is 1 tick less than DS_REWARD_CHARGE
            else:
                order_price = DS_REWARD_CHARGE - tick_size

        # Bot is a seller
        if self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            # Check if we can set an ask which beats the current best ask
            if best_ask - tick_size > DS_REWARD_CHARGE:
                order_price = best_ask - tick_size
            # Check if current best ask is profitable, but decreasing the
            # ask makes it unprofitable
            elif best_ask > DS_REWARD_CHARGE:
                order_price = best_ask
            # Best ask price is 1 tick more than DS_REWARD_CHARGE
            else:
                order_price = DS_REWARD_CHARGE + tick_size

        self._print_trade_opportunity(order_price)
        if self._bot_status == BotStatus["ACTIVE"]:
            my_order = MyOrder(order_price, 1, OrderType.LIMIT, order_side,
                               self._market_id)
            my_order.send_order(self)

    # TODO fix the MyMarket problem
    def _reactive_orders_price(self, best_bid, best_ask, order_type):
        """
        When the bot is a reactive, creates the order with class MyOrder
        """
        order_price = 0
        self.inform("best ask is: " + str(best_ask))
        self.inform("best bid is: " + str(best_bid))

        # Bot is a buyer
        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY


        # Bot is a seller
        if self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            # Check if we can set an ask which beats the current best ask
            if best_ask - MyMarkets._tick > DS_REWARD_CHARGE:
                order_price = best_ask - MyMarkets._tick
            # Check if current best ask is profitable, but decreasing the ask
            # makes it unprofitable
            elif best_ask > DS_REWARD_CHARGE:
                order_price = best_ask
            # Best ask price is 1 tick more than DS_REWARD_CHARGE
            else:
                order_price = DS_REWARD_CHARGE + MyMarkets._tick

        my_order = MyOrder(order_price, 1, OrderType.LIMIT, order_side,
                           self._market_id)
        my_order.send_order(self)

    def inform_server_order(self, order):
        """
        This function prints the detail of sever returned orders
        :param order: object of Order class of fmclient
        :return: no return
        """
        self.inform("Order Detail\n" \
                    "      Price: %d\n" \
                    "      Units: %d\n" \
                    "      Type:  %s\n" \
                    "      Side:  %s\n" \
                    "      Ref:   %s\n" \
                    "      Id:    %d\n"
                    % (order.price,
                       order.units,
                       ORDER_TYPE_TO_CHAR[order.type],
                       ORDER_SIDE_TO_CHAR[order.side],
                       order.ref if order.ref else "No Ref",
                       order.id if order.id else -1))
#
#
# # TODO improve or remove the MyMarket
# class MarketHandler:
#     """
#     MarketHandler class that can parse market from dictionary form to a
#     class form and provide extra-functionality to support putting orders
#     into market.
#     """
#     class MyOrderHandler:
#         """
#         A handler class for MyOrder. It's linked with a certain market and
#         handle certain side of orders, error will be thrown if used for
#         different side of orders
#         """
#         class MyOrder:
#             """
#             This class should be implemented to have a better storage of
#             current and past orders. And packing and sending orders will
#             also be better implemented in this class, also interact with
#             MyMarkets class
#             """
#
#             def __init__(self, price, units, order_type, order_side,
#                          market_id, agent, show=False):
#                 """
#                 Initialize and send an order to the server!
#                 :param price: Price the order is traded at
#                 :param units: Units the order contains
#                 :param order_type: OrderType.LIMIT only
#                 :param order_side: OrderSide.BUY or SELL
#                 :param market_id:  Id of the market
#                 """
#                 self.time = time.localtime()
#
#                 # year-month-day-hour-minute-second
#                 now = time.strftime(TIME_FORMATTER, self.time)
#
#                 ref = ORDER_TYPE_TO_CHAR[order_type] + SEPARATION + \
#                       ORDER_SIDE_TO_CHAR[order_side] + SEPARATION + now
#
#                 self.price = price
#
#                 self.units = units
#
#                 self.active_units = units        # Number of units not traded
#
#                 self.order_type = order_type     # LIMIT or MARKET
#
#                 self.order_side = order_side     # SELL or BUY
#
#                 self.market_id = market_id
#
#                 self.ref = ref
#
#                 self.sent_order = None   # Keeps a record of the sent order
#
#                 self.cancel_order = None # Keeps a record of the canceled order
#
#                 self.id = None           # Keeps the server sent id of the
#                                          # order on order book
#
#                 self.date = None         # Keeps the server send date of the
#                                          # order
#
#                 self.agent = agent
#
#                 # Make and send the order
#                 self.sent_order = self._make_order(show)
#                 self._send_order()
#                 self.status = OrderStatus["PENDING"]
#
#             def _make_order(self, show=False):
#                 """
#                 Create the order of given detail
#                 :param show: If show the detail of order
#                 :return: None
#                 """
#                 if show:
#                     self.agent.inform("Making Order with ref" + self.ref)
#                 return Order(self.price, self.units, self.order_type,
#                              self.order_side, self.market_id, ref=self.ref)
#
#             def _send_order(self):
#                 self.agent.send_order(self.sent_order)
#
#             def cancel_order(self):
#                 # if self.status in []
#                 pass
#
#             def update_order(self, order):
#                 self.active_units = order.units
#
#
#
#             # ------ Start of magic methods -----
#             # These magic method definition should only be used on same side of trade
#             def __lt__(self, other):
#                 """
#                 define behavior of my_order < other, based on price/time
#                 priority i.e. True if my_order holds less priority than
#                 other!
#                 :param other: order order to compare with
#                 :return: True if this holds, False otherwise
#                 """
#
#                 # Both orders have to be the same side to compare
#                 assert self.order_side == other.order_side
#
#                 # If comparing with Order class members
#                 if isinstance(other, Order):
#                     # Have to be my own orders for a valid compare
#                     assert other.mine == True
#
#                 # If comparing BUY order
#                 if self.order_side == OrderSide.BUY:
#                     # For BUY order, higher price have higher priority
#                     if self.price < other.price:
#                         return True
#                     elif self.price > other.price:
#                         return False
#                     else:
#                         # For same price the smaller the price, the more priority
#                         if other.date is None:
#                             return False
#                         elif self.date is None:
#                             return True
#                         elif self.date > other.date:
#                             return True
#                         else:
#                             return False
#                 # If comparing SELL order
#                 if self.order_side == OrderSide.SELL:
#                     # For SELL order, lower price have higher priority
#                     if self.price > other.price:
#                         return True
#                     elif self.price < other.price:
#                         return False
#                     else:
#                         # For same price the smaller the price, the more priority
#                         if other.date is None:
#                             return False
#                         elif self.date is None:
#                             return True
#                         elif self.date > other.date:
#                             return True
#                         else:
#                             return False
#
#             def __gt__(self, other):
#                 """
#                 define behavior of my_order > other_order, based on
#                 price/time priority This is the exact opposite of __ls__
#                 :param other: order order to compare with
#                 :return: True if this holds, False otherwise
#                 """
#                 # Both orders have to be the same side to compare
#                 assert self.order_side == other.order_side
#
#                 # If comparing with Order class members
#                 if isinstance(other, Order):
#                     # Have to be my own orders for a valid compare
#                     assert other.mine == True
#
#                 # If comparing BUY order
#                 if self.order_side == OrderSide.BUY:
#                     # For BUY order, higher price have higher priority
#                     if self.price < other.price:
#                         return False
#                     elif self.price > other.price:
#                         return True
#                     else:
#                         # For same price the smaller the price, the more priority
#                         if other.date is None:
#                             return True
#                         elif self.date is None:
#                             return False
#                         elif self.date > other.date:
#                             return False
#                         else:
#                             return True
#                 # If comparing SELL order
#                 elif self.order_side == OrderSide.SELL:
#                     # For SELL order, lower price have higher priority
#                     if self.price > other.price:
#                         return True
#                     elif self.price < other.price:
#                         return False
#                     else:
#                         # For same price the smaller the price, the more priority
#                         if other.date is None:
#                             return False
#                         elif self.date is None:
#                             return True
#                         elif self.date > other.date:
#                             return True
#                         else:
#                             return False
#
#             def __eq__(self, other):
#                 """
#                 define behavior of my_order == other_order,based on
#                 price/time priority This should normally return just False,
#                 for no same order should be created twice!!
#                 :param other: order order to compare with
#                 :return: True if this holds, False otherwise
#                 """
#                 # Both orders have to be the same side to compare
#                 assert self.order_side == other.order_side
#                 if self.ref == other.ref:
#                     return True
#
#                 # If comparing with Order class members
#                 if isinstance(other, Order):
#                     # Have to be my own orders for a valid compare
#                     assert other.mine == True
#
#                 # TODO Potential problem when date is None
#                 if self.price == other.price and self.date == other.date:
#                     return True
#                 else:
#                     return False
#                 # ------ End of magic methods -----
#
#         def __init__(self, side, agent):
#             self.side = side          # Store the side of handler
#             self.active_orders = []   # Including pending and active orders
#             self.inactive_orders = [] # Including completed and canceled orders
#             self.agent = agent
#
#         def add_order(self, price, units, order_type, order_side, market_id):
#             order = self.MyOrder(price, units, order_type,
#                                  order_side, market_id)
#             self.active_orders.append(order)
#             self.active_orders = sorted(self.active_orders)
#
#         def update_order(self, order, order_status=None):
#             """
#             Update the order based on given argument, order can be MyOrder, or
#             Order from fmclient
#             :param order: Of Order class
#             :param order_status: OrderStatus class member
#             :return: No return
#             """
#             # When order_status is passed, meaning got accepted or rejected
#             if order_status:
#                 assert isinstance(order_status, OrderStatus)
#                 # Order accepted
#                 if order_status == OrderStatus["ACTIVE"]:
#                     for my_order in self.active_orders:
#                         # Found the match
#                         if my_order == order:
#                             my_order.status = order_status
#                             break
#                     else:
#                         self.agent.inform("DIDN'T find corresponding order "
#                                           "in active_order! ERROR")
#                 # Order rejected, then add it to the inactive list, and remove
#                 # from active list
#                 elif order_status == OrderStatus["INACTIVE"]:
#                     for i, my_order in enumerate(self.active_orders):
#                         if my_order == order:
#                             self.inactive_orders.append(my_order)
#                             self.active_orders = self.active_orders[:i] + \
#                                                  self.active_orders[(i+1):]
#
#             # Updating from order book
#             else:
#                 for i, my_order in enumerate(self.active_orders):
#                     # Found the target order
#                     if my_order == order:
#                         # The order have less active units than on market,
#                         # which is not possible
#                         if my_order.active_units < order.units:
#                             self.agent.inform("ERROR: Active units "
#                                               "not matching")
#                         else:
#                             my_order.active_units = order.units
#
#     def __init__(self, market_dict, logger_agent=None):
#         if logger_agent:
#             logger_agent.inform("Start converting market")
#             logger_agent.inform("Currently logging market: " +
#                                 repr(list(market_dict.items())))
#         # These are only given property getter no other handles,
#         # for they are not supposed to be changed
#         self.dict = market_dict         # Also storing original version
#         self.time = time.time()
#         self.id = market_dict["id"]
#         self.min = market_dict["minimum"]
#         self.max = market_dict["maximum"]
#         self.tick = market_dict["tick"]
#         self.name = market_dict["name"]
#         self.item = market_dict["item"]
#         self.description = market_dict["description"]
#
#         # Order handlers for updating own orders
#         self.sell_orders = self.MyOrderHandler(OrderSide.SELL)
#         self.buy_orders = self.MyOrderHandler(OrderSide.BUY)
#
#         # current order book
#         self.order_book = None
#
#     def verify_order(self, order):
#         pass
#
#
# if __name__ == "__main__":
#     FM_ACCOUNT = "bullish-delight"
#
#     FM_EMAIL_CALVIN = "z.huang51@student.unimelb.edu.au"
#     FM_PASSWORD_CALVIN = "908525"
#     FM_EMAIL_JUNDA = "j.lee161@student.unimelb.edu.au"
#     FM_PASSWORD_JUNDA = "888086"
#     MARKETPLACE_ID = 260  # replace this with the marketplace id
#
#     ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL_CALVIN, FM_PASSWORD_CALVIN, MARKETPLACE_ID)
#     ds_bot.run()
#
#
#
# """
# This is a template for Project 1, Task 1 (Induced demand-supply)
# """
#
# from enum import Enum
# from fmclient import Agent, OrderSide, Order, OrderType
# import time
#
# # ------ Add a variable called DS_REWARD_CHARGE -----
# # Dependent on actual task, here set 500cents (5$) as the change
# DS_REWARD_CHARGE = 500
#
#
# # Enum for the roles of the bot
# class Role(Enum):
#     BUYER  = 0
#     SELLER = 1
#
#
# # Let us define another enumeration to deal with the type of bot
# class BotType(Enum):
#     MARKET_MAKER = 0
#     REACTIVE     = 1
#
#
# # Defining enumeration for the status of the bot
# class BotStatus(Enum):
#     UNABLE_UNITS_MAX = -1
#     UNABLE_CASH_NONE =  0
#     ACTIVE           =  1
#
#
# # Defining another enumeration for the status of orders
# # TODO match the new order status
# class OrderStatus(Enum):
#     PENDING  =  0   # Order sent but not confirmed
#     ACTIVE   =  1   # Order confirmed but not traded
#     INACTIVE = -1   # Order Canceled or Rejected
#
#
# # Dictionary to store letters in representation of a certain OrderType
# # and OrderSide for reference of orders
# ORDER_TYPE_TO_CHAR = {OrderType.LIMIT: "L", OrderType.CANCEL: "M"}
# ORDER_SIDE_TO_CHAR = {OrderSide.BUY: "B", OrderSide.SELL: "S"}
# SEPARATION = "-"  # for most string separation
# TIME_FORMATTER = "%y" + SEPARATION + "%m" + SEPARATION + "%d" + \
#                  SEPARATION + "%H" + SEPARATION + "%M" + SEPARATION + "%S"
#
#
# # TODO improve or remove the MyMarket
# class MarketHandler:
#     """
#     MarketHandler class that can parse market from dictionary form to a
#     class form and provide extra-functionality to support putting orders
#     into market.
#     """
#     class MyOrderHandler:
#         """
#         A handler class for MyOrder. It's linked with a certain market and
#         handle certain side of orders, error will be thrown if used for
#         different side of orders
#         """
#         class MyOrder:
#             """
#             This class should be implemented to have a better storage of
#             current and past orders. And packing and sending orders will
#             also be better implemented in this class, also interact with
#             MyMarkets class
#             """
#
#             def __init__(self, price, units, order_type, order_side,
#                          market_id, agent, show=False):
#                 """
#                 Initialize and send an order to the server!
#                 :param price: Price the order is traded at
#                 :param units: Units the order contains
#                 :param order_type: OrderType.LIMIT only
#                 :param order_side: OrderSide.BUY or SELL
#                 :param market_id:  Id of the market
#                 """
#                 self.time = time.localtime()
#
#                 # year-month-day-hour-minute-second
#                 now = time.strftime(TIME_FORMATTER, self.time)
#
#                 ref = ORDER_TYPE_TO_CHAR[order_type] + SEPARATION + \
#                       ORDER_SIDE_TO_CHAR[order_side] + SEPARATION + now
#
#                 self.price = price
#
#                 self.units = units
#
#                 self.active_units = units        # Number of units not traded
#
#                 self.order_type = order_type     # LIMIT or MARKET
#
#                 self.order_side = order_side     # SELL or BUY
#
#                 self.market_id = market_id
#
#                 self.ref = ref
#
#                 self.sent_order = None    # Keeps record of the sent order
#
#                 self.cancel_order = None  # Keeps record of the canceled order
#
#                 self.id = None            # Keeps the server sent id of the
#                 # order on order book
#
#                 self.date = None          # Keeps the server send date of the
#                 # order
#
#                 self.agent = agent
#
#                 # Make and send the order
#                 self.sent_order = self._make_order(show)
#                 self._send_order()
#                 self.status = OrderStatus["PENDING"]
#
#             def _make_order(self, show=False):
#                 """
#                 Create the order of given detail
#                 :param show: If show the detail of order
#                 :return: None
#                 """
#                 if show:
#                     self.agent.inform("Making Order with ref" + self.ref)
#                 return Order(self.price, self.units, self.order_type,
#                              self.order_side, self.market_id, ref=self.ref)
#
#             def _send_order(self):
#                 self.agent.send_order(self.sent_order)
#
#             def cancel_order(self):
#                 # if self.status in []
#                 pass
#
#             def update_order(self, order):
#                 self.active_units = order.units
#
#             # ------ Start of magic methods -----
#             # These magic method definition should only be used on same
#             # side of trade
#             def __lt__(self, other):
#                 """
#                 define behavior of my_order < other, based on price/time
#                 priority i.e. True if my_order holds less priority than
#                 other!
#                 :param other: order order to compare with
#                 :return: True if this holds, False otherwise
#                 """
#
#                 # Both orders have to be the same side to compare
#                 assert self.order_side == other.order_side
#
#                 # If comparing with Order class members
#                 if isinstance(other, Order):
#                     # Have to be my own orders for a valid compare
#                     assert other.mine is True
#
#                 # If comparing BUY order
#                 if self.order_side == OrderSide.BUY:
#                     # For BUY order, higher price have higher priority
#                     if self.price < other.price:
#                         return True
#                     elif self.price > other.price:
#                         return False
#                     else:
#                         # For same price the smaller the price,
#                         # the more priority
#                         if other.date is None:
#                             return False
#                         elif self.date is None:
#                             return True
#                         elif self.date > other.date:
#                             return True
#                         else:
#                             return False
#                 # If comparing SELL order
#                 if self.order_side == OrderSide.SELL:
#                     # For SELL order, lower price have higher priority
#                     if self.price > other.price:
#                         return True
#                     elif self.price < other.price:
#                         return False
#                     else:
#                         # For same price the smaller the price,
#                         # the more priority
#                         if other.date is None:
#                             return False
#                         elif self.date is None:
#                             return True
#                         elif self.date > other.date:
#                             return True
#                         else:
#                             return False
#
#             def __gt__(self, other):
#                 """
#                 define behavior of my_order > other_order, based on
#                 price/time priority This is the exact opposite of __ls__
#                 :param other: order order to compare with
#                 :return: True if this holds, False otherwise
#                 """
#                 # Both orders have to be the same side to compare
#                 assert self.order_side == other.order_side
#
#                 # If comparing with Order class members
#                 if isinstance(other, Order):
#                     # Have to be my own orders for a valid compare
#                     assert other.mine == True
#
#                 # If comparing BUY order
#                 if self.order_side == OrderSide.BUY:
#                     # For BUY order, higher price have higher priority
#                     if self.price < other.price:
#                         return False
#                     elif self.price > other.price:
#                         return True
#                     else:
#                         # For same price the smaller the price, the more priority
#                         if other.date is None:
#                             return True
#                         elif self.date is None:
#                             return False
#                         elif self.date > other.date:
#                             return False
#                         else:
#                             return True
#                 # If comparing SELL order
#                 elif self.order_side == OrderSide.SELL:
#                     # For SELL order, lower price have higher priority
#                     if self.price > other.price:
#                         return True
#                     elif self.price < other.price:
#                         return False
#                     else:
#                         # For same price the smaller the price, the more priority
#                         if other.date is None:
#                             return False
#                         elif self.date is None:
#                             return True
#                         elif self.date > other.date:
#                             return True
#                         else:
#                             return False
#
#             def __eq__(self, other):
#                 """
#                 define behavior of my_order == other_order,based on
#                 price/time priority This should normally return just False,
#                 for no same order should be created twice!!
#                 :param other: order order to compare with
#                 :return: True if this holds, False otherwise
#                 """
#                 # Both orders have to be the same side to compare
#                 assert self.order_side == other.order_side
#                 if self.ref == other.ref:
#                     return True
#
#                 # If comparing with Order class members
#                 if isinstance(other, Order):
#                     # Have to be my own orders for a valid compare
#                     assert other.mine == True
#
#                 # TODO Potential problem when date is None
#                 if self.price == other.price and self.date == other.date:
#                     return True
#                 else:
#                     return False
#                 # ------ End of magic methods -----
#
#         def __init__(self, side, agent):
#             self.side = side          # Store the side of handler
#             self.active_orders = []   # Including pending and active orders
#             self.inactive_orders = [] # Including completed and canceled orders
#             self.agent = agent
#
#         def add_order(self, price, units, order_type, order_side, market_id):
#             order = self.MyOrder(price, units, order_type,
#                                  order_side, market_id)
#             self.active_orders.append(order)
#             self.active_orders = sorted(self.active_orders)
#
#         def update_order(self, order, order_status=None):
#             """
#             Update the order based on given argument, order can be MyOrder, or
#             Order from fmclient
#             :param order: Of Order class
#             :param order_status: OrderStatus class member
#             :return: No return
#             """
#             # When order_status is passed, meaning got accepted or rejected
#             if order_status:
#                 assert isinstance(order_status, OrderStatus)
#                 # Order accepted
#                 if order_status == OrderStatus["ACTIVE"]:
#                     for my_order in self.active_orders:
#                         # Found the match
#                         if my_order == order:
#                             my_order.status = order_status
#                             break
#                     else:
#                         self.agent.inform("DIDN'T find corresponding order "
#                                           "in active_order! ERROR")
#                 # Order rejected, then add it to the inactive list, and remove
#                 # from active list
#                 elif order_status == OrderStatus["INACTIVE"]:
#                     for i, my_order in enumerate(self.active_orders):
#                         if my_order == order:
#                             self.inactive_orders.append(my_order)
#                             self.active_orders = self.active_orders[:i] + \
#                                                  self.active_orders[(i+1):]
#
#             # Updating from order book
#             else:
#                 for i, my_order in enumerate(self.active_orders):
#                     # Found the target order
#                     if my_order == order:
#                         # The order have less active units than on market,
#                         # which is not possible
#                         if my_order.active_units < order.units:
#                             self.agent.inform("ERROR: Active units "
#                                               "not matching")
#                         else:
#                             my_order.active_units = order.units
#
#     def __init__(self, market_dict, agent, show=False):
#         if show:
#             agent.inform("Start converting market")
#             agent.inform("Currently logging market: " +
#                          str(list(market_dict.items())))
#         # These are only given property getter no other handles,
#         # for they are not supposed to be changed
#         self.dict = market_dict         # Also storing original version
#         self.time = time.time()
#         self.id = market_dict["id"]
#         self.min = market_dict["minimum"]
#         self.max = market_dict["maximum"]
#         self.tick = market_dict["tick"]
#         self.name = market_dict["name"]
#         self.item = market_dict["item"]
#         self.description = market_dict["description"]
#
#         # Order handlers for updating own orders
#         self.sell_orders = self.MyOrderHandler(OrderSide.SELL)
#         self.buy_orders = self.MyOrderHandler(OrderSide.BUY)
#
#         # current order book
#         self.order_book = None
#
#     def verify_order(self, order):
#         pass
#
#
# market_dict = {540:
#                    {"id": 540, "minimum":50, "maximum": 500, "tick": 5,
#                     "name": "Apples", "item": "Apple", "description": "Apples"}
#                }
#
# agent = "dummy"
# market = MarketHandler(market_dict)
# order = MarketHandler.MyOrderHandler.MyOrder(100, 1, OrderType.LIMIT,
#                                              OrderSide.SELL, 540, agent)
# market.sell_orders.append(order)
