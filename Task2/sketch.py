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

payoffs = {
            250: [10, 0, 0, 5],
            350: [0, 2.5, 7.5, 5],
            450: [0, 7.5, 2.5, 5],
            550: [5, 5, 5, 5]
            }  # Return table


def payoff_variance(payoff, num_state):
    squared_states = []
    for states in payoff:
        squared_states.append(states**2)
    return (1/num_state*sum(squared_states))-((1/(num_states**2))*sum(payoff)**2)


def expected_return(stock, num_state):
    exp_ret = sum(stock)/num_state
    return exp_ret


def payoff_covariance(first_stock, second_stock, num_state):
    first_stock_payoff = payoffs[first_stock]
    second_stock_payoff = payoffs[second_stock]
    multiplied = []
    for num in range(num_state):
        multiplied.append(first_stock_payoff[num]*second_stock_payoff[num])
    return (1/num_state)*sum(multiplied) - \
           (expected_returns[first_stock]*expected_returns[second_stock])


def units_payoff_variance(units, variance, covariance):
    total_variance = 0
    for market_id in units.keys():
        market_id = market_id
        total_variance += (units[market_id]**2)*(variance[market_id])
    for market_ids in covariance.keys():
        ind_market_id = market_ids.split('-')
        total_variance += 2*units[int(ind_market_id[0])] * \
                          units[int(ind_market_id[1])] * covariance[market_ids]
    return total_variance


num_states = 4
variances = {}
expected_returns = {}
covariances = {}
for individual_stock in payoffs:
    ind_variance = payoff_variance(payoffs[individual_stock], num_states)
    ind_exp_ret = expected_return(payoffs[individual_stock], num_states)
    expected_returns[individual_stock] = ind_exp_ret
    variances[individual_stock] = ind_variance

for first_iter_stocks in payoffs.keys():
    for second_iter_stocks in payoffs.keys():
        to_be_key = sorted([first_iter_stocks, second_iter_stocks])
        key_for_dict = str(to_be_key[0])+'-'+str(to_be_key[1])
        if first_iter_stocks != second_iter_stocks and \
                key_for_dict not in covariances:
            individual_covariance = payoff_covariance(first_iter_stocks,
                                                      second_iter_stocks,
                                                      num_states)
            covariances[key_for_dict] = individual_covariance

print('variance')
print(variances)
print('expected_returns')
print(expected_returns)
print('covariances')
print(covariances)

tot_payoff_variance = units_payoff_variance(holdings, variances, covariances)
print(tot_payoff_variance)
