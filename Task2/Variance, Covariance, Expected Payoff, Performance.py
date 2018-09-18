import copy
import operator
origin_list = [
    {"name": "foo", "rank": 0, "rofl": 20000},
    {"name": "Silly", "rank": 15, "rofl": 1000},
    {"name": "Baa", "rank": 300, "rofl": 20},
    {"name": "Zoo", "rank": 10, "rofl": 200},
    {"name": "Penguin", "rank": -1, "rofl": 10000}
]
print(">> Original >>")
for foo in origin_list:
    print(foo)

print("\n>> Rofl sort >>")
print(sorted(origin_list, key=operator.itemgetter("rofl"), reverse=True)[0])

print("\n>> Rank sort >>")
for foo in sorted(origin_list, key=operator.itemgetter("rank")):
    print(foo)


available_orders = {
                    250: {"bid": {"price": 400, "units": 4},
                          'ask': {"price": 600, "units": 5}},  # Stock A
                    350: {"bid": {"price": 550, "units": 3},
                          'ask': {"price": 700, "units": 6}},  # Stock B
                    450: {"bid": {"price": 450, "units": 5},
                          'ask': {"price": 550, "units": 2}},  # Stock C
                    550: {"bid": {"price": 300, "units": 4},
                          'ask': {"price": 650, "units": 4}},  # risk-free
                    }

cash = 5000

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
total_payoff_variance = units_payoff_variance(holdings, variances, covariances)
print(total_payoff_variance)


def calculate_performance(orders_to_make, b=-0.01):
    """
    Calculates the portfolio performance
    :param orders_to_make: orders to make
    :param b: risk penalty, given -0.01
    :return: performance
    """
    try:
        holding = copy.copy(holdings)
        expected_payoff = cash

        for order in orders_to_make.keys():
            holding[order] = orders_to_make[order]['units']

            if orders_to_make[order]['side'] == 'buy':
                expected_payoff -= orders_to_make[order]['units']\
                                   * orders_to_make[order]['price']

            elif orders_to_make[order]['side'] == 'sell':
                expected_payoff += orders_to_make[order]['units']\
                                   * orders_to_make[order]['price']

        tot_payoff_variance = units_payoff_variance(holding, variances, covariances)

        for market in holding:
            expected_payoff += ini_exp_ret[market]*holding[market]

        return expected_payoff+b*tot_payoff_variance

    except Exception as e:
        print("Error Happened")
        print(e)


TEMPLATE_TO_MAKE_ORDER = {'price': 0, 'units': 0, 'side': 0}


def create_order():
    """
    Process best bid and best ask retrieved from market here
    :return: best combination of order that maximizes performance
    """
    orders_to_make = {}
    virtual_cash = cash        # virtual cash that only exist in the function
    holding = copy.copy(holdings)  # virtual holding that only exist in the function
    for market in available_orders.keys():
        orders_to_make[market] = copy.copy(TEMPLATE_TO_MAKE_ORDER)

    return orders_to_make


def check_performance(perform=None, to_compare=None):
    new_orders = create_order()
    new_performance = calculate_performance(new_orders)

    if perform is None and to_compare is None:
        return check_performance(perform=new_performance)

    elif to_compare is None:
        return check_performance(perform, new_performance)

    else:
        if perform < new_performance:
            # TODO make order here based on orders from calculate_performance
            return "Current best performing order is found!"

        elif perform > new_performance:
            return 'life'


def copy_price(order):
    pass


def make_price(order):
    pass


# check_performance()
sort_performance = []
# TEMPLATE_TO_MAKE_ORDER = {'price': 0, 'units': 0, 'side': 0}


def best_order(available):
    options_to_test = []
    for market in available.keys():
        m_market = {}
        for side in available[market].keys():
            units = available[market][side]['units']
            price = available[market][side]['price']
            for i in range(units):
                create = copy.copy(TEMPLATE_TO_MAKE_ORDER)
                create['price'] = price
                create['units'] = i
                create['side'] = side


print(best_order(available_orders))

















