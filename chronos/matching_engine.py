
"""ChronosMatch: Optimized Cython Matching Engine."""

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

        # Determine the matching price.
        if order_type == OrderType.MARKET:
            matching_price = (
                float("inf") if incoming_is_buy else 0.0
            )
        else:
            matching_price = order.price

        # Prepare only eligible resting orders.
        prices = []
        quantities = []
        available_quantity = 0

        for entry in resting_orders:

            # Stop when the price is no longer eligible.
            if incoming_is_buy:
                if entry.price > matching_price:
                    break
            else:
                if entry.price < matching_price:
                    break

            prices.append(entry.price)
            quantities.append(entry.remaining_quantity)

            available_quantity += entry.remaining_quantity

            # Stop once enough quantity is available.
            if available_quantity >= order.quantity:
                break

        # Call the Cython matching function.
        matched_results = match_orders(
            prices,
            quantities,
            matching_price,
            order.quantity,
            incoming_is_buy
        )

        # Capture one timestamp for all trades from this order.
        execution_timestamp_ns = (
            time.time_ns() if matched_results else 0
        )

        new_trades = []
        total_matched = 0
        completed_prefix_count = 0

        # Process matching results using original order indexes.
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
                execution_timestamp_ns=execution_timestamp_ns
            )

            new_trades.append(trade)
            self.trades.append(trade)

            total_matched += matched_qty
            resting_entry.remaining_quantity -= matched_qty

            # Fully filled orders form a consecutive prefix
            # because matching follows price-time priority.
            if resting_entry.remaining_quantity == 0:

                if resting_index != completed_prefix_count:
                    raise RuntimeError(
                        "Completed orders are not a consecutive priority prefix."
                    )

                completed_prefix_count += 1

        # Remove completed orders directly from the front.
        if completed_prefix_count:

            # Remove completed order IDs from the index.
            for index in range(completed_prefix_count):
                resting_id = resting_orders[index].order_id
                self.order_book.order_ids.remove(resting_id)

            # Remove the completed prefix from the order book.
            del resting_orders[:completed_prefix_count]

        # Calculate the remaining incoming quantity.
        remaining = order.quantity - total_matched

        # Only LIMIT orders can rest in the order book.
        if remaining > 0 and order_type == OrderType.LIMIT:
            remaining_order = order._replace(quantity=remaining)
            self.order_book.add_order(remaining_order)

        self.seen_order_ids.add(order.order_id)

        return new_trades
