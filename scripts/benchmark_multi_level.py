
"""ChronosMatch: Multi-Scenario Order Book Benchmark."""

import time
import math
import gc
import statistics

from chronos.protocol import Order, OrderType, Side
from chronos.matching_engine import MatchingEngine


BOOK_SIZES = (5, 100, 500, 1000)

SCENARIOS = ("EARLY_FILL", "DEEP_FILL", "NO_CROSS")

WARMUP = 20
OPERATIONS_PER_ROUND = 50
ROUNDS = 3


def create_test_case(index, book_size, scenario):

    engine = MatchingEngine()

    base_id = index * (book_size + 2)
    base_timestamp = time.time_ns()

    # Create resting SELL orders.
    for i in range(book_size):

        if scenario == "EARLY_FILL":

            if i == 0:
                price, quantity = 100.0, 3
            elif i == 1:
                price, quantity = 100.0, 4
            elif i == 2:
                price, quantity = 101.0, 5
            else:
                price, quantity = 103.0, 1

        elif scenario == "DEEP_FILL":

            # Every order is eligible for matching.
            # The incoming BUY must reach the final order.
            price = 100.0 + (i * 0.001)

            if i == book_size - 1:
                quantity = 10
            else:
                quantity = 1

        elif scenario == "NO_CROSS":

            # All SELL orders are above the BUY limit.
            price = 103.0
            quantity = 1

        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        order = Order(
            order_id=base_id + i + 1,
            timestamp_ns=base_timestamp + i,
            price=price,
            quantity=quantity,
            symbol_id=1001,
            side=Side.SELL,
            order_type=OrderType.LIMIT
        )

        engine.order_book.add_order(order)

    # Configure the incoming BUY order.
    if scenario == "EARLY_FILL":

        buy_price = 102.0
        buy_quantity = 10

        expected_trades = 3
        expected_quantity = 10

    elif scenario == "DEEP_FILL":

        buy_price = 102.0

        # Match every resting order.
        # The last order will be partially filled.
        buy_quantity = book_size - 1 + 5

        expected_trades = book_size
        expected_quantity = buy_quantity

    else:  # NO_CROSS

        buy_price = 102.0
        buy_quantity = 1

        expected_trades = 0
        expected_quantity = 0

    buy_order = Order(
        order_id=base_id + book_size + 1,
        timestamp_ns=base_timestamp + book_size + 1,
        price=buy_price,
        quantity=buy_quantity,
        symbol_id=1001,
        side=Side.BUY,
        order_type=OrderType.LIMIT
    )

    return (
        engine,
        buy_order,
        expected_trades,
        expected_quantity
    )


def create_cases(start, count, book_size, scenario):

    return [
        create_test_case(i, book_size, scenario)
        for i in range(start, start + count)
    ]


def run_benchmark_round(cases):

    latencies = []

    for engine, order, expected_trades, expected_quantity in cases:

        start = time.perf_counter_ns()

        trades = engine.process_order(order)

        end = time.perf_counter_ns()

        # Correctness checks are outside the timed section.
        total_quantity = sum(
            trade.quantity for trade in trades
        )

        if len(trades) != expected_trades:
            raise RuntimeError(
                f"Trade count mismatch: "
                f"expected {expected_trades}, got {len(trades)}"
            )

        if total_quantity != expected_quantity:
            raise RuntimeError(
                f"Quantity mismatch: "
                f"expected {expected_quantity}, got {total_quantity}"
            )

        latencies.append((end - start) / 1000)

    return latencies


def percentile(values, percent):

    ordered = sorted(values)

    index = math.ceil(percent / 100 * len(ordered)) - 1

    return ordered[index]


def benchmark_scenario(book_size, scenario):

    print()
    print("=" * 70)
    print(f" SCENARIO: {scenario}")
    print(f" ORDER BOOK SIZE: {book_size:,} RESTING ORDERS")
    print("=" * 70)

    # Prepare and execute warm-up operations.
    warmup_cases = create_cases(
        1,
        WARMUP,
        book_size,
        scenario
    )

    run_benchmark_round(warmup_cases)

    del warmup_cases

    all_latencies = []

    gc_was_enabled = gc.isenabled()

    try:

        for round_number in range(ROUNDS):

            start_index = (
                WARMUP
                + round_number * OPERATIONS_PER_ROUND
                + 1
            )

            # Prepare test cases outside the timed section.
            cases = create_cases(
                start_index,
                OPERATIONS_PER_ROUND,
                book_size,
                scenario
            )

            gc.disable()

            try:
                latencies = run_benchmark_round(cases)

            finally:
                if gc_was_enabled:
                    gc.enable()

            del cases

            average = statistics.mean(latencies)
            median = statistics.median(latencies)
            p99 = percentile(latencies, 99)

            all_latencies.extend(latencies)

            print(
                f"Round {round_number + 1}: "
                f"Average={average:.2f} us | "
                f"Median={median:.2f} us | "
                f"P99={p99:.2f} us"
            )

    finally:

        if gc_was_enabled:
            gc.enable()

    print("-" * 70)
    print(f"FINAL RESULTS: {scenario} - {book_size:,} ORDERS")
    print("-" * 70)

    print(f"Total Operations     : {len(all_latencies):,}")

    print(
        f"Average Latency     : "
        f"{statistics.mean(all_latencies):.2f} us"
    )

    print(
        f"Median Latency      : "
        f"{statistics.median(all_latencies):.2f} us"
    )

    print(
        f"P99 Latency         : "
        f"{percentile(all_latencies, 99):.2f} us"
    )

    print(
        f"Minimum Latency     : "
        f"{min(all_latencies):.2f} us"
    )

    print(
        f"Maximum Latency     : "
        f"{max(all_latencies):.2f} us"
    )


def main():

    print("=" * 70)
    print(" CHRONOSMATCH :: MULTI-SCENARIO ORDER BOOK BENCHMARK")
    print("=" * 70)

    print(f"Book Sizes           : {BOOK_SIZES}")
    print(f"Scenarios            : {SCENARIOS}")
    print(f"Warm-up Operations   : {WARMUP}")
    print(f"Operations/Round     : {OPERATIONS_PER_ROUND}")
    print(f"Benchmark Rounds     : {ROUNDS}")

    for scenario in SCENARIOS:

        for book_size in BOOK_SIZES:

            benchmark_scenario(book_size, scenario)

    print()
    print("=" * 70)
    print(" ALL BENCHMARK SCENARIOS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
