from heapq import heappush, heappop

class KeyedHeap:
    def __init__(self):
        self.pq_map = {}
        self.pq_list = []

    def __contains__(self, key):
        return key in self.pq_map

    def __getitem__(self, key):
        return self.pq_map[key]

    def __len__(self):
        return len(self.pq_list)

    def __bool__(self):
        return len(self.pq_list) != 0

    def __nonzero__(self):
        return len(self.pq_list) != 0

    def empty(self):
        return len(self.pq_list) == 0

    def push(self, key, value):
        if key in self:
            raise KeyError('key already exists: {}'.format(key))
        self.pq_map[key] = value
        heappush(self.pq_list, (key, value))

    def pop(self):
        if self.empty():
            raise IndexError('pop from an empty queue')
        key, value = heappop(self.pq_list)
        del self.pq_map[key]
        return (key, value)

    def pop_key(self):
        key, _ = self.pop()
        return key

    def pop_value(self):
        _, value = self.pop()
        return value

    def peek(self):
        if self.empty():
            raise IndexError('peek from an empty queue')
        key, value = self.pq_list[0]
        return (key, value)

    def peek_key(self):
        key, _ = self.peek()
        return key

    def peek_value(self):
        _, value = self.peek()
        return value

    def items(self):
        pq_list = list(self.pq_list)
        while len(pq_list) > 0:
            key, value = heappop(pq_list)
            yield key, value

    def keys(self):
        for key, _ in self.items():
            yield key

    def values(self):
        for _, value in self.items():
            yield value
