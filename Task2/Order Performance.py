import time
import timeit
from fmclient import Order, OrderSide, OrderType

available_orders = {
                    250: [[400, 4, 'bid'], [600, 5, 'ask']],  # Stock A
                    350: [[550, 3, 'bid'], [700, 6, 'ask']],  # Stock B
                    450: [[450, 5, 'bid'], [550, 2, 'ask']],  # Stock C
                    550: [[300, 4, 'bid'], [650, 7, 'ask']]   # risk-free
                    }


t0 = time.time()
store_orders = []


def best_order(orders):
    pass


t1 = time.time()

duration = timeit.timeit(best_order, number=1000)
print(duration)
print(t1-t0)

# ---------------------------------------------------------------------------

t0 = time.time()
order = None


def make_orders(orders):
    pass


t1 = time.time()

duration = timeit.timeit(make_orders, number=1000)
print(duration)
print(t1-t0)


