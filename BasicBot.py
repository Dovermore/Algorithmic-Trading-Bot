"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import copy
import time

# For debugging only
import inspect

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price", "888086": "Lee Jun Da"}

# ------ Add a variable called DS_REWARD_CHARGE -----
# Dependent on actual task
DS_REWARD_CHARGE = 500

# The unit to place order
ORDER_UNIT = 1

# The MAGIC cancel number
MAGIC_MM_CANCEL_CYCLE = 10

# Dictionary to store letters in representation of a certain OrderType
# and OrderSide for reference of orders
ORDER_TYPE_TO_CHAR = {
    OrderType.LIMIT: "L",
    OrderType.CANCEL: "M"
}
ORDER_SIDE_TO_CHAR = {
    OrderSide.BUY: "B",
    OrderSide.SELL: "S"
}
ORDER_AVAILABILITY_TEMPLATE = {
    "five_units": None,         # Max 5 units is reached, only for buying
    "cash_available": None,     # Is cash enough to place this order
    "unit_available": None,     # Is unit enough to place this order
}
SEPARATION = "-"  # for most string separation
TIME_FORMATTER = "%y" + SEPARATION + "%m" + SEPARATION + "%d" + \
                 SEPARATION + "%H" + SEPARATION + "%M" + SEPARATION + "%S"


# Enum for the roles of the bot
class Role(Enum):
    BUYER = 0
    SELLER = 1


# Let us define another enumeration to deal with the type of bot
class BotType(Enum):
    MARKET_MAKER = 0
    REACTIVE = 1


# Status of current order if there is any
class OrderStatus(Enum):
    CANCEL = -1
    INACTIVE = 0       # None/Completed/Rejected/Canceled
    MADE = 0
    PENDING = 1
    ACCEPTED = 2


