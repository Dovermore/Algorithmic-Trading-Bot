"""
Project Name: Induced Demand-Supply
Subject Code and Name: FNCE30010 Algorithmic Trading
Student Name (ID): Zhuoqun Huang (908525)
                   Nikolai Price (836389)
                   Lee Jun Da    (888086)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
from fmclient.utils.constants import DATE_FORMAT
from typing import List, Tuple, Dict
import copy
import time
import datetime

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
    SAME_ORDER = 1
    SAME_PRICE = 2
    DIFFERENT = -1

# ----- Start of Helper classes -----


class Market:
    """
    Holding market state and all corresponding information of a market,
    as well as the current order status of that market
    """
    SYNC_MAX_DELAY = 2
    states = -1

    def __init__(self, market_dict: dict, agent):
        # Parse market information into the object
        self._agent: CAPMBot = agent
        self._market_id = market_dict["id"]
        self._minimum = market_dict["minimum"]
        self._maximum = market_dict["maximum"]
        self._tick = market_dict["tick"]
        self._name = market_dict["name"]
        self._item = market_dict["item"]
        self._description = market_dict["description"]
        self._payoffs = tuple(int(a) for a in self._description.split(","))
        if self.states == -1:
            self.set_states(len(self._payoffs))
        else:
            assert len(self._payoffs) == self.states
        self._expected_return = sum(self._payoffs) / self.states
        # Setting up own order information
        self.order_holder = OrderHolder(self._market_id, agent)
        self._current_order: MyOrder = None

        # Setting up order book
        self._order_book = None
        self._best_bid = None
        self._best_ask = None

        # Setting up holding information
        self._sync_delay = 0
        self._units = 0
        self._available_units = self._units
        # A virtual holding, simulating condition if order got accepted
        self._virtual_available_units = self._available_units

        # Record where the completed order has been read to
        self._completed_order_index = 0

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

    @property
    def virtual_available_units(self):
        return self._virtual_available_units

    @virtual_available_units.setter
    def virtual_available_units(self, virtual_available_units):
        self._virtual_available_units = virtual_available_units

    def update_units(self, unit_dict):
        """
        ---- Should not be used elsewhere. Need not to read ----
        This function is used in received holdings to update the units in
        one particular market. Will also keep track and update outdated
        virtual holdings.
        :param unit_dict: Standard dictionary containing the units to check
        :return:
        """
        self._agent.fn_start()
        assert unit_dict["units"] > 0 and unit_dict["available_units"] > 0
        self._units = unit_dict["units"]
        self._available_units = unit_dict["available_units"]
        if self._available_units > self._virtual_available_units:
            self._sync_delay += 1
            if self._sync_delay >= self.SYNC_MAX_DELAY:
                self._agent.warning("Market" + str(self._market_id) +
                                    "Failed to sync virtual units properly")
            self._virtual_available_units = self._available_units
        elif self._available_units == self._virtual_available_units:
            self._sync_delay = 0
        else:
            self._agent.error("Market" + str(self._market_id) +
                              "Virtual Unit MORE Than available units")
        self._agent.fn_end()

    @classmethod
    def set_states(cls, states):
        """
        ---- Should not be used elsewhere. Need not to read ----
        :param states:
        :return:
        """
        assert states > 0
        cls.states = states

    def order_accepted(self, order: Order):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Market side order accepted processing, update available units
        :param order: The order accepted
        """
        if order.side == OrderSide.SELL:
            if order.type == OrderType.LIMIT:
                self._available_units -= order.units
            else:
                self._available_units += order.units

        self.order_holder.order_accepted(order)

    def order_rejected(self, order: Order):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Market side order rejected processing
        :param order: The order rejected
        """
        if order.side == OrderSide.SELL:
            if order.type == OrderType.LIMIT:
                self._available_units += order.units
            else:
                self._available_units -= order.units
        self.order_holder.order_rejected(order)

    def update_received_order_book(self, order_book):
        """
        ---- Should not be used elsewhere. Need not to read ----
        :param order_book: Order book from market
        """
        # TODO More logic here, update best_bid, best ask, and order book
        self._order_book = order_book
        self.order_holder.update_received_order_book(order_book)

    def update_completed_orders(self, orders):
        """
        ---- Should not be used elsewhere. Need not to read ----
        """
        # TODO More logic here
        self.order_holder.\
            update_completed_orders(orders[self._completed_order_index:])
        self._completed_order_index = len(orders)

    def add_order(self, price, units, order_type, order_side, market_id,
                  order_role):
        """
        :return: Reference to the added order
        """
        order = self.order_holder.add_order(price, units, order_type,
                                            order_side, market_id, order_role)
        self._current_order = order

    def send_current_order(self):
        """
        Send the last added order
        :return: Return True if successful, False Otherwise
        """
        if self._current_order is not None:
            # When selling, reduce virtual units
            if self._current_order.order.side == OrderSide.SELL:
                self._virtual_available_units -= \
                    self._current_order.order.units
            return self._current_order.send()
        return False

    def is_valid_price(self, price: int) -> bool:
        """
        Check if price is valid, that is, it's proper considering minimum,
        minimum and tick
        :param price: The price to be checked
        :return: True if valid, else False
        """
        return (self._minimum < price < self.maximum and
                (price - self._minimum) % self._tick != 0)


class OrderHolder:
    # TODO implement cancel order logic
    def __init__(self, market_id, agent):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Initialise an OrderHolder instance that holds all orders of a market
        :param market_id: Order of a market it's holding
        :param agent: The agent bot for logging
        """
        self._market_id = market_id
        self._agent: CAPMBot = agent
        # The order it's currently holding
        self._orders: List[MyOrder] = []

    @property
    def orders(self):
        """
        Retrieve active orders
        :return: list of active orders, None if failed to retrieve
        """
        try:
            return copy.deepcopy(self._orders)
        except KeyError:
            return None

    def add_order(self, price, units, order_type,
                  order_side, market_id, order_role,
                  order_status=OrderStatus.INACTIVE, orig_order=None):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Add order to order holder, default to inactive order, and return
        reference to the created MyOrder object
        :keyword order_status OrderStatus of order added (only aimed
                                                          for internal use)
        :keyword orig_order The order object to be added if
                 there is already such orders (so fixing issues)
        :return: MyOrder object created during addition
        """
        order = MyOrder(price, units, order_type, order_side,
                        market_id, order_role, order_status)
        if orig_order:
            order.order = orig_order
        self._orders.append(order)
        self._agent.inform([str(order) for order in self._orders])
        return order

    def order_accepted(self, order: Order):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Add new accepted_order to active_order
        :param order: The order accepted
        :return: True if added successfully, False otherwise
                 (E.g. Order invalid or no id for order provided)
        """
        # TODO handle CANCEL order, if order is cancel, remove something
        # Check all orders to find corresponding order, and accept it
        self._orders = sort_order_by_date(self._orders)
        for my_order in self._orders:
            if order.type == OrderType.CANCEL and \
                    MyOrder.compare_order(my_order.cancel_order, order) == \
                    OrderCompare.IDENTICAL:
                self._orders.remove(my_order)
                break
            if MyOrder.compare_order(my_order, order) ==\
                    OrderCompare.IDENTICAL:
                my_order.accepted()
                break
        # Didn't find matching order
        else:
            self._agent.warning(str(order) + ": Didn't find matching order")
            order_role = OrderRole.REACTIVE
            if order.ref is not None:
                if order.ref[-2:] == "MM":
                    order_role = OrderRole.MARKET_MAKER
                else:
                    order_role = OrderRole.REACTIVE
            self.add_order(order.price, order.units, order.type, order.side,
                           order.market_id, order_role, OrderStatus.ACCEPTED,
                           order)

    def order_rejected(self, order: Order):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Handles rejection of orders in order holder
        :param order: The rejected order
        """
        # TODO handle CANCEL order...
        self._orders = sort_order_by_date(self._orders)
        for my_order in self._orders:
            if MyOrder.compare_order(my_order, order) == \
                    OrderCompare.IDENTICAL:
                self._orders.remove(my_order)
                break
        # Didn't find matching order
        else:
            self._agent.warning(str(order) + ": Didn't find matching order")

    def update_received_order_book(self, order_book):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Update orders based on received order book
        """
        mine_orders = [order for order in order_book if order.mine is True]
        self._orders = sort_order_by_date(self._orders)
        for order in mine_orders:
            for my_order in self._orders:
                compare = MyOrder.compare_order(my_order, order)
                # Identical order, update its delay indicator
                # Partially traded orders will be updated by completed orders
                # Don't need to update it here
                if compare == OrderCompare.IDENTICAL:
                    if my_order.delayed():
                        my_order.cancel()
                    break
            # Didn't find order in all kept orders
            else:
                self._agent.warning(str(order) +
                                    ": Didn't find matching order")
                # Treat it as if it's reactive order if didn't find record
                self.add_order(order.price, order.units, order.type,
                               order.side, order.market_id, OrderRole.REACTIVE,
                               OrderStatus.ACCEPTED, order)

    def update_completed_orders(self, orders):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Update orders based on completed orders
        """
        mine_orders = sort_order_by_date([order for order in
                                          orders if order.mine is True])
        self._orders = sort_order_by_date(self._orders)
        for order in mine_orders:
            for my_order in self._orders:
                compare = MyOrder.compare_order(my_order, order)
                # Identical order, fully traded, remove it
                if compare == OrderCompare.SAME_ORDER:
                    self._orders.remove(my_order)
                    break
                # Partially traded order
                elif compare == OrderCompare.SAME_PRICE and \
                        my_order.order.units > order.units:
                    my_order.partial_traded(order)


class MyOrder:
    MM_ORDER_MAX_DELAY = 5
    REACTIVE_ORDER_MAX_DELAY = 1
    AGENT = None

    def __init__(self, price, units, order_type, order_side, market_id,
                 order_role, order_status=OrderStatus.INACTIVE):
        ref = self._make_order_ref(price, units, order_type, order_side,
                                   market_id, order_role)
        self._order = Order(price, units, order_type, order_side, market_id,
                            ref=ref)
        self._cancel_order = None
        self._order_delay = 0
        self._order_role = order_role
        self._order_status = order_status

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
        ref = ":" + time.strftime(DATE_FORMAT, time.localtime()) + SEPARATION
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

    @property
    def cancel_order(self):
        return copy.copy(self._order)

    @cancel_order.setter
    def cancel_order(self, cancel_order):
        self._cancel_order = cancel_order

    def send(self):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Send the order
        :return: True if successfully sent, False otherwise
        """
        if self.AGENT is not None and self._order_status ==\
                OrderStatus.INACTIVE:
            self.AGENT.send_order(self._order)
            self._order_status = OrderStatus.PENDING
            return True
        return False

    def cancel(self):
        """
        Cancel this order
        :return: True if cancel success, False otherwise
        """
        if self.AGENT is not None and self._order_status ==\
                OrderStatus.ACCEPTED:
            self._cancel_order = copy.copy(self._order)
            self._cancel_order.type = OrderType.CANCEL
            self.AGENT.send_order(self._cancel_order)
            return True
        return False

    def accepted(self):
        self._order_status = OrderStatus.ACCEPTED

    def delayed(self, times=1):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Called when this order is delayed,
        and return if the order should be cancelled
        :return: True if exceeded max delay, false otherwise
        """
        self._order_delay += times
        return self._should_cancel()

    def partial_traded(self, order):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Called when order is partially_traded and return if the order
        should be cancelled, if not reset the order delay
        :param order: The order in completed orders
        """
        if self._order_role == OrderRole.REACTIVE:
            return True
        self._order_delay = 0
        self._order.units = self._order.units - order.units
        return False

    def _should_cancel(self):
        """
        Check if should cancel itself, based on the current delay
        :return: True if need to cancel, False otherwise
        """
        if self._order_role == OrderRole.MARKET_MAKER and \
                self._order_delay >= self.MM_ORDER_MAX_DELAY:
            return True
        elif self._order_role == OrderRole.REACTIVE and \
                self._order_delay >= self.REACTIVE_ORDER_MAX_DELAY:
            return True
        else:
            return False

    @classmethod
    def set_agent(cls, agent):
        """
        Set up the agent used to send orders
        """
        cls.AGENT: CAPMBot = agent

    @staticmethod
    def compare_order(order1, order2):
        """
        ---- Should not be used elsewhere. Need not to read ----
        Compare if two orders are same, either Order or MyOrder can be passed
        :param order1: The first order to compare
        :param order2: The first order to compare
        :return: OrderCompare.IDENTICAL if two orders are completely same
                 OrderCompare.SAME_PRICE if two orders differs in unit but
                                    not price (thus might be the same order)
                 OrderCompare.DIFFERENT if two orders can't possibly be same
        """
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
        elif order1.price == order2.price and order1.units == order2.units:
            return OrderCompare.SAME_ORDER
        elif order1.price == order2.price and order1.units != order2.units:
            return OrderCompare.SAME_PRICE
        # Other conditions
        else:
            return OrderCompare.DIFFERENT


