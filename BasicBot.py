"""
This is a template for Project 1, Task 1 (Induced demand-supply)
"""

from enum import Enum
from fmclient import Agent, OrderSide, Order, OrderType
import copy
import time

# <For debugging only>
import inspect
import sys


INIT_STACK = 12
STACK_DIF = 5 * 2
BASE_LEN = 79


# Used for visualisation of function call as stacks, that it's easier to
# trace through functions
def get_stack_size():
    """
    Get stack size for caller's frame.
    %timeit len(inspect.stack())
    8.86 ms ± 42.5 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
    %timeit get_stack_size()
    4.17 µs ± 11.5 ns per loop (mean ± std. dev. of 7 runs, 100000 loops each)
    """
    size = 2  # current frame and caller's frame always exist
    while True:
        try:
            sys._getframe(size)
            size += 1
        except ValueError:
            return size - 1  # subtract current frame
# </For debugging only>


# Group details
GROUP_MEMBERS = {"908525": "Zhuoqun Huang", "836389": "Nikolai Price",
                 "888086": "Lee Jun Da"}

# ------ Add a variable called DS_REWARD_CHARGE -----
# Dependent on actual task
DS_REWARD_CHARGE = 500
MAX_REWARD_UNIT = 5

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
    # Verifying units within 5 should be the responsibility of mm and reactive
    # function, not order verifier.
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
    MADE = 1
    PENDING = 2
    ACCEPTED = 3


