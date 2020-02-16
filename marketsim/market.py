from collections import deque
from datetime import datetime
from enum import Enum
from time import mktime
from marketsim.keyed_heap import KeyedHeap

builtin_id = id

class Side(Enum):
    BUY  = 1
    SELL = 2

    @classmethod
    def normalize(cls, value):
        if value is None:
            return None
        elif isinstance(value, cls):
            return value
        elif isinstance(value, str):
            return cls[value.upper()]
        elif isinstance(value, int):
            return cls(value)
        else:
            raise ValueError('invalid side: {}'.format(value))

class State(Enum):
    NEW              = 0
    PARTIALLY_FILLED = 1
    FULLY_FILLED     = 2
    CANCELLED        = 3

class Order:
    def __init__(self, side=None, symbol=None, quantity=None, price=None, time=None, id=None):
        self._side = Side.normalize(side)
        self._symbol = symbol
        self._quantity = quantity
        self._price = price
        self._time = time
        self._id = id if id is not None else builtin_id(self)

    @property
    def side(self):
        return self._side

    @property
    def symbol(self):
        return self._symbol

    @property
    def quantity(self):
        return self._quantity

    @property
    def price(self):
        return self._price

    @property
    def time(self):
        return self._time

    @property
    def id(self):
        return self._id

    def __repr__(self):
        return 'Order(side={}, symbol={}, quantity={}, price={})'.format(self.side, self.symbol, self.quantity, self.price)

class Fill:
    def __init__(self, entry, quantity, price=None):
        self._order = entry.order
        self._quantity = quantity
        self._price = price if price is not None else entry.price

        self._side = entry.side
        self._symbol = entry.symbol
        self._order_quantity = entry.quantity
        self._order_price = entry.price
        self._order_time = entry.time
        self._order_id = entry.order_id
        self._cumulative_quantity = entry.filled_quantity

    @property
    def order(self):
        return self._order

    @property
    def quantity(self):
        return self._quantity

    @property
    def price(self):
        return self._price

    @property
    def side(self):
        return self._side

    @property
    def symbol(self):
        return self._symbol

    @property
    def order_quantity(self):
        return self._order_quantity

    @property
    def order_price(self):
        return self._order_price

    @property
    def order_time(self):
        return self._order_time

    @property
    def order_id(self):
        return self._order_id

    @property
    def cumulative_quantity(self):
        return self._cumulative_quantity

    def __repr__(self):
        return "Fill(side={}, symbol={}, quantity={}, price={}, cumulative_quantity={})".format(self.side, self.symbol, self.quantity, self.price, self.cumulative_quantity)

class Execution:
    def __init__(self, bid_entry, ask_entry, quantity, price=None):
        self._quantity = quantity
        self._price = price

        self._fills = {
            Side.BUY : Fill(bid_entry, quantity, price),
            Side.SELL: Fill(ask_entry, quantity, price),
        }

    @property
    def quantity(self):
        return self._quantity

    @property
    def price(self):
        return self._price

    @property
    def fills(self):
        return self._fills

    @property
    def bid_fill(self):
        return self.fills[Side.BUY]

    @property
    def ask_fill(self):
        return self.fills[Side.SELL]

    def __repr__(self):
        return "Execution(bid_fill={}, ask_fill={}, quantity={}, price={})".format(self.bid_fill, self.ask_fill, self.quantity, self.price)

class OrderEntry:
    def __init__(self, order):
        self._order = order

        self._side = order.side
        self._symbol = order.symbol
        self._quantity = order.quantity
        self._price = order.price
        self._time = order.time if order.time is not None else self.default_time()
        self._order_id = order.id

        self._remaining = order.quantity
        self._state = State.NEW

    @property
    def order(self):
        return self._order

    @property
    def side(self):
        return self._side

    @property
    def symbol(self):
        return self._symbol

    @property
    def quantity(self):
        return self._quantity

    @property
    def price(self):
        return self._price

    @property
    def time(self):
        return self._time

    @property
    def order_id(self):
        return self._order_id

    @property
    def remaining(self):
        return self._remaining

    @property
    def state(self):
        return self._state

    @property
    def filled_quantity(self):
        return self.quantity - self.remaining

    def default_time(self):
        now = datetime.now()
        return mktime(now.timetuple()) + now.microsecond / 1000000.0

    def cancel(self):
        self._remaining = 0
        self._state = State.CANCELLED

    def execute(self, ask_entry, quantity=None):
        bid_entry = self

        if quantity is None:
            quantity = min(bid_entry.remaining, ask_entry.remaining)

        bid_entry._remaining -= quantity
        ask_entry._remaining -= quantity

        bid_entry._state = State.FULLY_FILLED if bid_entry.remaining == 0 else State.PARTIALLY_FILLED
        ask_entry._state = State.FULLY_FILLED if ask_entry.remaining == 0 else State.PARTIALLY_FILLED

        return Execution(bid_entry, ask_entry, quantity)