def key(order):
    """
    ---- Should not be used elsewhere. Need not to read ----
    Takes an Order or a MyOrder object and return it's date attribute, for
    sorting purpose only. For order WITHOUT date, the time now will
    be used
    :param order: the object to be sorted
    :return: datetime object contained in it
    """
    assert isinstance(order, (MyOrder, Order))
    if isinstance(order, MyOrder):
        date = order.order.date
    else:
        date = order.date
    if date is None:
        date = datetime.datetime.now()
    return date


def sort_order_by_date(orders, reverse=False):
    """
    ---- Should not be used elsewhere. Need not to read ----
    Sort the given orders by time so that comparing logic will work well.
    :return: Sorted list or orders
    """
    return sorted(orders, key=key, reverse=reverse)

# ----- End of Helper classes -----


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
        self.covariances = {}
        self.variances = {}
        self.collect_payoffs = {}

        self._cash = 0
        self._available_cash = self._cash
        # A virtual holding, simulating condition if order got accepted
        self._virtual_available_cash = self._available_cash

        # Set up agent for Order sender
        MyOrder.set_agent(self)

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
        self.build_variance()
        self.build_covariance()
        self.inform("There are %s possible states" % str(Market.states))
        self.fn_end()

    def get_potential_performance(self, orders):
        """
        Returns the portfolio performance if the given list of orders is
        executed.
        :param orders: list of orders
        :return:
        """
        new_holdings = {}
        new_cash = self._cash
        for market in self._my_markets.keys():
            new_holdings[market] = self._my_markets[market].units
        for order in orders:
            if order.side == OrderSide.SELL:
                new_holdings[order.market_id] -= order.units
                new_cash += order.price * order.units
            else:
                new_holdings[order.market_id] += order.units
                new_cash -= order.price * order.units

        new_performance = self.calculate_performance(new_holdings, new_cash)
        return new_performance

    ##########################################################################
    def build_covariance(self) -> None:
        """
        Build the covariance for all payoffs
        :return: None
        """
        for first_iter_market in self._my_markets.keys():
            market_id1 = self._my_markets[first_iter_market].market_id
            for second_iter_market in self._my_markets:
                market_id2 = self._my_markets[second_iter_market].market_id
                to_be_key = sorted([market_id1, market_id2])
                key_for_dict = str(to_be_key[0])+'-'+str(to_be_key[1])
                if market_id1 != market_id2 and \
                        key_for_dict not in self.covariances:
                    self.covariances[key_for_dict] = \
                        self.compute_covariance(
                            self._my_markets[first_iter_market],
                            self._my_markets[second_iter_market])
                    self.inform(self.read_covariance
                                (market_id1, market_id2,
                                 self.covariances[key_for_dict]))

    def build_variance(self) -> None:
        """
        Build the Variance for all Payoffs
        :return: None
        """
        for market in self._my_markets.keys():
            self.variances[market] = \
                self.compute_variance(self._my_markets[market].payoffs)
            self.inform(self.read_variance(market, self.variances[market]))

    @staticmethod
    def compute_variance(payoff: Tuple[int]) -> float:
        squared_payoff = []
        for states in payoff:
            squared_payoff.append(states**2)
        return ((1/Market.states)*sum(squared_payoff)) - \
               ((1/(Market.states**2))*(sum(payoff)**2))

    @staticmethod
    def compute_covariance(market1, market2):
        """
        Compute the covariance between list of payoff1 and payoff2, they
        have to be the same length
        :param market1:
        :param market2: List of payoff2
        :return: the covariance value
        """
        # TODO implement compute covariance procedure
        cross_multiply = []
        payoff1 = tuple(market1.payoffs)
        payoff2 = tuple(market2.payoffs)
        exp_ret1 = market1.expected_return
        exp_ret2 = market2.expected_return
        for num in range(Market.states):
            cross_multiply.append(payoff1[num]*payoff2[num])
        return (1/Market.states)*sum(cross_multiply) - (exp_ret1*exp_ret2)

    def units_payoff_variance(self, units):
        total_variance = 0
        for market_id in units.keys():
            total_variance += (units[market_id]**2)*\
                              (self.variances[market_id])
        for market_ids in self.covariances.keys():
            ind_market_id = market_ids.split('-')
            total_variance += (2*units[int(ind_market_id[0])]) * \
                              (units[int(ind_market_id[1])]) * \
                              (self.covariances[market_ids])
        return total_variance

    def calculate_performance(self, holdings, cash):
        """
        Calculates the portfolio performance
        :param holdings: dictionary with market IDs and units held
        :param cash: cash held
        :return: performance
        """
        b = self._risk_penalty
        expected_payoff = cash
        tot_payoff_variance = self.units_payoff_variance(holdings)
        for market in holdings.keys():
            expected_payoff += self._my_markets[market].expected_return * holdings[market]
        return expected_payoff - b*tot_payoff_variance
    ##########################################################################

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
        try:
            self._my_markets[market_id].update_received_order_book(order_book)
        except Exception as e:
            self._exception_inform(e, inspect.stack()[0][3])

    # TODO move this to market section
    # def _get_bid_ask_price(self, orders):
    #     """
    #     Get the best bid and best ask price of the market
    #     :param orders: Orders from the order book
    #     :return: Best bid and best ask
    #     """
    #     pass

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
            self._my_markets[market_id].update_units(units)

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
        self._my_markets[market_id].update_received_order_book(order_book)

    def _update_completed_order(self, orders: List[Order],
                                market_id: int) -> None:
        """
        Update active orders based on received completed orders (Don't use)
        :param orders: List of completed orders
        :param market_id: Id of the market where completed orders come from
        """
        self._my_markets[market_id].update_completed_orders(orders)

    def _check_order(self, price, units, order_side, market_id) -> bool:
        """
        Check if an order can be sent based on cash or unit holdings, this only
        support limit order, use MyOrder's object method cancel to cancel order
        :param price: price to send order at
        :param units: units to send
        :param order_side: side of order
        :param market_id:  id of market
        :return: True if can send, False if order is null
        """
        # TODO check multiple orders at once
        if order_side == OrderSide.BUY:
            return self._virtual_available_cash >= price * units
        else:
            market: Market = self.markets[market_id]
            return (market.is_valid_price(price) and
                    market.virtual_available_units >= units)

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
        # TODO virtual holding check
        if self._check_order(price, units, order_side, market_id):
            market:Market = self._my_markets[market_id]
            market.add_order(price, units, order_type, order_side,
                             market_id, order_role)
            return market.send_current_order()
        else:
            return False

    def _cancel_order(self):
        """
        cancel some order, not implemented yet (not used right now)
        """
    # ---   END ORDER HANDLER   ---

    def run(self):
        self.initialise()
        self.start()

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
    def read_variance(market, variance):
        return "The variance for market %d is %3d" % (market, variance)

    @staticmethod
    def read_covariance(market1, market2, covariance):
        return "The covariance between market %d and market %d is %3d" \
               % (market1, market2, covariance)

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

    FM_SETTING = [FM_ACCOUNT] + FM_CH + [MARKETPLACE_ID1]
    bot = CAPMBot(*FM_SETTING)
    bot.run()
