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

payoffs = [[10, 0, 0, 5], [0, 2.5, 7.5, 5],
          [0, 7.5, 2.5, 5], [5, 5, 5, 5]]  # Return table


def payoff_variance(payoff):
    num_states = len(payoff)
    squared_states = []
    for states in payoff:
        squared_states.append(states**2)
    return (1/num_states*sum(squared_states))-(1/(num_states**2)*sum(payoff)**2)


def expected_return(stock):
    num_states = len(stock)
    exp_ret = sum(stock)/num_states
    return exp_ret


def payoff_covariance(stock_one_payoff, stock_two_payoff):
    for state_one in stock_one_payoff:
        pass


def units_payoff_variance(units, variance, covariance):
    pass


variances = []
expected_returns = []
for stocks in payoffs:
    variance = payoff_variance(stocks)
    ind_exp_ret = expected_return(stocks)
    expected_returns.append(ind_exp_ret)
    variances.append(variance)
print(variances)
print(expected_returns)

# for stockA in payoffs:
#     for stockB in payoffs:
#        covariance = payoff_covariance(stockA, stockB)

# tot_payoff_variance = units_payoff_variance(holdings,variance, covariance)
