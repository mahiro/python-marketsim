from marketsim import Market, Order, Side, Fill, Execution, Allocation, OrderEntry
import unittest

class TestOrder(unittest.TestCase):
    def test_side_enum(self):
        self.assertEqual(str(Side.BUY), 'Side.BUY')
        self.assertEqual(str(Side.SELL), 'Side.SELL')
        self.assertEqual(repr(Side.BUY), '<Side.BUY: 1>')
        self.assertEqual(repr(Side.SELL), '<Side.SELL: 2>')

        self.assertEqual(Side.normalize(None), None)
        self.assertEqual(Side.normalize(1), Side.BUY)
        self.assertEqual(Side.normalize(2), Side.SELL)
        self.assertEqual(Side.normalize('BUY'), Side.BUY)
        self.assertEqual(Side.normalize('SELL'), Side.SELL)
        self.assertEqual(Side.normalize('buy'), Side.BUY)
        self.assertEqual(Side.normalize('sell'), Side.SELL)

        with self.assertRaises(KeyError):
            Side.normalize('UNKNOWN')

        with self.assertRaises(ValueError):
            Side.normalize(-1)

        with self.assertRaises(ValueError):
            Side.normalize(1.0)

    def test_objects(self):
        bid_order = Order(Side.BUY, 'abc', 10)
        ask_order = Order(Side.SELL, 'abc', 10)
        self.assertEqual(repr(bid_order), 'Order(side=Side.BUY, symbol=abc, quantity=10, price=None)')
        self.assertEqual(repr(ask_order), 'Order(side=Side.SELL, symbol=abc, quantity=10, price=None)')

        bid_entry = OrderEntry(bid_order)
        ask_entry = OrderEntry(ask_order)
        execution = Execution(bid_entry, ask_entry, 5, 100)
        bid_fill = Fill(bid_entry, 5, 100)
        ask_fill = Fill(ask_entry, 5, 100)
        self.assertEqual(repr(execution), 'Execution(bid_fill={}, ask_fill={}, quantity=5, price=100)'.format(bid_fill, ask_fill))

        allocation = Allocation(bid_order, 5)
        self.assertEqual(repr(allocation), 'Allocation(entry={}, quantity=5)'.format(bid_order))

    def test_equal_buy_sell(self):
        bid_entry = OrderEntry(Order(Side.BUY, 'abc', 10, 130))
        ask_entry = OrderEntry(Order(Side.SELL, 'abc', 10, 110))

        execution = bid_entry.execute(ask_entry)

        self.assertEqual(execution.price, None)
        self.assertEqual(execution.quantity, 10)

        self.assertEqual(bid_entry.quantity, 10)
        self.assertEqual(ask_entry.quantity, 10)
        self.assertEqual(bid_entry.remaining, 0)
        self.assertEqual(ask_entry.remaining, 0)
        self.assertEqual(bid_entry.filled_quantity, 10)
        self.assertEqual(ask_entry.filled_quantity, 10)

        self.assertIs(execution.bid_fill.order, bid_entry.order)
        self.assertIs(execution.ask_fill.order, ask_entry.order)

    def test_more_buy_than_sell(self):
        bid_entry = OrderEntry(Order(Side.BUY, 'abc', 10, 130))
        ask_entry = OrderEntry(Order(Side.SELL, 'abc', 15, 110))

        execution = bid_entry.execute(ask_entry)

        self.assertEqual(execution.price, None)
        self.assertEqual(execution.quantity, 10)

        self.assertEqual(bid_entry.quantity, 10)
        self.assertEqual(ask_entry.quantity, 15)
        self.assertEqual(bid_entry.remaining, 0)
        self.assertEqual(ask_entry.remaining, 5)
        self.assertEqual(bid_entry.filled_quantity, 10)
        self.assertEqual(ask_entry.filled_quantity, 10)

        self.assertIs(execution.bid_fill.order, bid_entry.order)
        self.assertIs(execution.ask_fill.order, ask_entry.order)

    def test_less_buy_than_sell(self):
        bid_entry = OrderEntry(Order(Side.BUY, 'abc', 15, 130))
        ask_entry = OrderEntry(Order(Side.SELL, 'abc', 10, 110))

        execution = bid_entry.execute(ask_entry)

        self.assertEqual(execution.price, None)
        self.assertEqual(execution.quantity, 10)

        self.assertEqual(bid_entry.quantity, 15)
        self.assertEqual(ask_entry.quantity, 10)
        self.assertEqual(bid_entry.remaining, 5)
        self.assertEqual(ask_entry.remaining, 0)
        self.assertEqual(bid_entry.filled_quantity, 10)
        self.assertEqual(ask_entry.filled_quantity, 10)

        self.assertIs(execution.bid_fill.order, bid_entry.order)
        self.assertIs(execution.ask_fill.order, ask_entry.order)

if __name__ == '__main__':
    unittest.main()
