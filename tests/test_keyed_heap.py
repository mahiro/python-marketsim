from marketsim import KeyedHeap
import unittest

class TestKeyedHeap(unittest.TestCase):
    def test_heap(self):
        heap = KeyedHeap()
        self.assertFalse('key1' in heap)
        self.assertEqual(len(heap), 0)

        heap.push('key1', 'value1')
        self.assertTrue('key1' in heap)
        self.assertEqual(heap['key1'], 'value1')
        self.assertEqual(len(heap), 1)

        key, value = heap.peek()
        self.assertTrue('key1' in heap)
        self.assertEqual(key, 'key1')
        self.assertEqual(value, 'value1')
        self.assertEqual(heap['key1'], 'value1')
        self.assertEqual(len(heap), 1)

        key, value = heap.pop()
        self.assertFalse('key1' in heap)
        self.assertEqual(key, 'key1')
        self.assertEqual(value, 'value1')
        self.assertEqual(len(heap), 0)

    def test_priority(self):
        heap = KeyedHeap()
        heap.push('key2', 'bar')
        heap.push('key1', 'foo')
        heap.push('key3', 'baz')

        for expected_key, expected_value in [('key1', 'foo'), ('key2', 'bar'), ('key3', 'baz')]:
            key, value = heap.peek()
            self.assertEqual(key, expected_key)
            self.assertEqual(value, expected_value)

            key, value = heap.peek()
            self.assertEqual(key, expected_key)
            self.assertEqual(value, expected_value)

            key, value = heap.pop()
            self.assertEqual(key, expected_key)
            self.assertEqual(value, expected_value)

    def test_bool(self):
        heap = KeyedHeap()
        self.assertFalse(heap)
        self.assertFalse(heap.__bool__())
        self.assertFalse(heap.__nonzero__())
        self.assertTrue(heap.empty())

        heap.push('key1', 'value1')
        self.assertTrue(heap)
        self.assertTrue(heap.__bool__())
        self.assertTrue(heap.__nonzero__())
        self.assertFalse(heap.empty())

        heap.pop()
        self.assertFalse(heap)
        self.assertFalse(heap.__bool__())
        self.assertFalse(heap.__nonzero__())
        self.assertTrue(heap.empty())

    def test_exception(self):
        heap = KeyedHeap()

        with self.assertRaises(IndexError) as context:
            heap.peek()
        with self.assertRaises(IndexError) as context:
            heap.pop()

        heap.push('key1', 'value1')

        with self.assertRaises(KeyError) as context:
            heap.push('key1', 'value2')

        heap.pop()

        with self.assertRaises(IndexError) as context:
            heap.peek()
        with self.assertRaises(IndexError) as context:
            heap.pop()

    def test_iterate(self):
        heap = KeyedHeap()

        heap.push('key2', 'bar')
        heap.push('key1', 'foo')
        heap.push('key3', 'baz')

        self.assertEqual(list(heap.items()), [('key1', 'foo'), ('key2', 'bar'), ('key3', 'baz')])
        self.assertEqual(list(heap.keys()), ['key1', 'key2', 'key3'])
        self.assertEqual(list(heap.values()), ['foo', 'bar', 'baz'])

    def test_key_value(self):
        heap = KeyedHeap()

        heap.push('key1', 'value1')
        self.assertEqual(heap.peek_key(), 'key1')
        self.assertEqual(heap.pop_key(), 'key1')

        heap.push('key2', 'value2')
        self.assertEqual(heap.peek_value(), 'value2')
        self.assertEqual(heap.pop_value(), 'value2')
