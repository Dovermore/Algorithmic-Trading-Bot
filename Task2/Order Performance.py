import time
import timeit

available_orders = {
                    250: [[400, 4, 'bid'], [600, 5, 'ask']],  # Stock A
                    350: [[550, 3, 'bid'], [700, 6, 'ask']],  # Stock B
                    450: [[450, 5, 'bid'], [550, 2, 'ask']],  # Stock C
                    550: [[300, 4, 'bid'], [650, 7, 'ask']]   # risk-free
                    }

holdings = {
                250: 10,  # Stock A
                350: 10,  # Stock B
                450: 10,  # Stock C
                550: 10   # risk-free
                }

payoff = [[10, 0, 0, 5], [0, 2.5, 7.5, 5],
          [0, 7.5, 2.5, 5], [5, 5, 5, 5]]  # Return table


def payoff_variance(payoff):
    num_states = len(payoff[0])
    print(num_states)


def payoff_covariance(payoff):
    pass


def units_payoff_variance(units, variance, covariance):
    pass


variance = payoff_variance(payoff)
covariance = payoff_variance(payoff)


def calculate_performance(holding, b=-0.01):
    """
    Calculates the portfolio performance
    :param holding: assets held
    :param b: risk penalty, given -0.01
    :return: performance
    """
    pass


t0 = time.time()


def make_orders(orders, holding):
    store_orders = {}
    holding1 = holding
    for market in orders.keys():
        market_to_check = orders[market]
        order_to_make = None
        holding2 = holding1

        for buy_sell in market_to_check:
            price, units, side = buy_sell
            performance_to_compare = None

            for potential_order_units in range(1, units):

                if side == 'bid':
                    holding2[market] += potential_order_units
                elif side == 'ask':
                    holding2[market] -= potential_order_units

                performance = calculate_performance(holdings)
                if performance_to_compare:
                    performance_to_compare = performance
                    order_to_make = [potential_order_units, side]
                else:
                    if performance_to_compare < performance:
                        performance_to_compare = performance
                        order_to_make = [potential_order_units, side]

        store_orders[market] = order_to_make

    return store_orders


t1 = time.time()
make_orders(available_orders, holdings)
# duration = timeit.timeit(make_orders(available_orders), number=1000)
# print("best order: " + str(duration))
print("best order: " + str(t1-t0))

# ---------------------------------------------------------------------------

t0 = time.time()
order = None


def best_orders(orders):
    pass


t1 = time.time()

# duration = timeit.timeit(make_orders(available_orders), number=1000)
# print("make orders: " + str(duration))
print("make orders: " + str(t1-t0))

