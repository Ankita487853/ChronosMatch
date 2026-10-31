
from chronos.matching_engine import MatchingEngine
from chronos.protocol import Order, Side, OrderType

engine = MatchingEngine()

# Add an existing SELL order
sell = Order(
    101, 100, 100.0, 6, 1001,
    Side.SELL, OrderType.LIMIT
)

engine.process_order(sell)

# Add a BUY order with a higher price
buy = Order(
    102, 200, 105.0, 10, 1001,
    Side.BUY, OrderType.LIMIT
)

engine.process_order(buy)

# Display executed trades
print("\nEXECUTED TRADES")

for trade in engine.trades:
    print(
        f"BUY ID: {trade.buy_order_id}, "
        f"SELL ID: {trade.sell_order_id}, "
        f"Price: {trade.price}, "
        f"Quantity: {trade.quantity}"
    )

# Verify matching
assert len(engine.trades) == 1
assert engine.trades[0].price == 100.0
assert engine.trades[0].quantity == 6

# Verify remaining BUY quantity
remaining_buy = engine.order_book.best_bid(1001)

assert remaining_buy is not None
assert remaining_buy.order_id == 102
assert remaining_buy.remaining_quantity == 4

print("\nAll Matching Engine tests passed!")