class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id, name="DSBot")

        # TBD later
        self._bot_type = BotType["REACTIVE"]

        self._role = None

        # This member variable take advantage of only one order at a time
        self.active_order = None
        self.order_status = OrderStatus["INACTIVE"]
        self.order_availability = copy.copy(ORDER_AVAILABILITY_TEMPLATE)
        self.mm_order_cycle = 0
        self.order_units = 0
        self.inactive_order = []

        # self.markets stores all market info
        self._market_id = None

    def run(self):
        self.initialise()
        self.start()

    def initialised(self):
        self.inform("Initialised, examining markets available")
        for market_id, market_dict in self.markets.items():
            self.inform(self._str_market(market_dict))
        self._market_id = list(self.markets.keys())[0]
        self._role = self._get_role()

    # ------ End of Constructor and initialisation methods -----

    def _process_order_book(self, order_book, all_orders=False):
        """
        Process the order book and return useful values of order_book
        :param order_book: List of Order objects to be processed
        :param all_orders: optional to return full list of order instead
                           of just best
        :return: list of mine orders
                 best bid order
                 best ask order
                 (
                 all buy_orders descending sorted
                 all sell_orders descending sorted
                 ) if all_orders is True
        """
        def key(order):
            try:
                return order.price
            except Exception as e:
                self.inform(e)

        self._line_break_inform(inspect.stack()[0][3])
        # Get own order
        mine_orders = [order for order in order_book if order.mine is True]

        # Sorted from most to least
        buy_orders = sorted([order for order in order_book
                             if order.side == OrderSide.BUY], key=key,
                            reverse=True)
        best_bid = buy_orders[0] if len(buy_orders) > 0 else None

        # Sorted from lease to most
        sell_orders = sorted([order for order in order_book
                              if order.side == OrderSide.SELL], key=key)
        best_ask = sell_orders[0] if len(sell_orders) > 0 else None

        if all_orders:
            return mine_orders, buy_orders, sell_orders
        return mine_orders, best_bid, best_ask

    def _update_mine_orders(self, mine_orders):
        """
        Based on extracted mine_orders, update own holding status
        :param mine_orders: list of mine orders, empty if none
        """
        self._line_break_inform(inspect.stack()[0][3])
        if len(mine_orders) == 1:
            if not self.order_status == OrderStatus["ACCEPTED"]:
                if self.order_status == OrderStatus["CANCEL"]:
                    self._warning_inform("Cancel order did not go through")
                else:
                    self._warning_inform("The order status didn't get updated to "
                                         "ACCEPTED in received_order_book")
            else:
                cancel_order = self._check_accepted_order(mine_orders[0])
                if cancel_order is not None:
                    self.inactive_order.append([self.active_order,
                                                cancel_order])
                    self.inform(self.inactive_order)
                    self.order_status = OrderStatus["CANCEL"]
        elif len(mine_orders) > 1:
            self._warning_inform("More than one active order!")
        elif self.order_status == OrderStatus["ACCEPTED"]:
            self.order_status = OrderStatus["INACTIVE"]
            self.inform("Order was completed in market " +
                        str(self._market_id))
        elif self.order_status == OrderStatus["PENDING"]:
            self._warning_inform("Order completed in pending state!")
            self.inform("Order was completed in market " +
                        str(self._market_id))

    def _check_accepted_order(self, order):
        """
        Check the status of last accepted order and potentially cancel based
        on status
        :return The canceled order if there is one
        """
        self._line_break_inform(inspect.stack()[0][3])
        try:
            if self._bot_type == BotType["REACTIVE"]:
                self.inform("Reactive order still in the Order Book")
                return self._cancel_sent_order(order)
            elif self._bot_type == BotType["MARKET_MAKER"]:
                if self.mm_order_cycle >= MAGIC_MM_CANCEL_CYCLE:
                    return self._cancel_sent_order(order)
        except Exception as e:
            return self.inform(e)

    def _get_bid_ask_spread(self, best_bid, best_ask, show=False):
        """
        Inform basic info about current bid/ask status, including bid-ask
        spread
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        :param show: True if want to show detail of best bid/ask orders
        """
        self._line_break_inform(inspect.stack()[0][3])
        if show:
            self.inform("Best bid:")
            self.inform(self.str_order(best_bid))
            self.inform("Best ask:")
            self.inform(self.str_order(best_ask))
            pass
        # Both bid and ask exist
        if best_bid is not None and best_ask is not None:
            bid_ask_spread = best_ask.price - best_bid.price
            self.inform("Spread is: " + str(bid_ask_spread))
            return bid_ask_spread
        else:
            self.inform("no bid ask spread available")
            if best_bid is None: self.inform("           Bid unavailable")
            if best_ask is None: self.inform("           Ask unavailable")

    def _take_action(self, best_ask, best_bid):
        """
        Take action based on best_ask and best_bid and market info.
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        """
        self._line_break_inform(inspect.stack()[0][3])

        # If there are currently no active orders
        if self.order_status == OrderStatus["INACTIVE"]:
            self.inform("Currently no active orders")
            if self._bot_type == BotType["MARKET_MAKER"]:
                self._market_maker_orders(best_ask, best_bid)
            elif self._bot_type == BotType["REACTIVE"]:
                self._reactive_orders(best_ask, best_bid)
            else:
                self._error_inform("Found bot with non-MM-REACTIVE type")
                self.stop = True
            self._send_update_active_order()

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also
        cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        self._line_break_inform(inspect.stack()[0][3])
        self.inform("received order book from %d" % market_id)

        if self.order_status == OrderStatus["ACCEPTED"]:
            self.mm_order_cycle += 1

        mine_orders, best_bid, best_ask = self._process_order_book(order_book)
        self._update_mine_orders(mine_orders)

        # Currently redundant variable
        bid_ask_spread = self._get_bid_ask_spread(best_bid, best_ask)

        self._take_action(best_ask, best_bid)
        self.inform("Current order status is: " + str(self.order_status))
        if self._bot_type == BotType["MARKET_MAKER"]:
            self.inform("Current mm_order_cycle is " +str(self.mm_order_cycle))
        # Create bid-ask spread and check for depth of order
        # Depending on role, choose to buy or sell at relevant price

    def received_marketplace_info(self, marketplace_info):
        session_id = marketplace_info["session_id"]
        if marketplace_info["status"]:
            print("Marketplace is now open with session id " + str(session_id))
        else:
            print("Marketplace is now closed.")

    def received_completed_orders(self, orders, market_id=None):
        pass

    def received_holdings(self, holdings):
        """
        Read current holdings of account to make sure trade is possible
        :param holdings: Holdings of the account (Cash, Available Cash, Units,
               Available units)
        """
        self._line_break_inform(inspect.stack()[0][3])
        cash_holdings = holdings["cash"]
        self.inform("Total cash: " + str(cash_holdings["cash"]) +
                    " available cash: " + str(cash_holdings["available_cash"]))
        for market_id, market_holding in holdings["markets"].items():
            self.inform("Market ID " + str(market_id) + ": total units: " +
                        str(market_holding["units"]) + ", available units: " +
                        str(market_holding["available_units"]))
        # self.holdings = holdings The holdings don't need to be set,
        # supposingly automatically

        # To check if holdings are consistent
        cash_info = self.holdings["cash"]
        units_info = self.holdings["markets"][self._market_id]
        self.inform("Total self.cash:" + str(cash_info))
        self.inform("Total self.units:" + str(units_info))

    # ------ Helper and trivial methods -----
    def _get_role(self):
        cash_info = self.holdings["cash"]
        units_info = self.holdings["markets"][self._market_id]
        self.inform(cash_info)
        self.inform(units_info)
        if cash_info["cash"] == 0:
            self.inform("Bot is a seller")
            return Role["SELLER"]
        else:
            self.inform("Bot is a buyer")
            return Role["BUYER"]

    def order_accepted(self, order):
        self._line_break_inform(inspect.stack()[0][3])
        self.inform("Order was accepted in market " + str(self._market_id))
        self.order_units += 1
        if self.order_status == OrderStatus["PENDING"]:
            self.order_status = OrderStatus["ACCEPTED"]
        elif self.order_status == OrderStatus["CANCEL"]:
            self.order_status = OrderStatus["INACTIVE"]
            self.inform("Cancel order ACCEPTED!!!")
        else:
            self._warning_inform("Order ACCEPTED from INACTIVE state!!!")

    def order_rejected(self, info, order):
        self._line_break_inform(inspect.stack()[0][3])
        self.inform("Order was rejected in market " + str(self._market_id))
        if self.order_status == OrderStatus["PENDING"]:
            self.inactive_order.append([self.active_order])
            self.active_order = None
            self.order_status = OrderStatus["INACTIVE"]
        elif self.order_status == OrderStatus["CANCEL"]:
            self._warning_inform("CANCEL order was REJECTED!!!")
        else:
            self._warning_inform("Order REJECTED from INACTIVE state!!!")

    def _print_trade_opportunity(self, other_order):
        """
        Depending on our role and our bot type, print trade opportunity.
        :param other_order: trade opportunities seen
        """
        self._line_break_inform(inspect.stack()[0][3])
        try:
            if other_order and isinstance(other_order, Order):

                # From the given template
                self.inform("[" + str(self._role) + str(other_order))

                # TODO if BUYER, are we going to stop the bot from trading when it reaches 5 units?
                if self._role == Role["BUYER"]:
                    self.inform("Bot is a buyer")
                    if self.order_availability["cash_available"] is True and \
                            self.order_availability["five_units"] is True:
                        addition_info = "can respond to the order."
                    elif self.order_availability["cash_available"] is False:
                        addition_info = ("can not respond to the order "
                                         "due to limited cash")
                    elif self.order_availability["five_units"] is False:
                        addition_info = ("can not respond to the order as "
                                         "we have already bought 5 units")
                    else:
                        addition_info = ("Malfunctioning due to incorrect "
                                         "type given to cash_availability")
                elif self._role == Role["SELLER"]:
                    self.inform("Bot is a seller")
                    if self.order_availability["unit_available"] is True:
                        self.inform("can be sold")
                        addition_info = "can respond to the order."
                    elif self.order_availability["unit_available"] is False:
                        self.inform("can't be sold")
                        addition_info = ("can not respond to the order "
                                         "due to limited units")
                    else:
                        addition_info = ("Malfunctioning due to incorrect "
                                         "type given to unit_availability")
                else:
                    self._error_inform("The bot have unidentified _role!")
                    self.stop = True
                self.inform("The bot %s" % addition_info)
        except Exception as e:
            self.inform(e)

    # TODO this is not used, can be deleted, functionality done in received_holdings
    def _available_cash_units(self):
        """
        Check if enough cash or units to make purchase or sale
        :return: True if enough, False if not enough
        """
        available_cash = self.holdings["cash"]["available_cash"]
        available_units = self.holdings["markets"]\
            [self._market_id]["available_units"]
        self.inform("Available cash: " + str(available_cash))
        self.inform("Available units: " + str(available_units))
        if self._role == Role["BUYER"] and not available_units < 5:
            self._warning_inform("Have bought 5 units, "
                                 "additional units are not profitable")
            return False
        elif self._role == Role["SELLER"] and not available_units > 0:
            self._warning_inform("Do not have anymore units to trade")
            return False
        else:
            return True

    # TODO _check_previous_order_price is not used too
    def _check_previous_order_price(self, order_price):
        """
        Check if order price to be made is better or worse than the previous order
        :param order_price: order price to be made
        :return: True if criteria met, False if criteria not met
        """
        if self.active_order:
            previous_price = self.active_order.price
            if self._role == Role["BUYER"]:
                return True if previous_price > order_price else False
            elif self._role == Role["SELLER"]:
                return True if previous_price > order_price else False
        else:
            return True

    def _cancel_sent_order(self, order):
        self._line_break_inform(inspect.stack()[0][3])
        # First check order status before canceling
        if self.order_status in [OrderStatus["PENDING"],
                                 OrderStatus["ACCEPTED"]]:
            self.inform("Able to cancel order")
            cancel_order = copy.copy(order)
            cancel_order.type = OrderType.CANCEL
            cancel_order.ref = self._make_order_ref(
                self._market_id, self.active_order.price,
                self.active_order.side, self.active_order.units,
                OrderType.CANCEL
            )
            self.send_order(cancel_order)
            # Reset the cycle
            self.mm_order_cycle = 0
            # Reset the active order
            self.active_order = None
            return cancel_order
        else:
            self._warning_inform("Order cancelled while "
                                 "not PENDING or ACCEPTED!")
            return None

    @staticmethod
    def _make_order_ref(market_id, order_price, order_side,
                        order_unit=ORDER_UNIT, order_type=OrderType.LIMIT):
        ref = ORDER_SIDE_TO_CHAR[order_side] + SEPARATION
        ref += str(market_id) + SEPARATION
        ref += str(order_price) + SEPARATION
        ref += str(order_side) + SEPARATION
        ref += str(order_unit) + SEPARATION
        ref += time.strftime(TIME_FORMATTER, time.localtime())
        ref += ORDER_TYPE_TO_CHAR[order_type] + SEPARATION
        return ref

    def _make_order(self, order_price, order_side, order_unit=ORDER_UNIT,
                    order_type=OrderType.LIMIT):
        """
        MAKES order and stores in active order
        :param order_price: price made after decision
        :param order_side: buyer or seller
        :param order_unit: (Optional, not available) Traded units
        :param order_type: (Optional, not available) Type of order
        :return: sends order
        """
        self._line_break_inform(inspect.stack()[0][3])
        ref = self._make_order_ref(self._market_id, order_price, order_side)
        self.active_order = Order(order_price, order_unit, order_type,
                                  order_side, self._market_id, ref=ref)
        self.order_status = OrderStatus["MADE"]

    def _verify_active_order(self):
        """
        Verify current active order (against current market)and return a
        dictionary containing the information
        """
        self._line_break_inform(inspect.stack()[0][3])
        if self.order_status != OrderStatus["MADE"]:
            self._warning_inform("Verifying NON-MADE order")

        order_availability = copy.copy(ORDER_AVAILABILITY_TEMPLATE)
        if self.active_order and isinstance(self.active_order, Order):
            # BUY side
            if self.active_order.side == OrderSide.BUY:
                # Not enough mana
                if (self.active_order.price * self.active_order.units >
                        self.holdings["cash"]["available_cash"]):
                    order_availability["cash_available"] = False
                elif self.order_units > 5:
                    order_availability["five_units"] = False
                else:
                    order_availability["cash_available"] = True
                    order_availability["five_units"] = True
            # SELL side
            elif self.active_order.side == OrderSide.SELL:
                if (self.active_order.units > self.holdings["markets"]
                [self._market_id]["available_units"]):
                    order_availability["unit_available"] = False
                else:
                    order_availability["unit_available"] = True
            else:
                self._error_inform("Found order with non-BUY-SELL type")
                self.stop = True
        else:
            if self._bot_type == BotType["REACTIVE"]:
                self.inform("No profitable trades are available")
            else:
                self._warning_inform("Trying to verify NONE order")
        self.order_availability = order_availability

    def _send_update_active_order(self):
        """
        MAKE --> VERIFY --> PRINT(with verified message) --> SEND
        :return:
        """
        self._line_break_inform(inspect.stack()[0][3])
        self._verify_active_order()
        self._print_trade_opportunity(self.active_order)
        if (self.order_availability["cash_available"] is True and
                self.order_availability["five_units"] is True) or \
                self.order_availability["unit_available"] is True:
            self.inform("Sending order")
            self.send_order(self.active_order)
            self.order_status = OrderStatus["PENDING"]

    def _market_maker_orders(self, best_ask, best_bid):
        """
        When bot is set to market maker, this function creates the appropriate order
        :param best_ask: Best ask price by the market
        :param best_bid: Best bid price by the market
        :return: no return
        """
        self._line_break_inform(inspect.stack()[0][3])
        tick_size = self.markets[self._market_id]["tick"]

        minimum = self.markets[self._market_id]["minimum"]
        maximum = self.markets[self._market_id]["maximum"]
        tick = self.markets[self._market_id]["tick"]

        order_price = None
        order_side = None
        # Bot is a buyer
        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            if best_bid is None:
                order_price = ((DS_REWARD_CHARGE - minimum) //
                               tick // 2 * tick) + minimum
            # Check if we can set a bid which beats the current best bid
            elif best_bid.price + tick_size < DS_REWARD_CHARGE:
                order_price = best_bid.price + tick_size
            # Check if current best bid is profitable,
            # but increasing the bid makes it unprofitable
            elif best_bid.price < DS_REWARD_CHARGE:
                order_price = best_bid.price
            # Best buy price is 1 tick less than DS_REWARD_CHARGE
            else:
                order_price = ((DS_REWARD_CHARGE - minimum) //
                               tick * tick) + minimum

        # Bot is a seller
        elif self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            if best_ask is None:
                order_price = maximum - ((maximum - DS_REWARD_CHARGE)
                                         // tick // 2 * tick)
            # Check if we can set an ask which beats the current best ask
            elif best_ask.price - tick_size > DS_REWARD_CHARGE:
                order_price = best_ask.price - tick_size
            # Check if current best ask is profitable, but
            # decreasing the ask makes it unprofitable
            elif best_ask.price > DS_REWARD_CHARGE:
                order_price = best_ask.price
            # Best ask price is 1 tick more than DS_REWARD_CHARGE
            else:
                order_price = maximum - ((maximum - DS_REWARD_CHARGE)
                                         // tick * tick)

        else:
            self._error_inform("Found order with non-BUY-SELL type")
            self.stop = True

        if order_price:
            self._make_order(order_price, order_side)

    def _reactive_orders(self, best_ask, best_bid, show=False):
        """
        When bot is set to reactive, make orders using this
        :param best_ask: Best ask price by the market
        :param best_bid: Best bid price by the market
        :return: makes order according to role
        """
        self._line_break_inform(inspect.stack()[0][3])
        order_price = None
        order_side = None

        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            if best_ask is None:
                if show: self.inform("No orders can be made!"
                                     "Will continue wait for orders...")

                if show: self.inform("No orders can be made! Will "
                                     "continue wait for orders...")
            elif best_ask.price < DS_REWARD_CHARGE:
                order_price = best_ask.price
                if show: self.inform("Found an order!!! Making order now...")
            else:
                if show: self.inform("No good trade can be done right now")
        elif self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            if best_bid is None:
                if show: self.inform("No orders can be made!"
                                     "Will continue wait for orders...")
                if show: self.inform("No orders can be made! Will "
                                     "continue wait for orders...")
            elif best_bid.price > DS_REWARD_CHARGE:
                order_price = best_bid.price
                if show: self.inform("Found an order!!! Making order now...")
            else:
                if show: self.inform("No good trade can be done right now")
        if order_price:
            self._make_order(order_price, order_side)

    def _warning_inform(self, msg):
        """
        INFORM warning message
        """
        self.inform("***WARNING***\n"
                    "       %s" % msg)

    def _error_inform(self, msg):
        """
        INFORM error message
        """
        self.inform("@@@ERROR@@@\n"
                    "       %s" % msg)

    def _line_break_inform(self, msg="", char="-", rep=79):
        """
        Simply inform a line break with certain character
        :param char: The character to be repeated
        :param rep: The number of repetition char would be repeated
        """
        len_char = rep - len(msg)
        len_left = rep // 2
        len_right = len_char - len_left
        self.inform("".join([char] * len_left) +
                    msg + "".join([char] * len_right))

    @staticmethod
    def _str_market(market):
        """
        This is a staticmethod that returns the string representation of detail
        of a market
        :param market: Dictionary of a market to be turned into string
        """
        try:
            return ("Market: %d\n"
                    "       Minimum: %3d\n"
                    "       Maximum: %3d\n"
                    "       Tick   : %3d\n"
                    "       Name   : %s\n"
                    "       Item   : %s\n"
                    "       Describ: %s\n" % \
                    (market["id"], market["minimum"], market["maximum"],
                     market["tick"], market["name"], market["item"],
                     market["description"]))
        except Exception as e:
            return e

    @staticmethod
    def str_order(order):
        """
        This function return string representation of the detail of orders
        :param order: object of Order class of fmclient
        """
        try:
            if order is not None:
                return ("Order Detail\n" \
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
            else:
                return ("Order Detail\n"
                        "      Order is None")
        except Exception as e:
            return e


if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"

    FM_EMAIL_CALVIN = "z.huang51@student.unimelb.edu.au"
    FM_PASSWORD_CALVIN = "908525"

    FM_EMAIL_JD = "j.lee161@student.unimelb.edu.au"
    FM_PASSWORD_JD = "888086"

    MARKETPLACE_ID = 352  # replace this with the marketplace id

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL_JD, FM_PASSWORD_JD, MARKETPLACE_ID)
    ds_bot.run()
