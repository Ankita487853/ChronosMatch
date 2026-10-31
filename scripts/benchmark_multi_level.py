
"""ChronosMatch: Large Order Book Matching Benchmark."""

import time
import math
import gc
import statistics

from chronos.protocol import Order, OrderType, Side
from chronos.matching_engine import MatchingEngine


BOOK_SIZES = (5, 100, 500, 1000)

WARMUP = 50
OPERATIONS_PER_ROUND = 200
ROUNDS = 3


def create_test_case(index, book_size):
    engine = MatchingEngine()

    base_id = index * (book_size + 2)
    base_timestamp = time.time_ns()

    # Create resting SELL orders.
    for i in range(book_size):

        if i == 0:
            price, quantity = 100.0, 3
        elif i == 1:
            price, quantity = 100.0, 4
        elif i == 2:
            price, quantity = 101.0, 5
        else:
            price, quantity = 103.0, 1

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

    # Incoming BUY order.
    buy_order = Order(
        order_id=base_id + book_size + 1,
        timestamp_ns=base_timestamp + book_size + 1,
        price=102.0,
        quantity=10,
        symbol_id=1001,
        side=Side.BUY,
        order_type=OrderType.LIMIT
    )

    return engine, buy_order


def create_cases(start, count, book_size):
    return [
        create_test_case(i, book_size)
        for i in range(start, start + count)
    ]


def run_benchmark_round(cases):
    latencies = []

    for engine, order in cases:

        start = time.perf_counter_ns()
        trades = engine.process_order(order)
        end = time.perf_counter_ns()

        total_quantity = sum(trade.quantity for trade in trades)

        if len(trades) != 3 or total_quantity != 10:
            raise RuntimeError(
                "Matching correctness check failed."
            )

        latencies.append((end - start) / 1000)

    return latencies


def percentile(values, percent):
    ordered = sorted(values)
    index = math.ceil(percent / 100 * len(ordered)) - 1
    return ordered[index]


def benchmark_book_size(book_size):

    print()
    print("=" * 65)
    print(f" ORDER BOOK SIZE: {book_size:,} RESTING ORDERS")
    print("=" * 65)

    # Warm-up.
    warmup_cases = create_cases(
        1, WARMUP, book_size
    )

    run_benchmark_round(warmup_cases)
    del warmup_cases

    all_latencies = []
    round_averages = []

    gc_was_enabled = gc.isenabled()

    try:
        for round_number in range(ROUNDS):

            start_index = (
                WARMUP
                + round_number * OPERATIONS_PER_ROUND
                + 1
            )

            cases = create_cases(
                start_index,
                OPERATIONS_PER_ROUND,
                book_size
            )

            # Disable GC only during timed operations.
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

            round_averages.append(average)
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

    print("-" * 65)
    print(f"Results for {book_size:,} resting orders")
    print("-" * 65)

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

    print("=" * 65)
    print(" CHRONOSMATCH :: LARGE ORDER BOOK BENCHMARK")
    print("=" * 65)

    print(f"Book Sizes           : {BOOK_SIZES}")
    print(f"Warm-up Operations   : {WARMUP}")
    print(f"Operations/Round     : {OPERATIONS_PER_ROUND}")
    print(f"Benchmark Rounds     : {ROUNDS}")

    for book_size in BOOK_SIZES:
        benchmark_book_size(book_size)

    print()
    print("=" * 65)
    print(" LARGE ORDER BOOK BENCHMARK COMPLETED")
    print("=" * 65)


if __name__ == "__main__":
    main()
