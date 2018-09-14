"""
Project Name: Induced Demand-Supply
Subject Code and Name: FNCE30010 Algorithmic Trading
Student Name (ID): Zhuoqun Huang (908525)
                   Nikolai Price (836389)
                   Lee Jun Da    (888086)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
from typing import List, Tuple
import copy
# <For debugging only>
import inspect
INIT_STACK = 12
STACK_DIF = 10
BASE_LEN = 79
DEBUG = True
# </For debugging only>

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang",
                 "836389": "Nikolai Price",
                 "888086": "Lee Jun Da"}


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
SEPARATION = "-"  # for most string separation


# Let us define another enumeration to deal with the type of bot
class OrderRole(Enum):
    MARKET_MAKER = 0
    REACTIVE = 1


# Status of current order if there is any
class OrderStatus(Enum):
    CANCEL = -1        # Cancelled, turns INACTIVE when accepted
    INACTIVE = 0       # None/Completed/Rejected
    MADE = 1           # Made, turns PENDING when sent
    PENDING = 2        # Waiting to be accepted in the order book
    ACCEPTED = 3       # Accepted in the order book


class Market:
    _states = -1

    def __init__(self, market_dict: dict):
        # Market information
        self._market_id = market_dict["id"]
        self._minimum = market_dict["minimum"]
        self._maximum = market_dict["maximum"]
        self._tick = market_dict["tick"]
        self._name = market_dict["name"]
        self._item = market_dict["item"]
        self._description = market_dict["description"]
        self._payoffs = tuple(int(a) for a in self._description.split(","))
        self._expected_return = sum(self._payoffs) / self._states
        self._covariances = {}
        self._cycle = 0
        if self._states == -1:
            self._states = len(self._payoffs)
        else:
            assert len(self._payoffs) != self._states

        # Order information
        self._order = OrderHolder(self._market_id)

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
    def cycle(self):
        return self._cycle

    def add_cycle(self, add=1):
        self._cycle += add

    @classmethod
    def states(cls):
        return cls._states

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
    MM_ORDER_MAX_CYCLE = 5
    REACTIVE_ORDER_MAX_CYCLE = 1

    def __init__(self, market_id):
        self._market_id = market_id

        # The order it's currently holding
        self._order_status = OrderStatus.INACTIVE
        self._active_order = None

    @property
    def active_order(self):
        """
        Retrieve active order
        :return: list of active orders, None if failed to retrieve
        """
        try:
            return copy.copy(self._active_order)
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

        self._market_ids = {}

        self._risk_penalty = risk_penalty
        self._payoffs = {}
        self._variances = {}
        # Record the number of possible states
        self._states = 0

        # TBD later
        self._role = None

    def initialised(self):
        """
        Initialise by looking at the requirements of the market,
        collects data regarding the market to be traded in and their
        respective payoff
        """
        self.inform("Initialised, examining markets available")
        for market_id, market_dict in self.markets.items():
            self.inform(self._str_market(market_dict))

        self.inform("There are %s possible states" % str(self._states))

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
        for order in order_book:
            if order.mine:
                self.inform(order)

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
        pass

    def received_marketplace_info(self, marketplace_info):
        pass

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
        if not DEBUG:
            return
        self._line_break_inform(inspect.stack()[1][3], char="v",
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                (self.get_stack_size()-1) * STACK_DIF)

    def fn_end(self):
        if not DEBUG:
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
