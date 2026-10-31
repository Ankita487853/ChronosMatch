
"""ChronosMatch: Optimized Limit Order Book."""

from dataclasses import dataclass
from typing import Optional
from bisect import bisect_left

from chronos.protocol import Order, OrderType, Side


@dataclass
class BookEntry:
    """An order stored in the order book."""

    order: Order
    remaining_quantity: int

    @property
    def price(self) -> float:
        return self.order.price

    @property
    def timestamp_ns(self) -> int:
        return self.order.timestamp_ns

    @property
    def order_id(self) -> int:
        return self.order.order_id


class OrderBook:
    """Stores BUY and SELL limit orders with price-time priority."""

    def __init__(self):
        self.bids = {}
        self.asks = {}
        self.order_ids = set()

    def add_order(self, order: Order) -> BookEntry:
        """Add a valid LIMIT order using binary search insertion."""

        if OrderType(order.order_type) != OrderType.LIMIT:
            raise ValueError("Only LIMIT orders can be added to the order book.")

        side = Side(order.side)

        if order.quantity <= 0:
            raise ValueError("Order quantity must be greater than zero.")

        if order.price <= 0:
            raise ValueError("Order price must be greater than zero.")

        if order.order_id in self.order_ids:
            raise ValueError(f"Duplicate order ID: {order.order_id}")

        entry = BookEntry(
            order=order,
            remaining_quantity=order.quantity
        )

        symbol_id = order.symbol_id

        if side == Side.BUY:
            orders = self.bids.setdefault(symbol_id, [])

            # Higher BUY prices have higher priority.
            # Earlier timestamps and lower IDs win ties.
            key = (-entry.price, entry.timestamp_ns, entry.order_id)

        else:
            orders = self.asks.setdefault(symbol_id, [])

            # Lower SELL prices have higher priority.
            # Earlier timestamps and lower IDs win ties.
            key = (entry.price, entry.timestamp_ns, entry.order_id)

        # Find the insertion position using binary search.
        keys = [
            (-item.price, item.timestamp_ns, item.order_id)
            if side == Side.BUY
            else (item.price, item.timestamp_ns, item.order_id)
            for item in orders
        ]

        position = bisect_left(keys, key)

        # Insert without sorting the entire order book.
        orders.insert(position, entry)

        self.order_ids.add(order.order_id)

        return entry

    def best_bid(self, symbol_id: int) -> Optional[BookEntry]:
        """Return the highest-priority BUY order."""

        orders = self.bids.get(symbol_id, [])
        return orders[0] if orders else None

    def best_ask(self, symbol_id: int) -> Optional[BookEntry]:
        """Return the highest-priority SELL order."""

        orders = self.asks.get(symbol_id, [])
        return orders[0] if orders else None

    def get_bids(self, symbol_id: int):
        """Return BUY orders in priority order."""

        return list(self.bids.get(symbol_id, []))

    def get_asks(self, symbol_id: int):
        """Return SELL orders in priority order."""

        return list(self.asks.get(symbol_id, []))