class DSBot(Agent):

    # ------ Constructor and initialisation methods -----
    def __init__(self, account, email, password, marketplace_id):
        super().__init__(account, email, password, marketplace_id,
                         name="DSBot")

        self._bot_type = BotType.REACTIVE
        # TBD later
        self._role = None

        # This member variable take advantage of only one order at a time
        # --------------------------------------------------------------------
        # Stores active order currently in the order book
        self.active_order = None
        self.order_status = OrderStatus.INACTIVE
        self.order_availability = copy.copy(ORDER_AVAILABILITY_TEMPLATE)
        # Tracking number of cycles that Market Maker Order has been
        # accepted but not traded
        self.mm_order_cycle = 0

        self.inactive_order = []

        self._market_id = None

        # Additional information, not particularly useful, but helps with
        # Verifying when calling `received_holdings`.
        self.mine_orders = None

    def run(self):
        """
        Kick starts the bot
        """
        self.initialise()
        self.start()

    def _get_role(self):
        """
        Set the role of bot based on cash holdings (positive: BUYER, otherwise
        seller)
        """
        # self._line_break_inform(inspect.stack()[0][3],
        #                         length=79 + 32 - get_stack_size() * 6)
        cash_holdings = self.holdings["cash"]
        unit_holdings = self.holdings["markets"][self._market_id]
        self.inform(cash_holdings)
        self.inform(unit_holdings)
        if cash_holdings["cash"] <= 0:
            self.inform("Bot is a seller")
            return Role.SELLER
        else:
            self.inform("Bot is a buyer")
            return Role.BUYER

    def initialised(self):
        """
        Initialise by looking at the requirements of the market
        and gets the role of the bot based on holdings from the start
        """
        self.inform("Initialised, examining markets available")
        for market_id, market_dict in self.markets.items():
            self.inform(self._str_market(market_dict))
        self._market_id = list(self.markets.keys())[0]
        self._role = self._get_role()
        self._role = Role.BUYER

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
                self._exception_inform(e, inspect.stack()[0][3])

        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
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

    # TODO two conditions hard to cope with
    # TODO          1: Sent cancel, but cancel didn't arrive
    # TODO          2: Sent cancel, but order completed before canceled
    def _update_mine_orders(self, mine_orders, best_bid, best_ask):
        """
        Based on extracted mine_orders, update own holding status
        :param mine_orders: list of mine orders, empty if none
        :param best_bid:    Best bid price provided
        :param best_ask:    Best ask price provided
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        if len(mine_orders) == 1:
            if self.order_status != OrderStatus.ACCEPTED:
                if self.order_status == OrderStatus.CANCEL:
                    self.warning("Cancel order did not go through")
                else:
                    self.warning("Current Order: %s, with status %s, didn't "
                                 "get updated. now updating by order book!"
                                 % (str(self.active_order),
                                    str(self.order_status)))
                    if self.active_order is not None:
                        self.inactive_order.append([self.active_order, None])
                    self.active_order = mine_orders[0]
                    self.order_status = OrderStatus.ACCEPTED
            else:
                self._check_accepted_order(mine_orders[0], best_bid, best_ask)
        elif len(mine_orders) > 1:
            self.warning("More than one active order!")
            mine_orders_sorted = sorted([[order, self._order_profitable(order)]
                                         for order in mine_orders],
                                        key=lambda x: x[1], reverse=True)
            # The logic is not complete, this will only in rare cases produce
            # effective solution, hte precise solution is more complex.
            for order, profit in mine_orders_sorted:
                self.inform("order: %s, with potential profit %d"
                            % (str(order), profit))

            for order, profit in mine_orders_sorted[1:]:
                cancel_order = self._make_cancel_order(order)
                self.send_order(cancel_order)

            self.active_order = mine_orders_sorted[0][0]
            self.order_status = OrderStatus.ACCEPTED

        elif self.order_status == OrderStatus.ACCEPTED:
            self.order_status = OrderStatus.INACTIVE
            self.inform("Order %s was completed in market %s"
                        % (str(self.active_order), str(self._market_id)))
            self.active_order = None
        elif self.order_status != OrderStatus.INACTIVE:
            self.warning("Order %s completed with state: %s"
                         % (str(self.active_order),
                            str(self.order_status)))

    @staticmethod
    def _order_weak_equal(order1, order2, cancel=False):
        """
        Check if order1 and order2 have the same amount of units traded
        with same price of the same OrderSide, OrderType
        :param order1: The first order to compare
        :param order2: The second order to compare
        :return:       True if same, False if not the same,
                       None if either is None or type os not Order
        """
        # Both order exists
        if (order1 and isinstance(order1, Order) and
                order2 and isinstance(order2, Order)):
            if (cancel is False and order1.price == order2.price and
                    order1.units == order2.units and
                    order1.side == order2.side and
                    order1.type == order2.type):
                return True
            elif (order1.price == order2.price and
                  order1.units == order2.units and
                  order1.side == order2.side and
                  order1.type != order2.type):
                return True
            return False
        return None

    def _check_accepted_order(self, order, best_bid, best_ask):
        """
        Check the status of last accepted order and potentially cancel based
        on status
        :return The canceled order if there is one else None
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        try:
            if self._order_weak_equal(self.active_order, order) is not True:
                self.error("The accepted_order %s is different "
                           "from active_order %s, setting active_order"
                           " to correspond to order_book"
                           % (str(order), str(self.active_order)))
                self.active_order = order
                self.order_status = OrderStatus.ACCEPTED
            if self._bot_type == BotType.REACTIVE:
                self.inform("Reactive order still in the Order Book")
                return self._cancel_sent_order()
            elif self._bot_type == BotType.MARKET_MAKER:
                other_order = (best_bid if self._role == Role.BUYER
                               else best_ask)
                # The number of iterations exceeds magic number, cancel order
                if self.mm_order_cycle >= MAGIC_MM_CANCEL_CYCLE:
                    return self._cancel_sent_order()
                elif other_order.mine is not True:
                    order = self._mm_buyer_order(other_order)
                    # If the order found based on new booking is different,
                    # it means there will be better market making orders to
                    # place than current one
                    if (self._order_weak_equal(self.active_order, order)
                            is not True):
                        return self._cancel_sent_order()
                return None
        except Exception as e:
            self._exception_inform(e, inspect.stack()[0][3])

    def _get_bid_ask_spread(self, best_bid, best_ask, show=False):
        """
        Inform basic info about current bid/ask status, including bid-ask
        spread
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        :param show: True if want to show detail of best bid/ask orders
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
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
            if best_bid is None:
                self.inform("           Bid unavailable")
            if best_ask is None:
                self.inform("           Ask unavailable")

    def _take_action(self, best_ask, best_bid):
        """
        Take trade action based on best_ask and best_bid and market info.
        :param best_bid: Order object of best bid
        :param best_ask: Order object of best bid
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)

        # If there are currently no active orders
        if self.order_status == OrderStatus.INACTIVE:
            self.inform("Currently no active orders")
            if self._bot_type == BotType.MARKET_MAKER:
                other_order = (best_bid if self._role == Role.BUYER
                               else best_ask)
                self._market_maker_orders(other_order)
            elif self._bot_type == BotType.REACTIVE:
                other_order = (best_ask if self._role == Role.BUYER
                               else best_bid)
                self._reactive_orders(other_order)
            else:
                self.error("Found bot with non-MM-REACTIVE type")
                self.stop = True
            if self.order_status == OrderStatus.MADE:
                self._send_update_active_order()
                pass

    def received_order_book(self, order_book, market_id):
        """
        Most logic should reside in this function, and it should also
        cooperate with other classes
        :param order_book: The order book of specific market
        :param market_id:  Id of the corresponding market
        :return: No return. Only processes to be executed.
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        self.inform("received order book from %d" % market_id)

        try:
            if self.order_status == OrderStatus.ACCEPTED:
                self.mm_order_cycle += 1

            mine_orders, best_bid, best_ask = \
                self._process_order_book(order_book)
            self.mine_orders = mine_orders

            # Show some information about current bid ask spread
            self._get_bid_ask_spread(best_bid, best_ask)

            self._update_mine_orders(mine_orders, best_bid, best_ask)
            # Print trade opportunities based on the role
            if self._role == Role.BUYER:
                self._print_trade_opportunity(best_ask)
            elif self._role == Role.SELLER:
                self._print_trade_opportunity(best_bid)

            self._take_action(best_ask, best_bid)
            self.inform("Current order status is: " + str(self.order_status))
            if self._bot_type == BotType.MARKET_MAKER:
                self.inform("Current mm_order_cycle is " +
                            str(self.mm_order_cycle))
            # Create bid-ask spread and check for depth of order
            # Depending on role, choose to buy or sell at relevant price
        except Exception as e:
            self._exception_inform(e, inspect.stack()[0][3])

    def received_marketplace_info(self, marketplace_info):
        session_id = marketplace_info["session_id"]
        if marketplace_info["status"]:
            print("Marketplace is now open with session id " + str(session_id))
        else:
            print("Marketplace is now closed.")

    # TODO implement this part
    def received_completed_orders(self, orders, market_id=None):
        pass

    def received_holdings(self, holdings):
        """
        Read current holdings of account to make sure trade is possible
        :param holdings: Holdings of the account (Cash, Available Cash, Units,
               Available units)
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        cash_holdings = holdings["cash"]
        self.inform("Total cash: " + str(cash_holdings["cash"]) +
                    " available cash: " + str(cash_holdings["available_cash"]))
        if cash_holdings["cash"] > cash_holdings["available_cash"]:
            self.inform("Total cash %d != available cash")
            if self.order_status != OrderStatus.ACCEPTED:
                str_mine_orders = ""
                for mine_order in self.mine_orders:
                    str_mine_orders += str(mine_order) + " ;; "
                self.warning("Order %s status is %s while cash is not "
                             "consistent. And mine_orders has %s"
                             % (str(self.active_order),
                                str(self.order_status),
                                str_mine_orders))

        unit_holdings = holdings["markets"][self._market_id]
        # for market_id, market_holding in holdings["markets"].items():
        #     self.inform("Market ID " + str(market_id) + ": total units: " +
        #                 str(market_holding["units"]) + ", available units: "+
        #                 str(market_holding["available_units"]))
        self.inform("Market ID " + str(self._market_id) + ": total units: " +
                    str(unit_holdings) + ", available units: " +
                    str(unit_holdings["available_units"]))
        if cash_holdings["units"] > cash_holdings["available_units"]:
            self.inform("Total units %d != available units")
            if self.order_status != OrderStatus.ACCEPTED:
                str_mine_orders = ""
                for mine_order in self.mine_orders:
                    str_mine_orders += str(mine_order) + " ;; "
                self.warning("Order %s status is %s while unit is not "
                             "consistent. And mine_orders has %s "
                             % (str(self.active_order),
                                str(self.order_status),
                                str_mine_orders))

    def order_accepted(self, order):
        """
        To process accepted_order and verify against stored active_order
        :param order:
        :return:
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        self.inform("Order was accepted in market " + str(self._market_id))

        if order.type == OrderType.LIMIT:
            if self._order_weak_equal(self.active_order, order) is True:
                if not self.order_status == OrderStatus.PENDING:
                    self.warning("Order %s accepted with state: %s"
                                 % (str(self.active_order),
                                    str(self.order_status)))
                # the new order have id for canceling
                self.active_order = order
                self.order_status = OrderStatus.ACCEPTED
            else:
                self.error("accepted_order %s is different from"
                           "active_order %s, changing to new_order"
                           % (str(order), str(self.active_order)))
                self.inactive_order.append([self.active_order, None])
                self.active_order = order
                self.order_status = OrderStatus.ACCEPTED

        elif order.type == OrderType.CANCEL:
            if self._order_weak_equal(self.active_order, order, cancel=True):
                if not self.order_status == OrderStatus.CANCEL:
                    self.warning("Order %s canceled with state: %s"
                                 % (str(order), self.order_status))
                self.inactive_order.append([self.active_order, order])
                self.active_order = None
                self.order_status = OrderStatus.INACTIVE
            else:
                self.error("rejected_order %s is different from"
                           "active_order %s"
                           % (str(order), str(self.active_order)))
                new_order = copy.copy(order)
                new_order.type = OrderType.LIMIT
                self.inactive_order.append([new_order, order])
        else:
            try:
                self.warning("Order %s is of type %s"
                             % (str(order), str(order.type)))
            except Exception as e:
                self._exception_inform(e, inspect.stack()[0][3])

    def order_rejected(self, info, order):
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        self.inform("Order was rejected in market " + str(self._market_id))
        self.warning("Rejection info: %s" % str(info))

        if order.type == OrderType.LIMIT:
            # Different order
            if not self._order_weak_equal(self.active_order, order):
                self.error("rejected_order %s is different from"
                           "active_order %s, changing to new_order"
                           % (str(order), str(self.active_order)))
                return
            # Same order
            elif self.order_status != OrderStatus.PENDING:
                self.warning("Order %s rejected while "
                             "active_order %s in state: %s"
                             % (str(order), str(self.active_order),
                                str(self.order_status)))
            self.inactive_order.append([self.active_order, None])
            self.active_order = None
            self.order_status = OrderStatus.INACTIVE
        elif order.type == OrderType.CANCEL:
            # Different order
            if not self._order_weak_equal(self.active_order, order,
                                          cancel=True):
                self.error("rejected_order %s is different from"
                           "active_order %s, changing to new_order"
                           % (str(order), str(self.active_order)))
                return
            # Same order
            elif self.order_status != OrderStatus.CANCEL:
                self.warning("Order %s rejected while "
                             "active_order %s in state: %s"
                             % (str(order), str(self.active_order),
                                str(self.order_status)))
            # It's unsure here, but accepted will be a sufficient guess
            else:
                self.inform("Cancel Order %s is rejected (active order %s)"
                            % (str(order), str(self.active_order)))
                self.order_status = OrderStatus.ACCEPTED
        else:
            try:
                self.warning("Order %s is of type %s"
                             % (str(order), str(order.type)))
            except Exception as e:
                self._exception_inform(e, inspect.stack()[0][3])

    def _print_trade_opportunity(self, other_order):
        """
        Depending on our role and our bot type, print trade opportunity.
        :param other_order: The other order on market to trade with
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        try:
            # Process best BUY, SELL order --> collect information -->
            # If valid order --> print

            if other_order and isinstance(other_order, Order):
                # other_order is not mine
                if other_order.mine is not True:
                    order = self._make_opposite_order(other_order)
                    order_availability = self._verify_order(order)
                    if (order is not None and
                            self._order_profitable(order) <= 0):
                        return
                # Already posted best trade
                else:
                    return

                # From the given template
                self.inform("[" + str(self._role) + str(other_order))

                # Inform the results
                if len(set(order_availability.values())) == 1:
                    self.warning("only one value found in %s"
                                 % str(order_availability))
                    return
                can_trade = (False if False in order_availability.values()
                             else True)
                if order.side == OrderSide.SELL:
                    information = (":unit_available" if
                                   order_availability[":unit_available"]
                                   else ":unit_unavailable")
                else:
                    information = (":cash_available" if
                                   order_availability[":cash_available"]
                                   else ":cash_unavailable")
                information = "status" + (":have_trade" if can_trade else
                                          ":no_trade") + information
                self.inform(information)

            # Other other is not None and of other classes, means bugs
            elif other_order is not None:
                self.warning(str(type(other_order)) +
                             "is not Order Object")
        except Exception as e:
            self._exception_inform(e, inspect.stack()[0][3])

    def _cancel_sent_order(self):
        """
        High level interface for cancelling current active_order who must be
        PENDING or ACCEPTED
        :return: the cancel_order created
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        # First check order status before canceling
        # (can only cancel accepted)
        if self.order_status == OrderStatus.ACCEPTED:
            self.inform("Cancelling order %s" % str(self.active_order))
            cancel_order = self._make_cancel_order(self.active_order)
            self.send_order(cancel_order)
            # Reset the cycle
            self.mm_order_cycle = 0
            self.order_status = OrderStatus.CANCEL
            return cancel_order
        else:
            self.warning("Order cancelled while "
                         "not PENDING or ACCEPTED!")
            return None

    @staticmethod
    def _make_order_ref(market_id, order_price, order_side,
                        order_unit=ORDER_UNIT, order_type=OrderType.LIMIT):
        """
        Make the standard reference for an order
        :param market_id:   Id of the traded market
        :param order_price: Price traded at
        :param order_side:  Buy or sell
        :param order_unit:  How many units
        :param order_type:  Limit or Cancel
        :return:            A standard string containing all information
        """
        ref = ":" + ORDER_SIDE_TO_CHAR[order_side] + SEPARATION
        ref += str(market_id) + SEPARATION
        ref += str(order_price) + SEPARATION
        ref += str(order_unit) + SEPARATION
        ref += time.strftime(TIME_FORMATTER, time.localtime())
        ref += ORDER_TYPE_TO_CHAR[order_type]
        return ref

    def _make_order(self, order_price, order_side, order_unit=ORDER_UNIT,
                    order_type=OrderType.LIMIT):
        """
        Make and return an order
        :param order_price: price made after decision
        :param order_side:  buyer or seller
        :param order_unit:  (Optional, not available) Traded units
        :param order_type:  (Optional, not available) Type of order
        :return:            The made order, None if error happens
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        ref = self._make_order_ref(self._market_id, order_price, order_side)
        order = Order(order_price, order_unit, order_type,
                      order_side, self._market_id, ref=ref)
        self.inform("order- %s" % str(order))
        return order

    def _make_opposite_order(self, other_order):
        """
        Make an total opposite order to trade with other_order
        :param other_order: The order to trade with
        :return:            The made order, None if error happens or
                            other_order is None
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        if other_order and isinstance(other_order, Order):
            side = (OrderSide.SELL if other_order.side == OrderSide.BUY
                    else OrderSide.BUY)
            return self._make_order(other_order.price, side, other_order.units)
        return None

    def _make_cancel_order(self, order):
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        if order is not None and isinstance(order, Order):
            if order.type == OrderType.CANCEL:
                self.warning("Making CANCEL order for CANCEL order %s"
                             % str(order))
            # To cancel an order, must have it's id, so use copy
            cancel_order = copy.copy(order)
            cancel_order.type = OrderType.CANCEL
            return cancel_order
        else:
            return None

    def _set_active_order(self, order):
        """
        Update the new order made to be an OrderStatus.MADE order
        :param order: The order to be updated
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        if self.order_status not in [OrderStatus.INACTIVE,
                                     OrderStatus.CANCEL]:
            self.error("Old order is still in %s state" %
                       str(self.order_status))
        self.active_order = order
        self.order_status = OrderStatus.MADE

    # Tweaking the function a bit to incorporate to other functions
    def _verify_order(self, order):
        """
        Verify the given order with own holdings and return a dictionary
        containing availability of the order
        :param order: The order to be verified(Only price, units, side, needed)
        :return:
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)

        order_availability = copy.copy(ORDER_AVAILABILITY_TEMPLATE)
        if order and isinstance(order, Order):
            # BUY side
            if order.side == OrderSide.BUY:
                # Not enough mana
                if (order.price * order.units >
                        self.holdings["cash"]["available_cash"]):
                    order_availability["cash_available"] = False
                else:
                    order_availability["cash_available"] = True
            # SELL side
            elif order.side == OrderSide.SELL:
                if (order.units > self.holdings["markets"]
                        [self._market_id]["available_units"]):
                    order_availability["unit_available"] = False
                else:
                    order_availability["unit_available"] = True
            else:
                self.error("Found order with non-BUY-SELL type")
                self.stop = True
        elif order is None:
            self.inform("No order to verify.")
        else:
            self.warning(str(type(order)) +
                         "is not Order object")

        self.inform("order- %s, availability- %s"
                    % (order, str(order_availability)))
        return order_availability

    def _send_update_active_order(self):
        """
        MAKE --> VERIFY --> PRINT(with verified message) --> SEND
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        self.order_availability = self._verify_order(self.active_order)
        if self.order_status != OrderStatus.MADE:
            self.warning("Active order with order status %s is sent"
                         % str(self.order_status))

        if (self.order_availability["cash_available"] is True or
                self.order_availability["unit_available"] is True):
            self.inform("Sending order")
            self.send_order(self.active_order)
            self.order_status = OrderStatus.PENDING

    def _order_profitable(self, order):
        """
        Check if an order is profitable
        :param order: The order to check
        :return: positive value if positive, zero or negative if not
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        if order and isinstance(order, Order):
            # Buying at a lower price
            if order.side == OrderSide.BUY:
                # units currently holding
                units = self.holdings["markets"][self._market_id]["units"]
                # After purchasing the networth is larger
                net_current = units * DS_REWARD_CHARGE
                net_after = (min(MAX_REWARD_UNIT, units + order.units) *
                             DS_REWARD_CHARGE - order.price * order.units)
                self.inform("BuyOrder: NetCurrent=%dx%d=%d, "
                            "NetAfter=min(%d, %d+%d)x%d-%dx%d=%d"
                            % (units, DS_REWARD_CHARGE, net_current,
                               MAX_REWARD_UNIT, units, order.units,
                               DS_REWARD_CHARGE, order.price, order.units,
                               net_after))
                return net_after - net_current
            # Selling at a higher price
            elif order.side == OrderSide.SELL:
                self.inform("SellOrder: OrderPrice:%d, DSReward:%d"
                            % (order.price, DS_REWARD_CHARGE))
                return (order.price - DS_REWARD_CHARGE) * order.units
        return None

    def _market_maker_orders(self, other_order):
        """
        When bot is set to market maker, this function creates the appropriate
        order
        :param other_order: The best order of same side to compare with
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)

        # Bot is a buyer
        if self._role == Role.BUYER:
            order = self._mm_buyer_order(other_order)
        # Bot is a seller
        elif self._role == Role.SELLER:
            order = self._mm_seller_order(other_order)
        else:
            self.error("Found order with non-BUY-SELL type")
            self.stop = True
            return

        if order is not None and self._order_profitable(order) > 0:
            self._set_active_order(order)

    def _mm_buyer_order(self, other_order):
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        tick = self.markets[self._market_id]["tick"]
        minimum = self.markets[self._market_id]["minimum"]
        # Bot is a buyer
        order_side = OrderSide.BUY
        if other_order is None:
            order_price = ((DS_REWARD_CHARGE - minimum) //
                           tick // 2 * tick) + minimum
        elif other_order.mine is True:
            return None
        # Check if we can set a bid which beats the current best bid
        elif other_order.price + tick < DS_REWARD_CHARGE:
            order_price = other_order.price + tick
        # Check if current best bid is profitable,
        # but increasing the bid makes it unprofitable
        elif other_order.price < DS_REWARD_CHARGE:
            order_price = other_order.price
        # Best buy price is 1 tick less than DS_REWARD_CHARGE
        else:
            order_price = ((DS_REWARD_CHARGE - minimum) //
                           tick * tick) + minimum
        return self._make_order(order_price, order_side)

    def _mm_seller_order(self, other_order):
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        tick = self.markets[self._market_id]["tick"]
        maximum = self.markets[self._market_id]["maximum"]
        order_side = OrderSide.SELL
        if other_order is None:
            order_price = maximum - ((maximum - DS_REWARD_CHARGE)
                                     // tick // 2 * tick)
        elif other_order.mine is True:
            return None
        # Check if we can set an ask which beats the current best ask
        elif other_order.price - tick > DS_REWARD_CHARGE:
            order_price = other_order.price - tick
        # Check if current best ask is profitable, but
        # decreasing the ask makes it unprofitable
        elif other_order.price > DS_REWARD_CHARGE:
            order_price = other_order.price
        # Best ask price is 1 tick more than DS_REWARD_CHARGE
        else:
            order_price = maximum - ((maximum - DS_REWARD_CHARGE)
                                     // tick * tick)
        return self._make_order(order_price, order_side)

    def _reactive_orders(self, other_order):
        """
        When bot is set to reactive, make orders using this
        :param other_order: The best order to trade with
        :return:            makes order according to role
        """
        self._line_break_inform(inspect.stack()[0][3],
                                length=BASE_LEN + INIT_STACK * STACK_DIF -
                                get_stack_size() * STACK_DIF)
        self.inform("other_order- %s" % str(other_order))

        # Make the opposite order
        order = self._make_opposite_order(other_order)

        # If the opposite order exists and is profitable then set it to
        # be active order
        if order is not None and self._order_profitable(order) > 0:
            # sanity check
            if order.side == OrderSide.BUY:
                if self._role != Role.BUYER:
                    self.error("Order %s and Role %s doesn't correspond"
                               % (order.side, self._role))
            elif OrderSide == OrderSide.SELL:
                if self._role != Role.SELLER:
                    self.error("Order %s and Role %s doesn't correspond"
                               % (order.side, self._role))
            self._set_active_order(order)

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

    def _exception_inform(self, msg, fn_name):
        """
        Show the exception message with function name
        :param msg: exception to inform
        """
        assert isinstance(msg, Exception), ("msg %s is not an exception"
                                            % str(msg))
        self.inform("^^^Exception in function %s^^^:"
                    "msg: %s" % (fn_name, str(msg))
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

    # Archived No longer need to be used
    # def _warning_inform(self, msg):
    #     """
    #     INFORM warning message
    #     :param msg: message to warn
    #     """
    #     self.inform("***WARNING*** %s" % msg)
    #
    # def _error_inform(self, msg):
    #     """
    #     INFORM error message
    #     :param msg: message to error
    #     """
    #     self.inform("@@@@ERROR@@@@%s" % msg)


if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"

    FM_EMAIL_CALVIN = "z.huang51@student.unimelb.edu.au"
    FM_PASSWORD_CALVIN = "908525"

    FM_EMAIL_JD = "j.lee161@student.unimelb.edu.au"
    FM_PASSWORD_JD = "888086"

    MARKETPLACE_ID1 = 260
    MARKETPLACE_ID2 = 352

    ds_bot = DSBot(FM_ACCOUNT, FM_EMAIL_JD, FM_PASSWORD_JD, MARKETPLACE_ID2)
    ds_bot.run()