class OrderStat:
    def __init__(self, price, volume, count):
        self._price  = price
        self._volume = volume
        self._count  = count

    @property
    def price(self):
        return self._price

    @property
    def volume(self):
        return self._volume

    @property
    def count(self):
        return self._count

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return 'OrderStat(price={}, volume={}, count={})'.format(self.price, self.volume, self.count)

class Allocation:
    def __init__(self, entry, quantity):
        self._entry = entry
        self._quantity = quantity

    @property
    def entry(self):
        return self._entry

    @property
    def quantity(self):
        return self._quantity

    def __repr__(self):
        return 'Allocation(entry={}, quantity={})'.format(self.entry, self.quantity)

    @property
    def pair(self):
        return (self.entry, self.quantity)

class TimeOrderQueue:
    def __init__(self, time):
        self._time = time
        self._volume = 0
        self._entries = deque()

    @property
    def time(self):
        return self._time

    @property
    def volume(self):
        return self._volume

    @property
    def entries(self):
        return self._entries

    @property
    def count(self):
        return len(self.entries)

    def empty(self):
        return len(self.entries) == 0

    def push(self, entry):
        self._volume += entry.remaining
        self.entries.append(entry)
        return self

    def cancel(self, entry):
        self._volume -= entry.remaining
        entry.cancel()
        return self

    def execute(self, ask_queue):
        bid_queue = self

        sum_quantity = min(bid_queue.volume, ask_queue.volume)

        if sum_quantity == 0:
            return []

        bid_allocations = bid_queue.allocate(sum_quantity)
        ask_allocations = ask_queue.allocate(sum_quantity)

        executions = []
        b = 0
        a = 0
        bid_entry, bid_quantity = bid_allocations[0].pair
        ask_entry, ask_quantity = ask_allocations[0].pair

        while b < len(bid_allocations) and a < len(ask_allocations):
            quantity = min(bid_quantity, ask_quantity)
            execution = bid_entry.execute(ask_entry, quantity)
            executions.append(execution)

            bid_queue._volume -= execution.quantity
            ask_queue._volume -= execution.quantity
            bid_quantity -= execution.quantity
            ask_quantity -= execution.quantity

            if bid_quantity == 0:
                b += 1
                if b < len(bid_allocations):
                    bid_entry, bid_quantity = bid_allocations[b].pair
            if ask_quantity == 0:
                a += 1
                if a < len(ask_allocations):
                    ask_entry, ask_quantity = ask_allocations[a].pair

        return executions

    def allocate(self, sum_quantity):
        unit = float(sum_quantity) / self.volume
        remaining_entries = filter(lambda entry: entry.remaining > 0, self.entries)
        allocations = [Allocation(entry, round(entry.remaining * unit)) for entry in remaining_entries]

        current_sum = sum([allocation.quantity for allocation in allocations])

        while current_sum != sum_quantity:
            if current_sum < sum_quantity:
                incr = 1
                alloc_iter = iter(allocations)
            else:
                incr = -1
                alloc_iter = reversed(allocations)

            while current_sum != sum_quantity:
                allocation = next(alloc_iter)
                allocation._quantity += incr
                current_sum += incr

        return allocations

