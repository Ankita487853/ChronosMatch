
from chronos.matching_engine import MatchingEngine
from chronos.protocol import Order, Side, OrderType

engine = MatchingEngine()

def make_order(order_id, timestamp, price, quantity, symbol, side):
    return Order(
        order_id,
        timestamp,
        price,
        quantity,
        symbol,
        side,
        OrderType.LIMIT
    )


# Scenario 1: One BUY matches two SELL orders
engine.process_order(make_order(1, 100, 100, 4, 1001, Side.SELL))
engine.process_order(make_order(2, 200, 101, 6, 1001, Side.SELL))
engine.process_order(make_order(3, 300, 105, 8, 1001, Side.BUY))

assert len(engine.trades) == 2
assert engine.trades[0].quantity == 4
assert engine.trades[1].quantity == 4
assert engine.trades[0].price == 100
assert engine.trades[1].price == 101

print("Scenario 1 passed: One BUY matched two SELL orders.")


# Scenario 2: Different symbols must not match
engine2 = MatchingEngine()

engine2.process_order(make_order(4, 100, 100, 5, 1001, Side.SELL))
engine2.process_order(make_order(5, 200, 110, 5, 1002, Side.BUY))

assert len(engine2.trades) == 0

print("Scenario 2 passed: Different symbols did not match.")


# Scenario 3: Price-time priority
engine3 = MatchingEngine()

engine3.process_order(make_order(6, 100, 105, 5, 1001, Side.BUY))
engine3.process_order(make_order(7, 200, 105, 5, 1001, Side.BUY))
engine3.process_order(make_order(8, 300, 105, 6, 1001, Side.SELL))

assert len(engine3.trades) == 2
assert engine3.trades[0].buy_order_id == 6
assert engine3.trades[0].quantity == 5
assert engine3.trades[1].buy_order_id == 7
assert engine3.trades[1].quantity == 1

print("Scenario 3 passed: Price-time priority works.")

print("\nAll advanced matching tests passed!")
