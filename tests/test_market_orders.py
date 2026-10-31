
from chronos.protocol import Order, Side, OrderType
from chronos.matching_engine import MatchingEngine


engine = MatchingEngine()

# Add two SELL limit orders to the book.
sell1 = Order(201, 1000, 100.0, 5, 1001,
              Side.SELL, OrderType.LIMIT)

sell2 = Order(202, 2000, 101.0, 10, 1001,
              Side.SELL, OrderType.LIMIT)

engine.process_order(sell1)
engine.process_order(sell2)

# Submit a MARKET BUY order for 8 units.
market_buy = Order(203, 3000, 1.0, 8, 1001,
                   Side.BUY, OrderType.MARKET)

trades = engine.process_order(market_buy)

print("\nMARKET BUY TEST")

for trade in trades:
    print(
        f"BUY: {trade.buy_order_id}, "
        f"SELL: {trade.sell_order_id}, "
        f"Price: {trade.price}, "
        f"Quantity: {trade.quantity}"
    )

assert len(trades) == 2
assert trades[0].quantity == 5
assert trades[1].quantity == 3

# The second SELL order should have 7 units remaining.
remaining_asks = engine.order_book.get_asks(1001)

assert len(remaining_asks) == 1
assert remaining_asks[0].order_id == 202
assert remaining_asks[0].remaining_quantity == 7

print("\nMARKET BUY TEST PASSED!")