class PriceOrderQueue:
    def __init__(self, price):
        self._heap = KeyedHeap()
        self._price = price
        self._count = 0
        self._volume = 0

    @property
    def heap(self):
        return self._heap

    @property
    def price(self):
        return self._price

    @property
    def count(self):
        return self._count

    @property
    def volume(self):
        return self._volume

    def empty(self):
        return self.heap.empty()

    def get_time_key(self, entry):
        return entry.time

    def push(self, entry):
        time = entry.time
        time_key = self.get_time_key(entry)

        if time_key in self.heap:
            child = self.heap[time_key]
        else:
            child = TimeOrderQueue(time)
            self.heap.push(time_key, child)

        child.push(entry)
        self._count += 1
        self._volume += entry.remaining

        return self

    def cancel(self, entry):
        time_key = self.get_time_key(entry)
        assert time_key in self.heap, 'order entry does not exist for time_key: {}'.format(time_key)

        # Note: Update volume before child.cancel(entry). Otherwise, entry.remaining would already be zero.
        self._count -= 1
        self._volume -= entry.remaining
        child = self.heap[time_key]
        child.cancel(entry)

        return self

    def pop_empty_values(self):
        while not self.heap.empty():
            if self.heap.peek_value().empty() or self.heap.peek_value().volume == 0:
                self.heap.pop()
            else:
                break

    def execute(self, ask_queue):
        bid_queue = self

        executions = []

        while not bid_queue.heap.empty() and not ask_queue.heap.empty():
            bid_child = bid_queue.heap.peek_value()
            ask_child = ask_queue.heap.peek_value()

            bid_orig_count = bid_child.count
            ask_orig_count = ask_child.count

            child_executions = bid_child.execute(ask_child)

            bid_queue._count -= bid_orig_count - bid_child.count
            ask_queue._count -= ask_orig_count - ask_child.count

            bid_queue.pop_empty_values()
            ask_queue.pop_empty_values()

            for execution in child_executions:
                bid_queue._volume -= execution.quantity
                ask_queue._volume -= execution.quantity

            executions.extend(child_executions)

        return executions

