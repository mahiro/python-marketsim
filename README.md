# marketsim

This utility helps simulate a stock market.

* Market orders and limit orders
* Limit order books
* Continuous tradnig and auction

## Example: Continuous Trading

```
from marketsim import Market
market = Market()

market.execute_order('buy', 'symbol1', quantity=10, price=100)
    # places a limit order and attempts to execute it immediately
    # returns an empty array (no executions at this point)

market.execute_order('sell', 'symbol1', quantity=10, price=None)
    # places a market order and attempts to execute it immediately
    # returns a list of Execution object(s)
```

## Example: Auction

```
from marketsim import Market
market = Market()

market.place_order('buy', 'symbol1', quantity=10, price=100, time=0)
    # places a limit order without execution

market.place_order('sell', 'symbol1', quantity=10, price=None, time=0)
    # places a market order without execution

market.execute()
    # executes all trades at once
    # returns a list of Execution object(s)

# Note:
# A constant "time" value is specified to effectively disable time priority,
# which ensures all limit orders at the same price will be evenly filled.
```

## class Market

A Market object manages order books of multiple symbols.

```
from marketsim import Market, Product, Order, Side
market = Market()

# Place and execute orders (returns a list of Execution objects)
market.execute(Order(Side.BUY, 'symbol1', quantity=10, price=100))
market.execute_order(Side.BUY, 'symbol1', quantity=10, price=100)
market.execute_order('buy', 'symbol1', quantity=10, price=100)

# Place orders without execution
market.place(Order(Side.SELL, 'symbol1', quantity=10, price=100))
market.place_order(Side.SELL, 'symbol1', quantity=10, price=100)
market.place_order('sell', 'symbol1', quantity=10, price=100)

# Execute orders that have been placed (returns a list of Execution objects)
market.execute()

# Cancel order by object
order = Order(Side.BUY, 'symbol1', quantity=10, price=100)
market.place(order)
market.cancel(order)
    # Note: order ID is internally assigned as the Python object ID by default

# Cancel order by specific ID
market.place_order(Side.SELL, 'symbol1', quantity=10, price=100, id='order #1')
market.cancel_order(id='order #1')

# Retrieve information per symbol
market['symbol1'].bid_price
market['symbol1'].ask_price
market['symbol1'].last_price

# Retrieve Product objects from a market object
market = Market()
product = market.get_product('symbol1') # returns None
product = market.ensure_product('symbol1') # creates a new product if not existing
product = market.get_product('symbol1') # returns the object
product = market['symbol1'] # synonym for get_product()
market.set_product('symbol2', Product('symbol2'))
market.['symbol2'] = Product('symbol2')

# Get all products
market.get_products() # returns a list of Product objects

# Iterate all products
for product in market:
    pass

```

## class Product

A Product object represents an order book of a single symbol.

```
from marketsim import Market, Product, Order, Side

# Create a standalone product
product = Product('symbol1')

# Information per symbol
product.bid_price # initially None
product.ask_price # initially None
product.last_price # initially None

# Order book
product.format_order_book()

# Example output:
"""
| BID    | PRICE | ASK    |
|========|=======|========|
|        | 140   | 20 (2) |
|        | 130   | 20 (2) |
| 20 (2) | 110   |        |
| 20 (2) | 100   |        |
"""

# Order queues
product.order_queues[Side.BUY]
product.order_queues[Side.SELL]
product[Side.BUY] # synonym for product.order_queues[Side.BUY]
product[Side.SELL] # synonym for product.order_queues[Side.SELL]
```

## class Order, Side

An Order object can be used to place an order into a Market instance.

```
from marketsim import Order, Side

# Limit order
order = Order(Side.BUY, 'symbol1', quantity=10, price=100)

# Market order
order = Order(Side.BUY, 'symbol1', quantity=10)

# Order with ID (useful when cancelling an order)
order = Order(Side.BUY, 'symbol1', quantity=10, id='order #1')

# Order with time (useful to control price-time priority)
order = Order(Side.BUY, 'symbol1', quantity=10, time=12345)
    # Default: Unix timestamp in seconds with a fractional value in microseconds
    # Specify a constant value across all placed orders to simulate pro-rata.

# Side can be specified in alternative ways
order = Order(Side.BUY, 'symbol1', quantity=10)
order = Order('BUY', 'symbol1', quantity=10)
order = Order('Buy', 'symbol1', quantity=10)
order = Order('buy', 'symbol1', quantity=10)
order = Order(1, 'symbol1', quantity=10) # 1 means BUY, as in FIX tag 54

order = Order(Side.SELL, 'symbol1', quantity=10)
order = Order('SELL', 'symbol1', quantity=10)
order = Order('Sell', 'symbol1', quantity=10)
order = Order('sell', 'symbol1', quantity=10)
order = Order(2, 'symbol1', quantity=10) # 2 means SELL, as in FIX tag 54

# Special case for a cancel
order = Order(id='order #1')

# Retrieve individual attributes
order.side # Side object
order.symbol
order.quantity
order.price (None if market order)
order.id
order.time
```

## class Execution, Fill

An Execution object represents an execution result where bid and ask orders are matched.

In general, when execution is invoked for a market, zero or more execution objects are returned. For example, one bid order can be matched with multiple ask orders of smaller quantity, or it could be queued without being matched with any orders at all.

Each Execution object contains bid- and ask-sides of Fill objects.

```
from marketsim import Market

market = Market()
market.place_order('buy', 'symbol1', quantity=10, price=100)
market.place_order('sell', 'symbol1', quantity=10, price=100)
executions = market.execute()

for execution in executions:
    execution.quantity # executed number of shares
    execution.price    # executed price
    execution.bid_fill # bid-side Fill object
    execution.ask_fill # ask-side Fill object

    execution.bid_fill.order    # original Order object
    execution.bid_fill.quantity # same as execution.quantity
    execution.bid_fill.price    # same as execution.price
    execution.bid_fill.order_quantity # original order quantity
    execution.bid_fill.order_price    # original order price (None if market order)
    execution.bid_fill.cumulative_quantity # cumulative quantity filled for the order entry
```

## class OrderQueue, OrderStat

An OrderQueue object maintains a queue of order entries on one side (either bid or ask).

```
from marketsim import Market, Side
market = Market()
market.place_order(...)
market.place_order(...)

product = market['symbol1']
order_queue = product[Side.BUY]

# Aggregated volume/count
order_queue.market_order_volume
order_queue.market_order_count
order_queue.limit_order_volume
order_queue.limit_order_count

order_stats = order_queue.get_order_book() # returns a list of OrderStat objects

# Individual limit order volume/count per price
for order_stat in order_stats:
    order_stat.price
    order_stat.volume
    order_stat.count
```
