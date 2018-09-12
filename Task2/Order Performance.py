import time
import timeit

available_orders = {
                    250: [[400, 4, 'bid'], [600, 5, 'ask']],  # Stock A
                    350: [[550, 3, 'bid'], [700, 6, 'ask']],  # Stock B
                    450: [[450, 5, 'bid'], [550, 2, 'ask']],  # Stock C
                    550: [[300, 4, 'bid'], [650, 7, 'ask']]   # risk-free
                    }


def calculate_performance(expected_payoff, payoff_var, risk_penalty = -0.01):
    """
    Calculates the portfolio performance
    :param expected_payoff: potential payoff at end of session
    :param payoff_var: variance of portfolio
    :param risk_penalty: given -0.01
    :return:
    """
    performance = expected_payoff - risk_penalty*payoff_var
    return performance


t0 = time.time()


def best_order(orders):
    store_orders = []
    for market in orders.keys():
        market_to_check = orders[market]
        for buy_sell in market_to_check:
            price, units, side = buy_sell
            for potential_order_units in range(1,units):
                performance_to_compare = None
                potential_order = None
                if side == 'bid':
                    add_payoff = 
                    add_var =
                    performance = calculate_performance(add_payoff, add_var)
        order_specs = []
        store_orders.append(order_specs)


t1 = time.time()
best_order(available_orders)
# duration = timeit.timeit(best_order(available_orders), number=1000)
# print("best order: " + str(duration))
print("best order: " + str(t1-t0))

# ---------------------------------------------------------------------------

t0 = time.time()
order = None


def make_orders(orders):
    pass


t1 = time.time()

# duration = timeit.timeit(make_orders(available_orders), number=1000)
# print("make orders: " + str(duration))
print("make orders: " + str(t1-t0))