class OrderQueue:
    def __init__(self):
        self._heap = KeyedHeap()
        self._count = 0
        self._volume = 0
        self._market_order_count = 0
        self._market_order_volume = 0
        self._limit_order_count = 0
        self._limit_order_volume = 0
        self._next_price = None

    @property
    def heap(self):
        return self._heap

    @property
    def count(self):
        return self._count

    @property
    def volume(self):
        return self._volume

    @property
    def market_order_count(self):
        return self._market_order_count

    @property
    def market_order_volume(self):
        return self._market_order_volume

    @property
    def limit_order_count(self):
        return self._limit_order_count

    @property
    def limit_order_volume(self):
        return self._limit_order_volume

    @property
    def next_price(self):
        return self._next_price

    def update_stats(self, delta_count, delta_quantity, is_market_order):
        self._count += delta_count
        self._volume += delta_quantity
        if is_market_order:
            self._market_order_count += delta_count
            self._market_order_volume += delta_quantity
        else:
            self._limit_order_count += delta_count
            self._limit_order_volume += delta_quantity

    def update_next_price(self):
        if self.heap.empty():
            self._next_price = None
        elif self.heap.peek_value().price is not None:
            self._next_price = self.heap.peek_value().price
        else:
            # Put aside market order temporarily to find the next limit price
            key, child = self.heap.pop()
            if self.heap.empty():
                self._next_price = None
            else:
                self._next_price = self.heap.peek_value().price
            self.heap.push(key, child)

    def get_price_key(self, entry):
        price = entry.price
        side = entry.side

        if price is None:
            price_key = float('-inf')
        elif side == Side.BUY:
            price_key = -price
        else:
            price_key = price

        return price_key

    def pop_empty_values(self):
        while not self.heap.empty():
            if self.heap.peek_value().empty() or self.heap.peek_value().volume == 0:
                self.heap.pop()
            else:
                break

    def push(self, entry):
        price = entry.price
        price_key = self.get_price_key(entry)

        if price_key in self.heap:
            child = self.heap[price_key]
        else:
            child = PriceOrderQueue(price)
            self.heap.push(price_key, child)

        child.push(entry)
        self.update_stats(+1, entry.remaining, entry.price is None)
        self.update_next_price()

        return self

    def cancel(self, entry):
        price_key = self.get_price_key(entry)
        assert price_key in self.heap, 'order entry does not exist for price_key: {}'.format(price_key)

        # Note: Update stats before child.cancel(entry). Otherwise, entry.remaining would already be zero.
        self.update_stats(-1, -entry.remaining, entry.price is None)
        self.update_next_price()
        child = self.heap[price_key]
        child.cancel(entry)

        return self

    def can_execute(self, ask_queue):
        """
        In order for a product to be executable, certain conditions must be
        satisfied to be able to determine the execution price, depending on the
        currently queued orders.

        For example, the execution price cannot be determined solely by market-
        orders from both bid and ask sides, without limit-orders somehow
        involved.

        Case 1: Equal market-order volume on both bid and ask sides:
            There must be limit-orders on both sides. In addition, the limit-
            orders must include executable prices that cross each other.

        Case 2: There are more market-orders on bid side:
            After all market-orders on ask side are executed, there must be some
            limit-orders on ask side, in order to execute the remaining market-
            orders on bid side.

        Case 3: There are more market-orders on ask side:
            Same as above, but in the opposite way.
        """
        bid_queue = self

        if bid_queue.market_order_volume == ask_queue.market_order_volume:
            if bid_queue.limit_order_volume == 0 or ask_queue.limit_order_volume == 0:
                return False
            elif bid_queue.next_price < ask_queue.next_price:
                return False
        elif bid_queue.market_order_volume < ask_queue.market_order_volume:
            if bid_queue.limit_order_volume == 0:
                return False
        else:
            if ask_queue.limit_order_volume == 0:
                return False

        return True

    def execute(self, ask_queue):
        bid_queue = self

        if not bid_queue.can_execute(ask_queue):
            return []

        executions = []

        while not bid_queue.heap.empty() and not ask_queue.heap.empty():
            bid_child = bid_queue.heap.peek_value()
            ask_child = ask_queue.heap.peek_value()

            if bid_child.price is not None and ask_child.price is not None:
                if bid_child.price < ask_child.price:
                    break

            child_executions = bid_child.execute(ask_child)

            bid_queue.pop_empty_values()
            ask_queue.pop_empty_values()

            executions.extend(child_executions)

        assert executions, 'there were no executions. may be a bug in can_execute()'

        bid_price = executions[-1].bid_fill.price
        ask_price = executions[-1].ask_fill.price

        if bid_price is None:
            price = ask_price
        elif ask_price is None:
            price = bid_price
        else:
            price = (bid_price + ask_price) / 2

        assert price is not None

        for execution in executions:
            bid_delta = -1 if execution.bid_fill.cumulative_quantity == execution.bid_fill.order_quantity else 0
            ask_delta = -1 if execution.ask_fill.cumulative_quantity == execution.ask_fill.order_quantity else 0
            bid_queue.update_stats(bid_delta, -execution.quantity, execution.bid_fill.price is None)
            ask_queue.update_stats(ask_delta, -execution.quantity, execution.ask_fill.price is None)
            execution._price = price
            execution.bid_fill._price = price
            execution.ask_fill._price = price

        bid_queue.update_next_price()
        ask_queue.update_next_price()

        return executions

    def get_order_book(self):
        order_book = []
        for child in self.heap.values():
            if child.volume > 0:
                order_book.append(OrderStat(child.price, child.volume, child.count))
        return order_book

