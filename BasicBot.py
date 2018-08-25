"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import copy
import time, datetime

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price", "888086": "Lee Jun Da"}

# ------ Add a variable called DS_REWARD_CHARGE -----
# Dependent on actual task
DS_REWARD_CHARGE = 500

# The unit to place order
ORDER_UNIT = 1

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
    "profit": None,           # Amount of profit made by completing this order
    "cash_available": None,   # Is cash enough to place this order
    "unit_available": None,   # Is unit enough to place this order
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
    INACTIVE = 0       # None/Completed/Rejected/Canceled
    MADE = 0
    PENDING = 1
    ACCEPTED = 2


class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id, name="DSBot")

        # TBD later
        self._bot_type = None

        self._role = None

        # This member variable take advantage of only one order at a time
        self.active_order = None
        self.order_status = OrderStatus["INACTIVE"]
        self.order_availability = copy(ORDER_AVAILABILITY_TEMPLATE)

        self.inactive_order = []

        # self.markets stores all market info
        self._market_id = None

    def run(self):
        self.initialise()
        self.start()

    def initialised(self):
        self.inform("Initialised, examining markets available")
        for market_id, market_dict in self.markets.items():
            self.inform(self.str_market(market_dict))
        self._market_id = list(self.markets.keys())[0]
        self._role = self.get_role()

    # ------ End of Constructor and initialisation methods -----

    def process_order_book(self, order_book, all_orders=False):
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

    def update_mine_orders(self, mine_orders):
        """
        Based on extracted mine_orders, update own holding status
        :param mine_orders: list of mine orders, empty if none
        """
        if len(mine_orders) == 1:
            if not self.order_status == OrderStatus["ACCEPTED"]:
                self.warning_inform("The order status didn't get updated to "
                                    "ACCEPTED in received_order_book")

        elif len(mine_orders) > 1:
            self.warning_inform("More than one active order!!!!!")
        elif self.order_status == OrderStatus["ACCEPTED"]:
            self.inform("Order was completed in market " +
                        str(self._market_id))
        elif self.order_status == OrderStatus["PENDING"]:
            self.warning_inform("Order completed in pending state!")
            self.inform("Order was completed in market " +
                        str(self._market_id))

    def get_bid_ask_spread(self, best_bid, best_ask, show=False):
        """
        Inform basic info about current bid/ask status, including bid-ask
        spread
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        :param show: True if want to show detail of best bid/ask orders
        """
        if show:
            # TODO print best bid and ask
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

    def take_action(self, best_ask, best_bid):
        """
        Take action based on best_ask and best_bid and market info.
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        """
        self.line_break_inform()

        # If there are currently no active orders
        if self.order_status == OrderStatus["INACTIVE"]:
            self.inform("Currently no active orders")
            self._market_maker_orders(best_ask, best_bid) if \
                self._bot_type == BotType["MARKET_MAKER"] else \
                self._reactive_orders(best_ask, best_bid)

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also
        cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        self.inform("received order book from %d" % market_id)

        # Task spec specify bot need to be either reactive or market maker,
        # not both depending on the type of bot, make orders when appropriate.
        # When the bid-ask spread is large, print can buy at Lowest ask price
        # or sell at highest bid price
        mine_orders, best_bid, best_ask = self.process_order_book(order_book)
        self.update_mine_orders(mine_orders)

        # Currently redundant variable
        bid_ask_spread = self.get_bid_ask_spread(best_bid, best_ask)

        self.take_action(best_ask, best_bid)

        self.inform("Current order status is: " + str(self.order_status))
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
        cash_holdings = holdings["cash"]
        self.inform("Total cash: " + str(cash_holdings["cash"]) +
                    " available cash: " + str(cash_holdings["available_cash"]))
        for market_id, market_holding in holdings["markets"].items():
            self.inform("Market ID " + str(market_id) + ": total units: " +
                        str(market_holding["units"]) + ", available units: " +
                        str(market_holding["available_units"]))
        # self.holdings = holdings The holdings don't need to be set,
        # supposingly automatically

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

    def order_accepted(self, order):
        self.inform("Order was accepted in market " + str(self._market_id))
        if self.order_status == OrderStatus["PENDING"]:
            self.order_status = OrderStatus["ACCEPTED"]
        else:
            self.error_inform("Order ACCEPTED from INACTIVE state!!!")

    def order_rejected(self, info, order):
        self.inform("Order was rejected in market " + str(self._market_id))
        if self.order_status == OrderStatus["PENDING"]:
            self.inactive_order.append(self.active_order)
            self.active_order = None
            self.order_status = OrderStatus["INACTIVE"]
        else:
            self.error_inform("Order REJECTED from INACTIVE state!!!")

    def _print_trade_opportunity(self, other_order, show=False):
        """
        Depending on our role and our bottype, print trade opportunity accordingly
        :param other_order: trade opportunities seen
        :return: self.inform() - let user know there is a good trade opportunity
        """
        if other_order:
            return self.inform("My Role is " + str(self._role) +
                               ". Current best trade opportunity would "
                               "be buying at $"
                               + str(other_order / 100))

    def cancel_sent_order(self):
        """
        CANCELS my order that is existing in the order book
        :return: order ready to be cancelled
        """
        # RESOLVED: Copy library not imported, and use hardcopy
        # instead of softcopy
        cancel_order = copy.deepcopy(self.active_order)
        cancel_order.type = OrderType.CANCEL
        cancel_order.ref = "order cancel"   # needs to implement something here
        return cancel_order

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
        MAKES and SENDS order
        :param order_price: price made after decision
        :param order_side: buyer or seller
        :param order_unit: (Optional, not available) Traded units
        :param order_type: (Optional, not available) Type of order
        :return: sends order
        """
        ref = self._make_order_ref(self._market_id, order_price, order_side)
        self.active_order = Order(order_price, order_unit, order_type,
                                  order_side, self._market_id, ref=ref)
        self.order_status = OrderStatus["MADE"]

    def verify_active_order(self):
        """
        Verify current active order (against current market)and return a
        dictionary containing the information
        :return: a dictionary containing order information
        """

        pass

    # TODO is this part necessary? verify and making order is separated by the print opportunity
    # logic is after verifying order, knowing that we don't have enough cash or has bought maximum units
    # send message regarding opportunity, but not make order
    # OR can make into one function to process all 3 things together
    def _send_update_active_order(self):
        """
        VERIFY --- PRINT --- MAKE --- SEND
        :return:
        """
        self.verify_active_order(self.active_order, self.markets[self._market_id])
        self.send_order(self.active_order)
        self.order_status = OrderStatus["PENDING"]

    # TODO may need to put in a variable that counts how many iterations has the order been in the order book,
    # TODO maybe set a certain price point  where we think is better or certain number of iterations then CANCEL and make new order
    # TODO #### READ #### Split your inner function to two functions:
    # TODO _mm_sell_profit, _mm_buy_profit.This will definitely help
    def _market_maker_orders(self, best_ask, best_bid):
        """
        When bot is set to market maker, this function creates the appropriate order
        :param best_ask: Best ask price by the market
        :param best_bid: Best bid price by the market
        :return: no return
        """
        tick_size = self.markets[self._market_id]["tick"]

        order_price = None
        order_side = None

        # Bot is a buyer
        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            if best_bid is None:
                order_price = int(DS_REWARD_CHARGE/2)
            # Check if we can set a bid which beats the current best bid
            elif best_bid.price + tick_size < DS_REWARD_CHARGE:
                order_price = best_bid[0] + tick_size
            # Check if current best bid is profitable,
            # but increasing the bid makes it unprofitable
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

        # TODO put verify order here
        self._print_trade_opportunity(order_price)

        if order_price:
            self.make_send_order(order_price, order_side)

    # TODO #### READ #### Split your inner function to two functions:
    # TODO _reactive_sell_profit, _reactive_buy_profit. It will definitely help
    # TODO next few iterations the order is still in, cancel order and make new
    # or maybe a put in order book if bot_type is reactive but still have
    # order in the orderbook, cancel and wait for next opportunity
    def _reactive_orders(self, best_ask, best_bid, show=False):
        """
        When bot is set to reactive, make orders using this
        :param best_ask: Best ask price by the market
        :param best_bid: Best bid price by the market
        :param trade: If the order will actually be carried out
        :param show: If print trade opportunity
        :return: makes order according to role
        """
        order_price = None
        order_side = None

        if self._role == Role["BUYER"]:
            order_side = OrderSide.BUY
            if best_ask is None:
                self.inform("No orders can be made!"
                            "Will continue wait for orders...")
            elif best_ask[0] < DS_REWARD_CHARGE:
                order_price = best_ask[0]
                self.inform("Found an order!!! Making order now...")

        elif self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            if best_bid is None:
                self.inform("No orders can be made!"
                            "Will continue wait for orders...")
            elif best_bid[0] > DS_REWARD_CHARGE:
                order_price = best_bid[0]
                self.inform("Found an order!!! Making order now...")

        # TODO put verify order here
        self._print_trade_opportunity(order_price)
        if order_price:
            self.make_send_order(order_price, order_side)

    def warning_inform(self, msg):
        """
        INFORM warning message
        """
        self.inform("***WARNING***\n"
                    "       %s" % msg)

    def error_inform(self, msg):
        """
        INFORM error message
        """
        self.inform("@@@ERROR@@@\n"
                    "       %s" % msg)

    def line_break_inform(self, char="-", rep=79):
        """
        Simply inform a line break with certain character
        :param char: The character to be repeated
        :param rep: The number of repetition char would be repeated
        """
        self.inform("".join([char] * rep))

    @staticmethod
    def str_market(market):
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

    MARKETPLACE_ID = 260  # replace this with the marketplace id

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL_CALVIN, FM_PASSWORD_CALVIN, MARKETPLACE_ID)
    ds_bot.run()
