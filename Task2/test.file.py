orders = []
current_performance = 0

orders = [order for order in orders if
          order[1] > current_performance]