class Product:
    def __init__(self, symbol):
        self._symbol = symbol

        self._order_queues = {
            Side.BUY : OrderQueue(),
            Side.SELL: OrderQueue(),
        }

        self._entries = {}
        self._last_price = None

    @property
    def symbol(self):
        return self._symbol

    @property
    def order_queues(self):
        return self._order_queues

    @property
    def entries(self):
        return self._entries

    @property
    def bid_price(self):
        return self.order_queues[Side.BUY].next_price

    @property
    def ask_price(self):
        return self.order_queues[Side.SELL].next_price

    @property
    def last_price(self):
        return self._last_price

    @last_price.setter
    def last_price(self, last_price):
        self._last_price = last_price

    def __lt__(self, other):
        return self.symbol < other.symbol

    def __getitem__(self, side):
        side = Side.normalize(side)
        return self.order_queues[side]

    def place(self, order):
        if order.id in self.entries:
            raise ValueError('duplicate order id')

        entry = OrderEntry(order)
        self.order_queues[order.side].push(entry)
        self.entries[order.id] = entry

    def cancel(self, order):
        if order.id not in self.entries:
            raise ValueError('no such order id')

        # Note: Update volume before queue.cancel(entry). Otherwise, entry.remaining would already be zero.
        entry = self.entries[order.id]

        if entry.state == State.FULLY_FILLED:
            raise ValueError('already fully filled')
        if entry.state == State.CANCELLED:
            raise ValueError('already cancelled')

        self.order_queues[entry.side].cancel(entry)

    def execute(self, order=None):
        if order is not None:
            self.place(order)

        bid_order_queue = self.order_queues[Side.BUY]
        ask_order_queue = self.order_queues[Side.SELL]

        executions = bid_order_queue.execute(ask_order_queue)

        if executions:
            self._last_price = executions[-1].price

        return executions

    def place_order(self, *args, **kwargs):
        return self.place(Order(*args, **kwargs))

    def cancel_order(self, *args, **kwargs):
        return self.cancel(Order(*args, **kwargs))

    def execute_order(self, *args, **kwargs):
        return self.execute(Order(*args, **kwargs))

    def get_order_by_id(self, order_id):
        if order_id not in self.entries:
            return None
        entry = self.entries[order_id]
        return entry.order

    def format_order_book(self):
        bid_order_book = self.order_queues[Side.BUY].get_order_book()
        ask_order_book = self.order_queues[Side.SELL].get_order_book()

        entries = {}

        for side, order_book in [(Side.BUY, bid_order_book), (Side.SELL, ask_order_book)]:
            for entry in order_book:
                if entry.price not in entries:
                    entries[entry.price] = {}
                entries[entry.price][side] = entry

        rows = []
        rows.append(['BID', 'PRICE', 'ASK'])
        rows.append(['===', '=====', '==='])

        for price in reversed(sorted(list(entries.keys()))):
            values = {Side.BUY: '', Side.SELL: ''}
            for side in [Side.BUY, Side.SELL]:
                if side in entries[price]:
                    entry = entries[price][side]
                    values[side] = '{} ({})'.format(entry.volume, entry.count)
            rows.append([values[Side.BUY], str(price), values[Side.SELL]])

        max_len = [max(len(row[i]) for row in rows) for i in range(3)]

        result = []

        for row in rows:
            values = [('{:' + str(max_len[i]) + '}').format(row[i]) for i in range(3)]
            result.append('| ' + ' | '.join(values) + ' |')

        result[1] = '|' + '|'.join(['=' * (max_len[i] + 2) for i in range(3)]) + '|'

        return "\n".join(result)

class Market:
    def __init__(self):
        self._products = {}
        self._entries = {}

    @property
    def products(self):
        return self._products

    @property
    def entries(self):
        return self._entries

    def __contains__(self, symbol):
        return symbol in self.products

    def __setitem__(self, symbol, product):
        if symbol is None:
            raise KeyError('symbol must be specified')
        if product is None:
            product = Product(symbol)
        self.products[symbol] = product
        return product

    def __getitem__(self, symbol):
        if not self.has_product(symbol):
            self[symbol] = None
        return self.products[symbol]

    def __iter__(self):
        return iter(self.products)

    def get_products(self):
        return self.products.values()

    def has_product(self, symbol):
        return symbol in self

    def get_product(self, symbol):
        return self[symbol]

    def set_product(self, symbol, product):
        self[symbol] = product
        return self[symbol]

    def ensure_product(self, symbol, product=None):
        if symbol not in self:
            self.set_product(symbol, product)
        return self.get_product(symbol)

    def items(self):
        return self.products.items()

    def keys(self):
        return self.products.keys()

    def values(self):
        return self.products.values()

    def place(self, order):
        if order.id in self.entries:
            raise ValueError('duplicate order id')
        product = self.ensure_product(order.symbol)
        product.place(order)
        self.entries[order.id] = product.entries[order.id]

    def cancel(self, order):
        if order.id not in self.entries:
            raise ValueError('no such order id')
        entry = self.entries[order.id]
        product = self.ensure_product(entry.symbol)
        product.cancel(order)

    def execute(self, order=None):
        if order is not None:
            product = self.ensure_product(order.symbol)
            executions = product.execute(order)
            self.entries[order.id] = product.entries[order.id]
            return executions
        else:
            executions = []
            for symbol in self.products:
                executions.extend(self.products[symbol].execute())
            return executions

    def place_order(self, *args, **kwargs):
        return self.place(Order(*args, **kwargs))

    def cancel_order(self, *args, **kwargs):
        return self.cancel(Order(*args, **kwargs))

    def execute_order(self, *args, **kwargs):
        return self.execute(Order(*args, **kwargs))

    def get_order_by_id(self, order_id):
        if order_id not in self.entries:
            return None
        entry = self.entries[order_id]
        return entry.order
