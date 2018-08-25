"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType, Holding

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price", "888086": "Lee Jun Da"}

# ------ Add a variable called DS_REWARD_CHARGE -----
# Dependent on actual task
DS_REWARD_CHARGE = 500

# The unit to place order
ORDER_UNIT = 1

# Dictionary to store letters in representation of a certain OrderType
# and OrderSide for reference of orders
ORDER_TYPE_TO_CHAR = {OrderType.LIMIT: "L", OrderType.CANCEL: "M"}
ORDER_SIDE_TO_CHAR = {OrderSide.BUY: "B", OrderSide.SELL: "S"}


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
    PENDING  = 1
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
            else:
                self._reactive_check(mine_orders[0])

        elif len(mine_orders) > 1:
            self.warning_inform("More than one active order!!!!!")
        elif self.order_status == OrderStatus["ACCEPTED"]:
            self.inform("Order was completed in market " +
                        str(self._market_id))
        elif self.order_status == OrderStatus["PENDING"]:
            self.warning_inform("Order completed in pending state!")
            self.inform("Order was completed in market " +
                        str(self._market_id))

    def _to_cancel_order(self):
        """
        Cancels previous order
        """
        cancel_order = self.active_order
        cancel_order.type = OrderType.CANCEL
        self.send_order(cancel_order)
        self.order_status = OrderStatus["INACTIVE"]

    def _reactive_check(self):
        """
        If REACTIVE bot, if order is still in the order book, need to cancel
        :param order: my order that is in the order book
        """
        if self._bot_type == BotType["REACTIVE"]:
            self.inform("Reactive order still in the Order Book")
            self._to_cancel_order()

    def get_bid_ask_spread(self, best_bid, best_ask, show=False):
        """
        Inform basic info about current bid/ask status, including bid-ask
        spread
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        :param show: True if want to show detail of best bid/ask orders
        """
        if show:
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

        # TODO should verify order here if it is able to be put into next iteration
        # TODO this does not allow for active orders to be cancelled to be made new orders
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

        self.inform(self.order_status)
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
        :param holdings: Holdings of the account (Cash, Available Cash, Units, Available units)
        :return: return holdings of account
        """
        cash_holdings = holdings["cash"]
        self.inform("Total cash: " + str(cash_holdings["cash"]) +
                    " available cash: " + str(cash_holdings["available_cash"]))
        for market_id, market_holding in holdings["markets"].items():
            self.inform("Market ID " + str(market_id) + ": total units: " +
                        str(market_holding["units"]) + ", available units: "
                        + str(market_holding["available_units"]))
        cash_info = self.holdings["cash"]
        units_info = self.holdings["markets"][self._market_id]
        self.inform(cash_info)
        self.inform(units_info)


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

    def order_accepted(self, order):
        self.inform("Order was accepted in market " + str(self._market_id))
        if self.order_status == OrderStatus["PENDING"]:
            self.order_status = OrderStatus["ACCEPTED"]
        else:
            self.error_inform("Order accepted from INACTIVE state!!!")

    def order_rejected(self, info, order):
        self.inform("Order was rejected in market " + str(self._market_id))
        if self.order_status == OrderStatus["PENDING"]:
            self.inactive_order.append(self.active_order)
            self.active_order = None
            self.order_status = OrderStatus["INACTIVE"]
        else:
            self.error_inform("Order rejected from INACTIVE state!!!")

    def _print_trade_opportunity(self, other_order, show=False):
        """
        Depending on our role and our bottype, print trade opportunity accordingly
        :param other_order: trade opportunities seen
        :return: self.inform() - let user know there is a good trade opportunity
        """
        if other_order:
            return self.inform("My Role is " + str(self._role) +
                               ". Current best trade opportunity would be buying at $"
                               + str(other_order / 100))

    def verify_order(self, price):
        """
        verified on the holdings and also previous price if order can be made
        :param price:
        :return:
        """
        if self._check_previous_order_price(price):
            self._print_trade_opportunity(price)

            if self._available_cash_units():
                if self._bot_type == BotType["MARKET_MAKER"]:
                    self._to_cancel_order()
                    return True
                else:
                    return True
            else:
                return False

    def _available_cash_units(self):
        """
        Check if enough cash or units to make purchase or sale
        :return: True if enough, False if not enough
        """
        available_cash = self.holdings["cash"]["available_cash"]
        available_units = self.holdings["markets"][self._market_id]["available_units"]
        self.inform(available_cash)
        self.inform(available_units)
        if self._role == Role["BUYER"] and not available_units < 5:
            self.warning_inform("Have bought 5 units, additional units are not profitable")
            return False
        elif self._role == Role["SELLER"] and not available_units > 0:
            self.warning_inform("Do not have anymore units to trade")
            return False
        else:
            return True

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

    def make_send_order(self, order_price, order_side):
        """
        MAKES and SENDS order
        :param order_price: price made after decision
        :param order_side: buyer or seller
        :return: sends order
        """

        if self.verify_order():
            self.active_order = Order(order_price, ORDER_UNIT, OrderType.LIMIT, order_side, self._market_id)
            self.send_order(self.active_order)
            self.order_status = OrderStatus["PENDING"]

    # TODO may need to put in a variable that counts how many iterations has the order been in the order book,
    # TODO maybe set a certain price point  where we think is better or certain number of iterations then CANCEL and make new order
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

        if order_price:
            self.make_send_order(order_price, order_side)

    # TODO next few iterations the order is still in, cancel order and make new
    # or maybe a put in order book if bot_type is reactive but still have order in the orderbook, cancel and wait for next opportunity
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
                self.inform("No orders can be made! Will continue wait for orders...")
            elif best_ask[0] < DS_REWARD_CHARGE:
                order_price = best_ask[0]
                self.inform("Found an order!!! Making order now...")

        elif self._role == Role["SELLER"]:
            order_side = OrderSide.SELL
            if best_bid is None:
                self.inform("No orders can be made! Will continue wait for orders...")
            elif best_bid[0] > DS_REWARD_CHARGE:
                order_price = best_bid[0]
                self.inform("Found an order!!! Making order now...")

        if order_price:
            self.make_send_order(order_price, order_side)

    def warning_inform(self, msg):
        """
        INFORM warning message
        """
        self.inform("WARNING!!\n"
                    "       %s" % msg)

    def error_inform(self, msg):
        """
        INFORM error message
        """
        self.inform("ERROR!!!!!!!!!\n"
                    "       %s" % msg)

    def line_break_inform(self, char="-", rep=79):
        """
        Simply inform a line break with certain character
        :param char: The character to be repeated
        :param rep: The number of repetition char would be repeated
        """
        self.inform("".join([char] * rep))


if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"

    FM_EMAIL_CALVIN = "z.huang51@student.unimelb.edu.au"
    FM_PASSWORD_CALVIN = "908525"

    FM_EMAIL_JD = "j.lee161@student.unimelb.edu.au"
    FM_PASSWORD_JD = "888086"

    MARKETPLACE_ID = 260  # replace this with the marketplace id

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL_JD, FM_PASSWORD_JD, MARKETPLACE_ID)
    ds_bot.run()
