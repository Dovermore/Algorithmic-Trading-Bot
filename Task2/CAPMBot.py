"""
This is a template bot for  the CAPM Task.
"""

from fmclient import Agent
from fmclient import Order, OrderSide, OrderType

# Group details
GROUP_MEMBERS = {"1234": "Name 1", "4567": "Name 2"}


class CAPMBot(Agent):

    def __init__(self, account, email, password, marketplace_id, risk_penalty=0.01, session_time=20):
        """
        Constructor for the Bot
        :param account: Account name
        :param email: Email id
        :param password: password
        :param marketplace_id: id of the marketplace
        :param risk_penalty: Penalty for risk
        :param session_time: Total trading time for one session
        """
        super().__init__(account, email, password, marketplace_id, name="CAPM Bot")
        self._payoffs = {}
        self._risk_penalty = risk_penalty
        self._session_time = session_time
        self._market_ids = {} 

    def initialised(self):
        for market_id, market_info in self.markets.items():
            security = market_info["item"]
            description = market_info["description"]
            self._payoffs[security] = [int(a) for a in description.split(",")]

    def get_potential_performance(self, orders):
        """
        Returns the portfolio performance if the given list of orders is executed.
        The performance as per the following formula:
        Performance = ExpectedPayoff - b * PayoffVariance, where b is the penalty for risk.
        :param orders: list of orders
        :return:
        """
        pass

    def is_portfolio_optimal(self):
        """
        Returns true if the current holdings are optimal (as per the performance formula), false otherwise.
        :return:
        """
        pass

    def order_accepted(self, order):
        pass

    def order_rejected(self, info, order):
        pass

    def received_order_book(self, order_book, market_id):
        pass

    def received_completed_orders(self, orders, market_id=None):
        pass

    def received_holdings(self, holdings):
        pass

    def received_marketplace_info(self, marketplace_info):
        pass

    def run(self):
        self.initialise()
        self.start()


if __name__ == "__main__":
    FM_ACCOUNT = "bullish-delight"
    FM_EMAIL = "<email>"
    FM_PASSWORD = "<password>"
    MARKETPLACE_ID = -1  # replace this with the marketplace id

    bot = CAPMBot(FM_ACCOUNT, FM_EMAIL, FM_PASSWORD, MARKETPLACE_ID)
    bot.run()
