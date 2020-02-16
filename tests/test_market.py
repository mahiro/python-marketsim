from marketsim import Market, Order, Side, State, Product
import unittest

class TestMarket(unittest.TestCase):
    def execute(self, market, side, symbol, quantity, price = None):
        executions = market.execute(Order(side, symbol, quantity, price))
        return self.format_executions(executions)

    def format_executions(self, executions):
        return [(execution.quantity, execution.price) for execution in executions]

    def get_order_book(self, market, side, symbol):
        order_book = market[symbol][side].get_order_book()
        return [(entry.count, entry.volume, entry.price) for entry in order_book]

    def format_queue_stats(self, order_queue):
        return [
            order_queue.count,
            order_queue.volume,
            order_queue.market_order_count,
            order_queue.market_order_volume,
            order_queue.limit_order_count,
            order_queue.limit_order_volume,
        ]

    def test_market_products(self):
        market = Market()

        abcd = Product('abcd')
        self.assertIs(market.set_product('abcd', abcd), abcd)
        self.assertIs(market.get_product('abcd'), abcd)
        self.assertIs(market['abcd'], abcd)

        efgh = market.set_product('efgh', None)
        self.assertIsNotNone(market.get_product('efgh'))
        self.assertIsNotNone(market['efgh'])

        self.assertEqual(sorted(list(market)), ['abcd', 'efgh'])
        self.assertEqual(sorted(list(market.items())), [('abcd', abcd), ('efgh', efgh)])
        self.assertEqual(sorted(list(market.keys())), ['abcd', 'efgh'])
        self.assertEqual(sorted(list(market.values())), [abcd, efgh])

        self.assertEqual(set(market.get_products()), set([abcd, efgh]))

    def test_market_prices(self):
        market = Market()

        self.assertIsNone(market['abc'].bid_price)
        self.assertIsNone(market['abc'].ask_price)
        self.assertIsNone(market['abc'][Side.BUY].next_price)
        self.assertIsNone(market['abc'][Side.SELL].next_price)
        self.assertIsNone(market['abc'].last_price)

        market['abc'].last_price = 100
        self.assertEqual(market['abc'].last_price, 100)

        self.assertEqual(self.execute(market, Side.BUY, 'abc', 10, 100), [])
        self.assertEqual(self.execute(market, Side.BUY, 'abc', 10, 110), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, 120), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, 110), [(10, 110)])

        self.assertEqual(market['abc'].bid_price, 100)
        self.assertEqual(market['abc'].ask_price, 120)
        self.assertEqual(market['abc'][Side.BUY].next_price, 100)
        self.assertEqual(market['abc'][Side.SELL].next_price, 120)
        self.assertEqual(market['abc'].last_price, 110)

    def test_market_exceptions(self):
        market = Market()

        with self.assertRaises(KeyError):
            market.set_product(None, Product('invalid'))

        market.ensure_product('abc')

        with self.assertRaises(KeyError):
            market['abc']['invalid']

    def test_order_exceptions(self):
        market = Market()
        product = market.ensure_product('abc')
        order1 = Order(Side.BUY, 'abc', 10)

        # Order does not exist
        with self.assertRaises(ValueError):
            market.cancel(order1)
        with self.assertRaises(ValueError):
            product.cancel(order1)

        market.place(order1)

        # Order already exists
        with self.assertRaises(ValueError):
            market.place(order1)
        with self.assertRaises(ValueError):
            product.place(order1)

        order2 = Order(Side.SELL, 'abc', 20, 120)
        market.place(order2)
        market.execute()

        # Already fully filled  
        with self.assertRaises(ValueError):
            market.cancel(order1)

        market.cancel(order2)

        # Already cancelled
        with self.assertRaises(ValueError):
            market.cancel(order2)

    def test_limit_order_market_order(self):
        market = Market()
        self.assertEqual(self.execute(market, Side.BUY, 'abc', 10, 120), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, None), [(10, 120)])
        self.assertEqual(market['abc'].last_price, 120)
        self.assertIsNone(market['abc'].bid_price)
        self.assertIsNone(market['abc'].ask_price)

    def test_limit_order_limit_order(self):
        market = Market()
        self.assertEqual(self.execute(market, Side.BUY, 'abc', 10, 130), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, 110), [(10, 120)])
        self.assertEqual(market['abc'].last_price, 120)
        self.assertIsNone(market['abc'].bid_price)
        self.assertIsNone(market['abc'].ask_price)

    def test_market_order_limit_order(self):
        market = Market()
        self.assertEqual(self.execute(market, Side.BUY, 'abc', 10, None), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, 120), [(10, 120)])
        self.assertEqual(market['abc'].last_price, 120)
        self.assertIsNone(market['abc'].bid_price)
        self.assertIsNone(market['abc'].ask_price)

    def test_market_order_market_order(self):
        market = Market()
        self.assertEqual(self.execute(market, Side.BUY, 'abc', 10, None), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, None), [])
        self.assertEqual(market['abc'].last_price, None)
        self.assertIsNone(market['abc'].bid_price)
        self.assertIsNone(market['abc'].ask_price)

    def test_trading(self):
        market = Market()
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 40, 130), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 80, 130), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 10, 120), [])
        self.assertEqual(self.execute(market, Side.SELL, 'abc', 20, 120), [])

        self.assertEqual(self.get_order_book(market, Side.BUY, 'abc'), [])
        self.assertEqual(self.get_order_book(market, Side.SELL, 'abc'), [(2, 30, 120), (2, 120, 130)])

        self.assertEqual(self.execute(market, Side.BUY, 'abc', 45, None), [(10, 130), (20, 130), (15, 130)])
        self.assertEqual(market['abc'].last_price, 130)
        self.assertIsNone(market['abc'].bid_price)
        self.assertEqual(market['abc'].ask_price, 130)

        self.assertEqual(self.get_order_book(market, Side.BUY, 'abc'), [])
        self.assertEqual(self.get_order_book(market, Side.SELL, 'abc'), [(2, 105, 130)])

    def test_auction(self):
        market = Market()
        market.place(Order(Side.SELL, 'abc', 40, 130, time=0))
        market.place(Order(Side.SELL, 'abc', 80, 130, time=0))
        market.place(Order(Side.SELL, 'abc', 10, 120, time=0))
        market.place(Order(Side.SELL, 'abc', 20, 120, time=0))
        market.place(Order(Side.BUY, 'abc', 45, None, time=0))

        self.assertEqual(self.get_order_book(market, Side.BUY, 'abc'), [(1, 45, None)])
        self.assertEqual(self.get_order_book(market, Side.SELL, 'abc'), [(2, 30, 120), (2, 120, 130)])

        self.assertEqual(self.format_executions(market.execute()), [(10, 130), (20, 130), (5, 130), (10, 130)])
        self.assertEqual(market['abc'].last_price, 130)
        self.assertIsNone(market['abc'].bid_price)
        self.assertEqual(market['abc'].ask_price, 130)

        self.assertEqual(self.get_order_book(market, Side.BUY, 'abc'), [])
        self.assertEqual(self.get_order_book(market, Side.SELL, 'abc'), [(2, 105, 130)])

    def test_auction_with_remaining_market_orders(self):
        market = Market()
        market.place(Order(Side.SELL, 'abc', 40, 130, time=0))
        market.place(Order(Side.SELL, 'abc', 80, 130, time=0))
        market.place(Order(Side.SELL, 'abc', 10, 120, time=0))
        market.place(Order(Side.SELL, 'abc', 20, 120, time=0))
        market.place(Order(Side.SELL, 'abc', 60, None, time=0))
        market.place(Order(Side.BUY, 'abc', 45, 110, time=0))

        self.assertEqual(self.get_order_book(market, Side.BUY, 'abc'), [(1, 45, 110)])
        self.assertEqual(self.get_order_book(market, Side.SELL, 'abc'), [(1, 60, None), (2, 30, 120), (2, 120, 130)])

        self.assertEqual(self.format_executions(market.execute()), [(45, 110)])
        self.assertEqual(market['abc'].last_price, 110)
        self.assertIsNone(market['abc'].bid_price)
        self.assertEqual(market['abc'].ask_price, 120)

        self.assertEqual(self.get_order_book(market, Side.BUY, 'abc'), [])
        self.assertEqual(self.get_order_book(market, Side.SELL, 'abc'), [(1, 15, None), (2, 30, 120), (2, 120, 130)])

    def test_auction_cannot_execute_market_orders_only(self):
        market = Market()
        market.place(Order(Side.SELL, 'abc', 10, None, time=0))
        market.place(Order(Side.BUY, 'abc', 10, None, time=0))
        self.assertEqual(market.execute(), [])

    def test_auction_cannot_execute_spread_limit_orders(self):
        market = Market()
        market.place(Order(Side.SELL, 'abc', 10, 130, time=0))
        market.place(Order(Side.BUY, 'abc', 10, 110, time=0))
        market.place(Order(Side.SELL, 'abc', 10, None, time=0))
        market.place(Order(Side.BUY, 'abc', 10, None, time=0))
        self.assertEqual(market.execute(), [])

    def test_auction_cannot_execute_insufficient_bid_limit_order(self):
        market = Market()
        market.place(Order(Side.SELL, 'abc', 10, 130, time=0))
        market.place(Order(Side.SELL, 'abc', 15, None, time=0))
        market.place(Order(Side.BUY, 'abc', 10, None, time=0))
        self.assertEqual(market.execute(), [])

    def test_auction_cannot_execute_insufficient_ask_limit_order(self):
        market = Market()
        market.place(Order(Side.BUY, 'abc', 10, 110, time=0))
        market.place(Order(Side.SELL, 'abc', 10, None, time=0))
        market.place(Order(Side.BUY, 'abc', 15, None, time=0))
        self.assertEqual(market.execute(), [])

    def test_cancel(self):
        market = Market()
        order1 = Order(Side.BUY, 'abc', 10, 120)
        order2 = Order(Side.BUY, 'abc', 10, 110)
        market.place(order1)
        market.place(order2)
        market.cancel(order1)
        market.place(Order(Side.SELL, 'abc', 10))
        self.assertEqual(self.format_executions(market.execute()), [(10, 110)])

    def test_cancel_by_id(self):
        market = Market()
        order1 = Order(Side.BUY, 'abc', 10, 120, id='order1')
        order2 = Order(Side.BUY, 'abc', 10, 110, id='order2')
        market.place(order1)
        market.place(order2)
        market.cancel(Order(id='order1'))
        market.place(Order(Side.SELL, 'abc', 10))
        self.assertEqual(self.format_executions(market.execute()), [(10, 110)])

    def test_execute(self):
        market = Market()
        order1 = Order(Side.BUY, 'abc', 10, 120, time=1, id='order1')
        order2 = Order(Side.SELL, 'abc', 20, None, time=2, id='order2')
        self.assertEqual(market.execute(order1), [])
        executions = market.execute(order2)
        self.assertEqual(self.format_executions(executions), [(10, 120)])
        fill1 = executions[0].fills[Side.BUY]
        fill2 = executions[0].fills[Side.SELL]

        self.assertEqual(fill1.order, order1)
        self.assertEqual(fill1.quantity, 10)
        self.assertEqual(fill1.price, 120)
        self.assertEqual(fill1.side, Side.BUY)
        self.assertEqual(fill1.symbol, 'abc')
        self.assertEqual(fill1.order_quantity, 10)
        self.assertEqual(fill1.order_price, 120)
        self.assertEqual(fill1.order_time, 1)
        self.assertEqual(fill1.order_id, 'order1')
        self.assertEqual(fill1.cumulative_quantity, 10)

        self.assertEqual(fill2.order, order2)
        self.assertEqual(fill2.quantity, 10)
        self.assertEqual(fill2.price, 120)
        self.assertEqual(fill2.side, Side.SELL)
        self.assertEqual(fill2.symbol, 'abc')
        self.assertEqual(fill2.order_quantity, 20)
        self.assertEqual(fill2.order_price, None)
        self.assertEqual(fill2.order_time, 2)
        self.assertEqual(fill2.order_id, 'order2')
        self.assertEqual(fill2.cumulative_quantity, 10)

    def test_execute_after_cancel(self):
        market = Market()
        order = Order(Side.BUY, 'abc', 100, 110)
        market.place(order)
        market.cancel(order)
        self.assertEqual(market.execute(), [])

    def test_market_shortcuts(self):
        market = Market()

        market.place_order('buy', 'abc', 10, 110, id='order1')
        self.assertEqual(market.entries['order1'].state, State.NEW)

        market.cancel_order(id='order1')
        self.assertEqual(market.entries['order1'].state, State.CANCELLED)

        market.execute_order('buy', 'abc', 10, 120, id='order2')
        market.execute_order('sell', 'abc', 20, 120, id='order3')
        self.assertEqual(market.entries['order2'].state, State.FULLY_FILLED)
        self.assertEqual(market.entries['order3'].state, State.PARTIALLY_FILLED)

    def test_product_shortcuts(self):
        market = Market()
        product = market.ensure_product('abc')

        product.place_order('buy', 'abc', 10, 110, id='order1')
        self.assertEqual(product.entries['order1'].state, State.NEW)

        product.cancel_order(id='order1')
        self.assertEqual(product.entries['order1'].state, State.CANCELLED)

        product.execute_order('buy', 'abc', 10, 120, id='order2')
        product.execute_order('sell', 'abc', 20, 120, id='order3')
        self.assertEqual(product.entries['order2'].state, State.FULLY_FILLED)
        self.assertEqual(product.entries['order3'].state, State.PARTIALLY_FILLED)

    def test_order_queue_stats(self):
        market = Market()

        sell1 = Order(Side.SELL, 'abc', 10, 130, id='sell1')
        sell2 = Order(Side.SELL, 'abc', 10, 120, id='sell2')
        sell3 = Order(Side.SELL, 'abc', 10, 110, id='sell3')
        sell4 = Order(Side.SELL, 'abc', 10, None, id='sell4')

        buy1 = Order(Side.BUY, 'abc', 10, 110, id='buy1')
        buy2 = Order(Side.BUY, 'abc', 10, 100, id='buy2')
        buy3 = Order(Side.BUY, 'abc', 10, 90, id='buy3')
        buy4 = Order(Side.BUY, 'abc', 10, None, id='buy4')

        for order in (sell1, sell2, sell3, sell4, buy1, buy2, buy3, buy4):
            market.place(order)

        self.assertEqual(self.format_queue_stats(market['abc'][Side.BUY]), [4, 40, 1, 10, 3, 30])
        self.assertEqual(self.format_queue_stats(market['abc'][Side.SELL]), [4, 40, 1, 10, 3, 30])

        market.execute()
        self.assertEqual(self.format_queue_stats(market['abc'][Side.BUY]), [2, 20, 0, 0, 2, 20])
        self.assertEqual(self.format_queue_stats(market['abc'][Side.SELL]), [2, 20, 0, 0, 2, 20])

        market.cancel(buy3)
        self.assertEqual(self.format_queue_stats(market['abc'][Side.BUY]), [1, 10, 0, 0, 1, 10])
        self.assertEqual(self.format_queue_stats(market['abc'][Side.SELL]), [2, 20, 0, 0, 2, 20])

        market.cancel(sell1)
        self.assertEqual(self.format_queue_stats(market['abc'][Side.BUY]), [1, 10, 0, 0, 1, 10])
        self.assertEqual(self.format_queue_stats(market['abc'][Side.SELL]), [1, 10, 0, 0, 1, 10])

    def test_order_queue_internal(self):
        market = Market()

        sell1 = Order(Side.SELL, 'abc', 10, 130, time=1, id='sell1') # filled
        sell2 = Order(Side.SELL, 'abc', 10, 120, time=2, id='sell2') # top of price & time queues
        sell3 = Order(Side.SELL, 'abc', 10, 120, time=3, id='sell3') # top of price queue
        sell4 = Order(Side.SELL, 'abc', 10, 110, time=4, id='sell4')
        sell5 = Order(Side.SELL, 'abc', 10, None, time=5, id='sell5') # filled

        buy1 = Order(Side.BUY, 'abc', 10, 110, time=6, id='buy1') # filled
        buy2 = Order(Side.BUY, 'abc', 10, 100, time=7, id='buy2') # top of price & time queue
        buy3 = Order(Side.BUY, 'abc', 10, 100, time=8, id='buy3') # top of price queue
        buy4 = Order(Side.BUY, 'abc', 10, 90, time=9, id='buy4')
        buy5 = Order(Side.BUY, 'abc', 10, None, time=10, id='buy5') # filled

        for order in (sell1, sell2, sell3, sell4, sell5, buy1, buy2, buy3, buy4, buy5):
            market.place(order)

        market.execute()

        buy_order_queue = market['abc'][Side.BUY]
        sell_order_queue = market['abc'][Side.SELL]
        self.assertEqual(buy_order_queue.next_price, 100)
        self.assertEqual(sell_order_queue.next_price, 120)

        buy_price_queue = buy_order_queue.heap.peek_value()
        sell_price_queue = sell_order_queue.heap.peek_value()
        self.assertEqual(buy_price_queue.price, 100)
        self.assertEqual(buy_price_queue.count, 2)
        self.assertEqual(buy_price_queue.volume, 20)
        self.assertEqual(sell_price_queue.price, 120)
        self.assertEqual(sell_price_queue.count, 2)
        self.assertEqual(sell_price_queue.volume, 20)

        buy_time_queue = buy_price_queue.heap.peek_value()
        sell_time_queue = sell_price_queue.heap.peek_value()
        self.assertEqual(buy_time_queue.time, 7)
        self.assertEqual(buy_time_queue.count, 1)
        self.assertEqual(buy_time_queue.volume, 10)
        self.assertEqual(sell_time_queue.time, 2)
        self.assertEqual(sell_time_queue.count, 1)
        self.assertEqual(sell_time_queue.volume, 10)

    def test_order_persistence(self):
        market = Market()
        self.assertIs(market.get_order_by_id('order1'), None)
        self.assertIs(market.get_order_by_id('order2'), None)
        self.assertIs(market['abc'].get_order_by_id('order1'), None)
        self.assertIs(market['abc'].get_order_by_id('order2'), None)

        order1 = Order(Side.BUY, 'abc', 10, 90, id='order1')
        market.place(order1)
        self.assertIs(market.get_order_by_id('order1'), order1)
        self.assertIs(market.get_order_by_id('order2'), None)
        self.assertIs(market['abc'].get_order_by_id('order1'), order1)
        self.assertIs(market['abc'].get_order_by_id('order2'), None)

        order2 = Order(Side.SELL, 'abc', 20, None, id='order2')
        market.execute(order2)
        self.assertIs(market.get_order_by_id('order1'), order1)
        self.assertIs(market.get_order_by_id('order2'), order2)
        self.assertIs(market['abc'].get_order_by_id('order1'), order1)
        self.assertIs(market['abc'].get_order_by_id('order2'), order2)

        market.cancel(order2)
        self.assertIs(market.get_order_by_id('order1'), order1)
        self.assertIs(market.get_order_by_id('order2'), order2)
        self.assertIs(market['abc'].get_order_by_id('order1'), order1)
        self.assertIs(market['abc'].get_order_by_id('order2'), order2)

if __name__ == '__main__':
    unittest.main()
