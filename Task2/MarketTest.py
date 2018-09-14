import random
from typing import List


class Market:
    _states = -1

    def __init__(self, market_dict: dict):
        self._market_id = market_dict["id"]
        self._minimum = market_dict["minimum"]
        self._maximum = market_dict["maximum"]
        self._tick = market_dict["tick"]
        self._name = market_dict["name"]
        self._item = market_dict["item"]
        self._description = market_dict["description"]
        self._payoffs = tuple(int(a) for a in self._description.split(","))
        self._expected_return = sum(self._payoffs) / self._states
        self._covariances = {}
        if self._states == -1:
            self._states = len(self._payoffs)
        else:
            assert len(self._payoffs) != self._states

    @property
    def market_id(self):
        return self._market_id

    @property
    def minimum(self):
        return self._minimum

    @property
    def maximum(self):
        return self._maximum

    @property
    def tick(self):
        return self._tick

    @property
    def name(self):
        return self._name

    @property
    def item(self):
        return self._item

    @property
    def description(self):
        return self._description

    @property
    def payoffs(self):
        return self._payoffs

    @property
    def expected_return(self):
        return self._expected_return

    @property
    def covariances(self):
        return self._covariances

    @classmethod
    def states(cls):
        return cls._states

    def is_valid_price(self, price: int) -> bool:
        """
        Check if price is valid, that is, it's proper considering minimum,
        minimum and tick
        :param price: The price to be checked
        :return: True if valid, else false
        """
        # TODO implement

    def build_covariance(self, markets):
        for market in markets:
            self._covariances[market.market_id] = \
                self.compute_covariance(self._payoffs, market.payoffs)

    @staticmethod
    def compute_covariance(payoff1: List[int],
                           payoff2: List[int]) -> float:
        """
        Compute the covariance between list of payoff1 and payoff2, they
        have to be the same length
        :param payoff1: List of payoff1
        :param payoff2: List of payoff2
        :return: the covariance value
        """
        # TODO implement compute covariance procedure


if __name__ == "__main__":
    id_range = [1, 500]
    minimum = 10
    maximum = 1000
    tick_choice = [5, 10, 15]
    state_choice = [0,5,10,15,20]
    n_state = 3

    markets = []

    ids = []
    tick = random.choice(tick_choice)
    for i in range(5):
        mid = random.randint(*id_range)
        while mid in ids:
            mid = random.randint(*id_range)
        name = "name" + str(i)
        item = "item" + str(i)
        description = ""
        for j in range(n_state):
            description += str(random.choice(state_choice)) + ","
        description = description[:-1]

        market_dict = {}
        market_dict["id"] = mid
        market_dict["minimum"] = minimum
        market_dict["maximum"] = maximum
        market_dict["tick"] = tick
        market_dict["name"] = name
        market_dict["item"] = item
        market_dict["description"] = description
        markets.append(Market(market_dict))

    for i in range(5):
        print(markets[i])
        for j in range(5):
            markets[i].build_covariance(markets)
        print(str(markets[i].payoffs))
        print(str(markets[i].covariances.items()))