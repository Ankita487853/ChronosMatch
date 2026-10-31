
"""ChronosMatch: Cython-Accelerated Matching Engine."""

import time
from dataclasses import dataclass

from chronos.protocol import Order, OrderType, Side
from chronos.order_book import OrderBook
from chronos.matching_core import match_orders


@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    symbol_id: int
    price: float
    quantity: int
    execution_timestamp_ns: int


class MatchingEngine:

    def __init__(self):
        self.order_book = OrderBook()
        self.trades = []
        self.seen_order_ids = set()

    def process_order(self, order: Order):
        """Process LIMIT and MARKET orders using the Cython kernel."""

        order_type = OrderType(order.order_type)
        side = Side(order.side)

        if order_type not in (OrderType.LIMIT, OrderType.MARKET):
            raise ValueError("Unsupported order type.")

        if order.quantity <= 0 or order.price <= 0:
            raise ValueError("Price and quantity must be positive.")

        if order.order_id in self.seen_order_ids:
            raise ValueError("Duplicate order ID.")

        symbol_id = order.symbol_id
        incoming_is_buy = side == Side.BUY

        # Get opposite-side resting orders.
        if incoming_is_buy:
            resting_orders = self.order_book.asks.get(symbol_id, [])
        else:
            resting_orders = self.order_book.bids.get(symbol_id, [])

        # Prepare Cython inputs.
        prices = []
        quantities = []

        for entry in resting_orders:
            prices.append(entry.price)
            quantities.append(entry.remaining_quantity)

        # MARKET orders have no price limit.
        if order_type == OrderType.MARKET:
            matching_price = (
                float("inf") if incoming_is_buy else 0.0
            )
        else:
            matching_price = order.price

        # Call the updated Cython matching function.
        matched_results = match_orders(
            prices,
            quantities,
            matching_price,
            order.quantity,
            incoming_is_buy
        )

        new_trades = []
        total_matched = 0
        completed_order_ids = set()

        # Use the returned index to access resting orders directly.
        for resting_index, execution_price, matched_qty in matched_results:

            resting_entry = resting_orders[resting_index]
            resting_id = resting_entry.order_id

            if incoming_is_buy:
                buy_id = order.order_id
                sell_id = resting_id
            else:
                buy_id = resting_id
                sell_id = order.order_id

            trade = Trade(
                buy_order_id=buy_id,
                sell_order_id=sell_id,
                symbol_id=symbol_id,
                price=execution_price,
                quantity=matched_qty,
                execution_timestamp_ns=time.time_ns()
            )

            new_trades.append(trade)
            self.trades.append(trade)

            total_matched += matched_qty
            resting_entry.remaining_quantity -= matched_qty

            if resting_entry.remaining_quantity == 0:
                completed_order_ids.add(resting_id)

        # Remove completely filled orders.
        if completed_order_ids:
            resting_orders[:] = [
                entry for entry in resting_orders
                if entry.order_id not in completed_order_ids
            ]

            for order_id in completed_order_ids:
                self.order_book.order_ids.remove(order_id)

        remaining = order.quantity - total_matched

        # Only LIMIT orders can rest in the order book.
        if remaining > 0 and order_type == OrderType.LIMIT:
            remaining_order = order._replace(quantity=remaining)
            self.order_book.add_order(remaining_order)

        self.seen_order_ids.add(order.order_id)

        return new_trades
