
from chronos.order_book import OrderBook
from chronos.protocol import Order, Side, OrderType

book = OrderBook()

# Create three BUY orders
buy1 = Order(1, 100, 100.0, 10, 1001, Side.BUY, OrderType.LIMIT)
buy2 = Order(2, 200, 105.0, 5, 1001, Side.BUY, OrderType.LIMIT)
buy3 = Order(3, 150, 105.0, 8, 1001, Side.BUY, OrderType.LIMIT)

# Create two SELL orders
sell1 = Order(4, 300, 110.0, 6, 1001, Side.SELL, OrderType.LIMIT)
sell2 = Order(5, 250, 108.0, 4, 1001, Side.SELL, OrderType.LIMIT)

# Add orders
for order in [buy1, buy2, buy3, sell1, sell2]:
    book.add_order(order)

# Display BUY orders
print("\nBUY ORDER BOOK")
for entry in book.get_bids(1001):
    print(
        f"ID: {entry.order_id}, "
        f"Price: {entry.price}, "
        f"Quantity: {entry.remaining_quantity}"
    )

# Display SELL orders
print("\nSELL ORDER BOOK")
for entry in book.get_asks(1001):
    print(
        f"ID: {entry.order_id}, "
        f"Price: {entry.price}, "
        f"Quantity: {entry.remaining_quantity}"
    )

# Verify priority
assert [x.order_id for x in book.get_bids(1001)] == [3, 2, 1]
assert [x.order_id for x in book.get_asks(1001)] == [5, 4]

print("\nAll Order Book tests passed!")
