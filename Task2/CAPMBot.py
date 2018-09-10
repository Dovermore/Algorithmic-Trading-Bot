"""
Project Name: Induced Demand-Supply
Subject Code and Name: FNCE30010 Algorithmic Trading
Student Name (ID): Zhuoqun Huang (908525)
                   Nikolai Price (836389)
                   Lee Jun Da    (888086)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import copy
import time
from collections import defaultdict as dd

# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price",
                 "888086": "Lee Jun Da"}

# <For debugging only>
import inspect

INIT_STACK = 12
STACK_DIF = 10
BASE_LEN = 79
# </For debugging only>

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
    # Verifying units within 5 should be the responsibility of mm and reactive
    # function, not order verifier.
    "cash_available": None,     # Is cash enough to place this order
    "unit_available": None,     # Is unit enough to place this order
}
SEPARATION = "-"  # for most string separation


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
    CANCEL = -1        # Cancelled, turns INACTIVE when accepted
    INACTIVE = 0       # None/Completed/Rejected
    MADE = 1           # Made, turns PENDING when sent
    PENDING = 2        # Waiting to be accepted in the order book
    ACCEPTED = 3       # Accepted in the order book


class CAPMBot(Agent):

    def __init__(self, account, email, password, marketplace_id, risk_penalty=0.01, session_time=20):
        """
        Constructor for the Bot
        :param account: Account name
        :param email: Email id
        :param password: password
        :param marketplace_id: id of the marketplace
        :param risk_penalty: Penalty for risk
        :param session_time: Total trading time for one session
        """
        super().__init__(account, email, password, marketplace_id, name="CAPM Bot")
        self._payoffs = {}
        self._risk_penalty = risk_penalty
        self._session_time = session_time
        self._market_ids = {}

        # Record the number of possible states
        self._states = 0

        # Expected return for each security
        self._expected_returns = {}
        # TODO use time to change the type of bot to be more
        # TODO     aggressive when almost end we we have not reach target
        self._bot_type = BotType.REACTIVE

        # TBD later
        self._role = None

        # This member variable take advantage of only one order at a time
        # --------------------------------------------------------------------
        # Stores active orders currently in the order book
        self._active_orders = []
        self._order_status = OrderStatus.INACTIVE
        self._order_availability = copy.copy(ORDER_AVAILABILITY_TEMPLATE)
        # --------------------------------------------------------------------

        # Iterations since Market Maker order made
        self._mm_order_cycle = 0

        # Stores any inactive order that has been rejected
        self._inactive_order = []

        # Additional information, not particularly useful, but helps with
        # Verifying when calling `received_holdings`.
        self.mine_orders = None

    def initialised(self):
        """
        Initialise by looking at the requirements of the market,
        collects data regarding the market to be traded in and their
        respective payoff
        """
        self.inform("Initialised, examining markets available")
        for market_id, market_dict in self.markets.items():
            self.inform(self._str_market(market_dict))
            security = market_dict["item"]
            security_id = market_dict["id"]
            description = market_dict["description"]
            self._market_ids[security] = security_id
            self._payoffs[security] = [int(a) for a in description.split(",")]
            # Record number of states
            if len(self._payoffs) == 1:
                self._states = len(self._payoffs[security])
            self._expected_returns[security] = sum(self._payoffs[security]) / self._states
        self.inform("There are %s possible states" % str(self._states))

    def get_potential_performance(self, orders):
        """
        Returns the portfolio performance if the given list of orders is executed.
        The performance as per the following formula:
        Performance = ExpectedPayoff - b * PayoffVariance, where b is the penalty for risk.
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
        pass

    def order_rejected(self, info, order):
        pass

    def received_order_book(self, order_book, market_id):

        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                self.get_stack_size() * STACK_DIF)
        self.inform("received order book from %d" % market_id)

        try:
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
        pass

    def received_holdings(self, holdings):
        pass

    def received_marketplace_info(self, marketplace_info):
        pass

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

    @staticmethod
    def str_order(order):
        """
        This function return string representation of the detail of orders
        :param order: object of Order class of fmclient
        """
        try:
            if order is not None:
                return ("Order Detail\n"
                        "                       Price: %d\n"
                        "                       Units: %d\n"
                        "                       Type:  %s\n"
                        "                       Side:  %s\n"
                        "                       Ref:   %s\n"
                        "                       Id:    %d\n"
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


if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"

    FM_EMAIL_CALVIN = "z.huang51@student.unimelb.edu.au"
    FM_PASSWORD_CALVIN = "908525"

    FM_EMAIL_JD = "j.lee161@student.unimelb.edu.au"
    FM_PASSWORD_JD = "888086"

    FM_EMAIL_NP = "n.price3@student.unimelb.edu.au"
    FM_PASSWORD_NP = "836389"

    MARKETPLACE_ID1 = 372   # 3 risky 1 risk-free
    MARKETPLACE_ID2 = 363   # 2 risky 1 risk-free

    bot = CAPMBot(FM_ACCOUNT, FM_EMAIL_JD, FM_PASSWORD_JD, MARKETPLACE_ID1)
    bot.run()
