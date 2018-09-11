import time
import timeit
from fmclient import Order, OrderSide, OrderType
import random

random.seed(100)

order_side = {
    0: OrderSide.BUY,
    1: OrderSide.SELL
}

order_list = []

for x in range(10):
    units = random.randint(1, 5)
    side = order_side[random.randint(0, 1)]
    price = random.randint(0, 1000)//5*5
    order_to_make = Order(price, units, OrderType.LIMIT, side, 250)
    order_list.append(order_to_make)

for i in range(10):
    print(order_list[i])

t0 = time.time()
order = None


def best_orders(orders):
    for order in orders:
        pass


t1 = time.time()

duration = timeit.timeit(best_orders, number=1000)
print(duration)
