from marketsim import Market, Order, OrderStat, Side
import re
import unittest

class TestOrderBook(unittest.TestCase):
    def strip_spaces(self, str):
        str = re.sub(r'^\s+|\s+$', '', str)
        str = re.compile(r'^\s+', re.MULTILINE).sub('', str)
        return str

    def test_order_book_entry(self):
        market = Market()
        market.place(Order(Side.BUY, 'abc', 10, 110))
        market.place(Order(Side.SELL, 'abc', 10, 130))
        bid_order_book = market['abc'][Side.BUY].get_order_book()
        ask_order_book = market['abc'][Side.SELL].get_order_book()
        self.assertEqual(bid_order_book, [OrderStat(110, 10, 1)])
        self.assertEqual(ask_order_book, [OrderStat(130, 10, 1)])
        self.assertEqual(repr(bid_order_book[0]), 'OrderStat(price=110, volume=10, count=1)')
        self.assertEqual(repr(ask_order_book[0]), 'OrderStat(price=130, volume=10, count=1)')

    def test_side_order_book(self):
        market = Market()

        for price in [110, 120, 130, 140]:
            market.place(Order(Side.SELL, 'abc', 10, price))
            market.place(Order(Side.SELL, 'abc', 10, price))

        for price in [100, 110, 120, 130]:
            market.place(Order(Side.BUY, 'abc', 10, price))
            market.place(Order(Side.BUY, 'abc', 10, price))

    def test_format_order_book(self):
        market = Market()

        for price in [110, 120, 130, 140]:
            market.place(Order(Side.SELL, 'abc', 10, price))
            market.place(Order(Side.SELL, 'abc', 10, price))

        for price in [100, 110, 120, 130]:
            market.place(Order(Side.BUY, 'abc', 10, price))
            market.place(Order(Side.BUY, 'abc', 10, price))

        self.assertEqual(market['abc'].format_order_book(), self.strip_spaces(
            """
            | BID    | PRICE | ASK    |
            |========|=======|========|
            |        | 140   | 20 (2) |
            | 20 (2) | 130   | 20 (2) |
            | 20 (2) | 120   | 20 (2) |
            | 20 (2) | 110   | 20 (2) |
            | 20 (2) | 100   |        |
            """
        ))

        market.execute()

        self.assertEqual(market['abc'].format_order_book(), self.strip_spaces(
            """
            | BID    | PRICE | ASK    |
            |========|=======|========|
            |        | 140   | 20 (2) |
            |        | 130   | 20 (2) |
            | 20 (2) | 110   |        |
            | 20 (2) | 100   |        |
            """
        ))

    def test_order_book_after_cancel(self):
        market = Market()

        for price in [110, 120, 130, 140]:
            market.place(Order(Side.SELL, 'abc', 10, price, id='sell-{}-1'.format(price)))
            market.place(Order(Side.SELL, 'abc', 10, price, id='sell-{}-2'.format(price)))

        for price in [100, 110, 120, 130]:
            market.place(Order(Side.BUY, 'abc', 10, price, id='buy-{}-1'.format(price)))
            market.place(Order(Side.BUY, 'abc', 10, price, id='buy-{}-2'.format(price)))

        market.cancel(Order(id='buy-120-1', symbol='abc'))
        market.cancel(Order(id='sell-130-1', symbol='abc'))

        self.assertEqual(market['abc'].format_order_book(), self.strip_spaces(
            """
            | BID    | PRICE | ASK    |
            |========|=======|========|
            |        | 140   | 20 (2) |
            | 20 (2) | 130   | 10 (1) |
            | 10 (1) | 120   | 20 (2) |
            | 20 (2) | 110   | 20 (2) |
            | 20 (2) | 100   |        |
            """
        ))

        market.cancel(Order(id='buy-120-2', symbol='abc'))
        market.cancel(Order(id='sell-130-2', symbol='abc'))

        self.assertEqual(market['abc'].format_order_book(), self.strip_spaces(
            """
            | BID    | PRICE | ASK    |
            |========|=======|========|
            |        | 140   | 20 (2) |
            | 20 (2) | 130   |        |
            |        | 120   | 20 (2) |
            | 20 (2) | 110   | 20 (2) |
            | 20 (2) | 100   |        |
            """
        ))
