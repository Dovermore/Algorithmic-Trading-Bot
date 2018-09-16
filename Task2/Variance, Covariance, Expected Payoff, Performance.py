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
            250: [1000, 0, 750, 250],
            350: [0, 250, 750, 1000],
            450: [0, 750, 250, 1000],
            550: [500, 500, 500, 500]
            }  # Return table


def payoff_variance(payoff, num_states=4):
    squared_states = []
    for states in payoff:
        squared_states.append(states**2)
    return (1/num_states*sum(squared_states))-((1/(num_states**2))*sum(payoff)**2)


def all_variance(given_payoffs, num_states=4):
    cal_variances = {}
    for individual_stock in given_payoffs:
        ind_variance = payoff_variance(given_payoffs[individual_stock], num_states)
        cal_variances[individual_stock] = ind_variance
    return cal_variances


def expected_return(stock, num_state=4, num_stocks=1):
    exp_ret = num_stocks*sum(stock)/num_state
    return exp_ret


def initial_expected_return(given_payoffs, num_states=4):
    expected_returns = {}
    for individual_stock in given_payoffs:
        ind_exp_ret = expected_return(given_payoffs[individual_stock],
                                      num_states)
        expected_returns[individual_stock] = ind_exp_ret
    return expected_returns


def update_expected_return(units, given_payoffs, num_states=4):
    expected_returns = {}
    for individual_stock in given_payoffs:
        ind_exp_ret = expected_return(given_payoffs[individual_stock],
                                      num_states,
                                      units[individual_stock])
        expected_returns[individual_stock] = ind_exp_ret
    return expected_returns


def payoff_covariance(first_stock, second_stock, num_states=4):
    first_stock_payoff = payoffs[first_stock]
    second_stock_payoff = payoffs[second_stock]
    multiplied = []
    for num in range(num_states):
        multiplied.append(first_stock_payoff[num]*second_stock_payoff[num])
    return (1/num_states)*sum(multiplied) - \
           (ini_exp_ret[first_stock]*ini_exp_ret[second_stock])


def total_covariance(given_payoffs, num_states=4):
    cal_covariance = {}
    for first_iter_stocks in given_payoffs.keys():
        for second_iter_stocks in given_payoffs.keys():
            to_be_key = sorted([first_iter_stocks, second_iter_stocks])
            key_for_dict = str(to_be_key[0])+'-'+str(to_be_key[1])
            if first_iter_stocks != second_iter_stocks and \
                    key_for_dict not in cal_covariance:
                individual_covariance = payoff_covariance(first_iter_stocks,
                                                          second_iter_stocks,
                                                          num_states)
                cal_covariance[key_for_dict] = individual_covariance
    return cal_covariance


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


print('variance')
variances = all_variance(payoffs)
print(variances)
print('')
print('initial expected_returns')
ini_exp_ret = initial_expected_return(payoffs)
print(ini_exp_ret)
print('')
print('updated expected return')
new_exp_ret = update_expected_return(holdings, payoffs)
print(new_exp_ret)
print('')
print('covariances')
covariances = total_covariance(payoffs)
print(covariances)
print('')
print('total payoff variance')
tot_payoff_variance = units_payoff_variance(holdings, variances, covariances)
print(tot_payoff_variance)


def calculate_performance(holding, b=-0.01):
    """
    Calculates the portfolio performance
    :param holding: assets held
    :param b: risk penalty, given -0.01
    :return: performance
    """
    tot_payoff_variance = units_payoff_variance(holding, variances, covariances)
    new_expected_return = update_expected_return(holdings, payoffs)
    expected_payoff = sum(new_expected_return.values())
    return expected_payoff+b*tot_payoff_variance

print('')
print('performance')
print(calculate_performance(holdings))
