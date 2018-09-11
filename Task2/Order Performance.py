import time
import timeit

t0 = time.time()


def best_orders():
    pass


t1 = time.time()

duration = timeit.timeit(best_orders, number=1000)
print(duration)
