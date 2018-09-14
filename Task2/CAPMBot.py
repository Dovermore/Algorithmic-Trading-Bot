"""
Project Name: Induced Demand-Supply
Subject Code and Name: FNCE30010 Algorithmic Trading
Student Name (ID): Zhuoqun Huang (908525)
                   Nikolai Price (836389)
                   Lee Jun Da    (888086)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
from typing import List, Tuple, Dict
import copy
import time

# <For debugging only>
import inspect
INIT_STACK = 12
STACK_DIF = 10
BASE_LEN = 79
DEBUG_TOGGLE = 1
# </For debugging only>

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang",
                 "836389": "Nikolai Price",
                 "888086": "Lee Jun Da"}


# Market maker or reactive order
class OrderRole(Enum):
    MARKET_MAKER = 0
    REACTIVE = 1

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
ORDER_ROLE_TO_CHAR = {
    OrderRole.MARKET_MAKER: "MM",
    OrderRole.REACTIVE: "RE"
}
SEPARATION = "-"  # for most string separation


# Status of current order if there is any
class OrderStatus(Enum):
    CANCEL = -1        # Cancelled, turns INACTIVE when accepted
    INACTIVE = 0       # None/Completed/Rejected
    MADE = 1           # Made, turns PENDING when sent
    PENDING = 2        # Waiting to be accepted in the order book
    ACCEPTED = 3       # Accepted in the order book


# Status of current order if there is any
class OrderCompare(Enum):
    IDENTICAL = 0
    SAME_PRICE = 1
    DIFFERENT = -1


class Market:
    """
    Holding market state and all corresponding information of a market,
    as well as the current order status of that market
    """
    SYNC_MAX_DELAY = 2
    states = -1

    def __init__(self, market_dict: dict, host: Agent):
        print(list(market_dict.keys()))
        # Market information
        self._host = host
        self._market_id = market_dict["id"]
        self._minimum = market_dict["minimum"]
        self._maximum = market_dict["maximum"]
        self._tick = market_dict["tick"]
        self._name = market_dict["name"]
        self._item = market_dict["item"]
        self._description = market_dict["description"]
        self._payoffs = tuple(int(a) for a in self._description.split(","))
        self._covariances = {}
        if self.states == -1:
            self.set_states(len(self._payoffs))
        else:
            assert len(self._payoffs) == self.states
        self._expected_return = sum(self._payoffs) / self.states
        # Order information
        self.order = OrderHolder(self._market_id)

        # Holding information
        self._sync_delay = 0
        self._units = 0
        self._available_units = self._units
        # A virtual holding, simulating condition if order got accepted
        self._virtual_available_units = self._available_units

    @property
    def market_id(self):
        return self._market_id

    @property
    def minimum(self):
        return self._minimum

    @property
    def maximum(self):
        return self._maximum

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

    @property
    def payoffs(self):
        return self._payoffs

    @property
    def expected_return(self):
        return self._expected_return

    @property
    def covariances(self):
        return self._covariances

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, units):
        self._units = units

    @property
    def available_units(self):
        return self._available_units

    @available_units.setter
    def available_units(self, available_units):
        self._available_units = available_units

    def update_units(self, unit_dict):
        assert unit_dict["units"] > 0 and unit_dict["available_units"] > 0
        self._units = unit_dict["units"]
        self._available_units = unit_dict["available_units"]
        if self._available_units > self._virtual_available_units:
            self._sync_delay += 1
            if self._sync_delay >= self.SYNC_MAX_DELAY:
                self._host.warning("Market" + str(self._market_id) +
                                   "Failed to sync virtual units properly")
            self._virtual_available_units = self._available_units
        elif self._available_units == self._virtual_available_units:
            self._sync_delay = 0
        else:
            self._host.error("Market" + str(self._market_id) +
                             "Virtual Unit MORE Than available units")


    @classmethod
    def set_states(cls, states):
        assert states > 0
        cls.states = states

    def order_accepted(self, order):
        """
        Market side order processing
        :param order: The order accepted
        :return: True if added successfully, False otherwise
        """

    def is_valid_price(self, price: int) -> bool:
        """
        Check if price is valid, that is, it's proper considering minimum,
        minimum and tick
        :param price: The price to be checked
        :return: True if valid, else false
        """
        # TODO implement price checking

    def build_covariance(self, markets) -> None:
        for market in markets:
            self._covariances[market.market_id] = \
                self.compute_covariance(self._payoffs, market.payoffs)

    @staticmethod
    def compute_covariance(payoff1: Tuple[int],
                           payoff2: Tuple[int]) -> float:
        """
        Compute the covariance between list of payoff1 and payoff2, they
        have to be the same length
        :param payoff1: List of payoff1
        :param payoff2: List of payoff2
        :return: the covariance value
        """
        # TODO implement compute covariance procedure


class OrderHolder:
    def __init__(self, market_id):
        self._market_id = market_id

        # The order it's currently holding
        self._active_orders = []

    @property
    def active_order(self):
        """
        Retrieve active order
        :return: list of active orders, None if failed to retrieve
        """
        try:
            return copy.deepcopy(self._active_orders)
        except KeyError:
            return None

    def order_accepted(self, order: Order) -> bool:
        """
        Add new accepted_order to active_order
        :param order: The order accepted
        :return: True if added successfully, False otherwise
                 (E.g. Order invalid or no id for order provided)
        """
        pass

    def order_rejected(self, order: Order) -> None:
        """
        Handles rejection of orders in order holder
        :param order: The rejected order
        """
        pass

    def sort(self):
        self._active_orders = sorted(self._active_orders, key=self.key)

    @staticmethod
    def key(my_order):
        return my_order.order


class MyOrder:
    MM_ORDER_MAX_DELAY = 5
    REACTIVE_ORDER_MAX_DELAY = 1

    def __init__(self, price, units, order_type, order_side, market_id,
                 order_role):
        ref = self._make_order_ref(price, units, order_type, order_side,
                                   market_id, order_role)
        self._order = Order(price, units, order_type, order_side, market_id,
                            ref=ref)
        self._order_delay = 0
        self._order_role = order_role

    @staticmethod
    def _make_order_ref(price, units, order_type,
                        order_side, market_id, order_role):
        """
        Make the standard reference for an order
        :param price: price the order is placed on
        :param units: units the order is trading
        :param order_type: Limit or Cancel
        :param order_side: Buy or sell
        :param market_id:  Market order is trading on
        :param order_role: Market maker or reactive
        :return: A standard string containing all information
        """

        ref = ":" + time.strftime(("%y" + SEPARATION + "%m" + SEPARATION
                                   + "%d" +SEPARATION + "%H" + SEPARATION
                                   + "%M" +SEPARATION + "%S"),
                                  time.localtime()) + SEPARATION
        ref += str(price) + SEPARATION
        ref += str(units) + SEPARATION
        ref += ORDER_TYPE_TO_CHAR[order_type] + SEPARATION
        ref += ORDER_SIDE_TO_CHAR[order_side] + SEPARATION
        ref += str(market_id) + SEPARATION
        ref += ORDER_ROLE_TO_CHAR[order_role]
        return ref

    @property
    def order(self):
        return copy.copy(self._order)

    @order.setter
    def order(self, order):
        self._order = order

    @staticmethod
    def compare_order(order1, order2):
        if isinstance(order1, MyOrder):
            order1 = order1._order
        if isinstance(order2, MyOrder):
            order2 = order2._order
        # When side or type different
        if order1.side != order2.side or order1.type != order2.type:
            return OrderCompare.DIFFERENT
        # Handles accepted_order() and rejected order()
        elif (order1.ref is not None and order2.ref is not None
            and order1.ref == order2.ref):
            return OrderCompare.IDENTICAL
        # Handles accepted order but not traded yet
        elif (order1.id is not None and order2.id is not None and
              order1.id == order2.id):
            return OrderCompare.IDENTICAL
        # When price same but units differs
        elif order1.price == order2.price and order1.units != order2.units:
            return OrderCompare.SAME_PRICE
        # Other conditions
        else:
            return OrderCompare.DIFFERENT


class CAPMBot(Agent):
    def __init__(self, account, email, password, marketplace_id,
                 risk_penalty=0.01, session_time=20):
        """
        Constructor for the Bot
        :param account: Account name
        :param email: Email id
        :param password: password
        :param marketplace_id: id of the marketplace
        :param risk_penalty: Penalty for risk
        :param session_time: Total trading time for one session
        """
        super().__init__(account, email, password, marketplace_id,
                         name="CAPM_Bot")
        self._session_time = session_time

        self._risk_penalty = risk_penalty

        self._my_markets: Dict[int, Market] = {}

        self._cash = 0
        self._available_cash = self._cash
        # A virtual holding, simulating condition if order got accepted
        self._virtual_available_cash = self._available_cash

    def initialised(self):
        """
        Initialise by looking at the requirements of the market,
        collects data regarding the market to be traded in and their
        respective payoff
        """
        self.fn_start()
        for market_id, market_dict in self.markets.items():
            self.inform(market_id)
            self.inform(self._str_market(market_dict))
            self._my_markets[market_id] = Market(market_dict, self)
        self.inform("There are %s possible states" % str(Market.states))
        self.fn_end()

    def get_potential_performance(self, orders):
        """
        Returns the portfolio performance if the given list of orders is
        executed.
        The performance as per the following formula:
        Performance = ExpectedPayoff - b * PayoffVariance, where b is the
        penalty for risk.
        :param orders: list of orders
        :return:
        """
        pass

    def is_portfolio_optimal(self):
        """
        Returns true if the current holdings are optimal
        (as per the performance formula), false otherwise.
        :return:
        """
        pass

    def order_accepted(self, order):
        self.fn_start()

        self.inform(order)

        self.fn_end()
        pass

    def order_rejected(self, info, order):
        pass

    def received_order_book(self, order_book, market_id):

        self.fn_start()
        self.get_completed_orders(market_id)
        self.inform("received order book from %d" % market_id)
        od = None
        for order in order_book:
            if order.mine:
                self.inform(order)
                self.inform(order.date)

        try:
            self.fn_end()
            pass
        except Exception as e:
            self._exception_inform(e, inspect.stack()[0][3])

    def _get_bid_ask_price(self, orders):
        """
        Get the best bid and best ask price of the market
        :param orders: Orders from the order book
        :return: Best bid and best ask
        """
        pass

    def received_completed_orders(self, orders, market_id=None):
        self.fn_start()
        for order in orders:
            if order.mine:
                self.inform(order)
        self.fn_end()
        pass

    def received_holdings(self, holdings):
        self.fn_start()

        self.inform(list(holdings.items()))
        cash = holdings["cash"]
        self._cash = cash["cash"]
        self._available_cash = cash["available_cash"]

        for market_id, units in holdings["markets"]:
            self._my_markets[market_id].units = units["units"]
            self._my_markets[market_id].available_units = units["available_units"]

        self.fn_end()
        pass

    def received_marketplace_info(self, marketplace_info):
        self.fn_start()

        session_id = marketplace_info["session_id"]
        if marketplace_info["status"]:
            self.inform("Marketplace is now open with session id "
                        + str(session_id))
        else:
            self.inform("Marketplace is now closed.")

        self.fn_end()

    # --- ORDER HANDLER section ---
    def _update_received_order_book(self, order_book: List[Order],
                                    market_id: int) -> None:
        """
        Update active order based on received order book (Don't use this)
        :param order_book: Received Order book
        :param market_id: Id of the market where order_book come from
        """
        pass

    def _update_completed_order(self, orders: List[Order],
                                market_id: int) -> None:
        """
        Update active orders based on received completed orders (Don't use)
        :param orders: List of completed orders
        :param market_id: Id of the market where completed orders come from
        """
        pass

    def _check_order(self, price, units, order_type,
                     order_side, market_id) -> bool:
        """
        Check if an order can be sent based on cash or unit holdings
        :param price: price to send order at
        :param units: units to send
        :param order_type: type of order
        :param order_side: side of order
        :param market_id:  id of market
        :return: True if can send, False if order is null
        """
        pass

    def _send_order(self, price, units, order_type,
                    order_side, market_id, order_role) -> bool:
        """
        Check and send an order
        :param price: price to send order at
        :param units: units to send
        :param order_type: type of order
        :param order_side: side of order
        :param market_id:  id of market
        :param order_role: role of order (market_maker or reactive)
        :return: True if successfully sent, false if failed check
        """
        # TODO first make MyOrder then send it
        pass
    # ---   END ORDER HANDLER   ---

    def run(self):
        self.initialise()
        self.start()

    def calculate_performance(self, expected_payoff, payoff_var):
        """
        Calculates the portfolio performance
        :param expected_payoff: potential payoff at end of session
        :param payoff_var: variance of portfolio
        :return: performance
        """
        performance = expected_payoff - self._risk_penalty*payoff_var
        return performance

    def _line_break_inform(self, msg="", char="-",
                           length=BASE_LEN, width=BASE_LEN):
        """
        Simply inform a line break with certain character
        :param char:   The character to be repeated
        :param length: The number of repetition char would be repeated
        :param width:  The least width of line (symmetric space padding)
        """
        if msg != "":
            msg = "  " + msg + "  "
        len_char = (length - len(msg)) // len(char)
        char_left = len_char // 2
        char_right = len_char - char_left
        len_space = width - length
        if len_space < 0:
            len_space = 0
        space_left = len_space // 2
        space_right = len_space - space_left

        self.inform(" " * space_left + "".join([char] * char_left) +
                    msg + "".join([char] * char_right) + " " * space_right)

    def _exception_inform(self, msg, fn_name, addition=""):
        """
        Show the exception message with function name
        :param msg: exception to inform
        """
        assert isinstance(msg, Exception), ("msg %s is not an exception"
                                            % str(msg))
        if len(addition) > 0:
            addition = "addition, " + addition
        self.warning("^^^Exception in function %s^^^:"
                     "msg: %s%s" % (fn_name, str(msg), addition)
                     )

    @staticmethod
    def _str_market(market):
        """
        This is a staticmethod that returns the string representation of detail
        of a market
        :param market: Dictionary of a market to be turned into string
        """
        try:
            return ("Market: %d\n"
                    "                       Minimum: %3d\n"
                    "                       Maximum: %3d\n"
                    "                       Tick   : %3d\n"
                    "                       Name   : %s\n"
                    "                       Item   : %s\n"
                    "                       Describ: %s\n" %
                    (market["id"], market["minimum"], market["maximum"],
                     market["tick"], market["name"], market["item"],
                     market["description"]))
        except Exception as e:
            return e

    # Used for visualisation of function call as stacks, that it's easier to
    # trace through functions
    @staticmethod
    def get_stack_size():
        """
        Get stack size for caller's frame.
        %timeit len(inspect.stack())
        8.86 ms ± 42.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
        %timeit get_stack_size()
        4.17 µs ± 11.5 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
        """
        return len(inspect.stack())

    def fn_start(self):
        if not DEBUG_TOGGLE == 1:
            return
        self._line_break_inform(inspect.stack()[1][3], char="v",
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                (self.get_stack_size()-1) * STACK_DIF)

    def fn_end(self):
        if not DEBUG_TOGGLE == 1:
            return
        self._line_break_inform(inspect.stack()[1][3], char="^",
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                (self.get_stack_size()-1) * STACK_DIF)


if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"

    FM_EMAIL_CH = "z.huang51@student.unimelb.edu.au"
    FM_PASSWORD_CH = "908525"
    FM_CH = [FM_EMAIL_CH, FM_PASSWORD_CH]

    FM_EMAIL_JD = "j.lee161@student.unimelb.edu.au"
    FM_PASSWORD_JD = "888086"
    FM_JD = [FM_EMAIL_CH, FM_PASSWORD_CH]

    FM_EMAIL_NP = "n.price3@student.unimelb.edu.au"
    FM_PASSWORD_NP = "836389"
    FM_NP = [FM_EMAIL_CH, FM_PASSWORD_CH]

    MARKETPLACE_MANUAL = 387
    MARKETPLACE_ID1 = 372   # 3 risky 1 risk-free
    MARKETPLACE_ID2 = 363   # 2 risky 1 risk-free

    FM_SETTING = [FM_ACCOUNT] + FM_CH + [MARKETPLACE_MANUAL]
    bot = CAPMBot(*FM_SETTING)
    bot.run()
