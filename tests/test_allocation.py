from marketsim import Order, OrderEntry, Side, TimeOrderQueue
import unittest

class TestAllocation(unittest.TestCase):
    def allocate(self, queue, sum_quantity):
        allocations = queue.allocate(sum_quantity)
        return [(alloc.quantity, alloc.entry.remaining, alloc.entry.quantity) for alloc in allocations]

    def test_allocation(self):
        bid_queue = TimeOrderQueue(None)
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 10, 120)))
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 20, 120)))
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 30, 120)))

        self.assertEqual(self.allocate(bid_queue, 18), [(3, 10, 10), (6, 20, 20), (9, 30, 30)])

        ask_queue = TimeOrderQueue(None)
        ask_queue.push(OrderEntry(Order(Side.SELL, 'abc', 18, None)))
        bid_queue.execute(ask_queue)

        TimeOrderQueue.DEBUG = True
        self.assertEqual(self.allocate(bid_queue, 35), [(6, 7, 10), (12, 14, 20), (17, 21, 30)])
        TimeOrderQueue.DEBUG = False

    def test_adjust_allocation(self):
        bid_queue = TimeOrderQueue(None)
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 11, 120)))
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 13, 120)))
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 17, 120)))
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 19, 120)))
        bid_queue.push(OrderEntry(Order(Side.BUY, 'abc', 23, 120)))
        # 11 + 13 + 17 + 19 + 23 == 83
        # 11 / 83 == 0.13
        # 13 / 83 == 0.15
        # 17 / 83 == 0.20
        # 19 / 83 == 0.22
        # 23 / 83 == 0.27

        # Allocate 41
        # [5.43, 6.42, 8.39, 9.38, 11.36]
        # [5, 6, 8, 9, 11] #=> sum == 39
        # [5+1, 6+1, 8, 9, 11]
        self.assertEqual(self.allocate(bid_queue, 41), [(6, 11, 11), (7, 13, 13), (8, 17, 17), (9, 19, 19), (11, 23, 23)])

        # Allocate 42
        # [5.56, 6.57, 8.60, 9.61, 11.63]
        # [6, 7, 9, 10, 12] #=> sum == 44
        # [6, 7, 9, 10-1, 12-1]
        self.assertEqual(self.allocate(bid_queue, 42), [(6, 11, 11), (7, 13, 13), (9, 17, 17), (9, 19, 19), (11, 23, 23)])

if __name__ == '__main__':
    unittest.main()
