
"""ChronosMatch: Multi-round Matching Engine Benchmark."""

import time
import math
import statistics

from chronos.protocol import Order, OrderType, Side
from chronos.matching_engine import MatchingEngine


WARMUP_OPERATIONS = 10000
MEASURED_OPERATIONS = 10000
BENCHMARK_ROUNDS = 7


def create_test_case(index):
    engine = MatchingEngine()

    # Prepare one resting SELL order.
    sell_order = Order(
        order_id=index * 2,
        timestamp_ns=time.time_ns(),
        price=100.0,
        quantity=10,
        symbol_id=1001,
        side=Side.SELL,
        order_type=OrderType.LIMIT
    )

    engine.order_book.add_order(sell_order)

    # Incoming BUY order crosses the resting SELL.
    buy_order = Order(
        order_id=index * 2 + 1,
        timestamp_ns=time.time_ns(),
        price=101.0,
        quantity=5,
        symbol_id=1001,
        side=Side.BUY,
        order_type=OrderType.LIMIT
    )

    return engine, buy_order


def run_round(cases):
    latencies = []

    for engine, order in cases:
        start = time.perf_counter_ns()

        trades = engine.process_order(order)

        end = time.perf_counter_ns()

        if len(trades) != 1:
            raise RuntimeError("Expected exactly one executed trade.")

        latencies.append((end - start) / 1000)

    return latencies


def percentile(values, percent):
    ordered = sorted(values)
    index = math.ceil((percent / 100) * len(ordered)) - 1
    return ordered[index]


def main():

    print("=" * 65)
    print(" CHRONOSMATCH :: MULTI-ROUND MATCHING ENGINE BENCHMARK")
    print("=" * 65)

    print(f"Warm-up Operations : {WARMUP_OPERATIONS:,}")
    print(f"Measured Operations: {MEASURED_OPERATIONS:,}")
    print(f"Benchmark Rounds   : {BENCHMARK_ROUNDS}")
    print("-" * 65)

    # Prepare independent test cases before timing.
    warmup_cases = [
        create_test_case(i + 1)
        for i in range(WARMUP_OPERATIONS)
    ]

    measured_cases = [
        create_test_case(WARMUP_OPERATIONS + i + 1)
        for i in range(MEASURED_OPERATIONS * BENCHMARK_ROUNDS)
    ]

    # Warm-up.
    run_round(warmup_cases)

    round_averages = []
    round_medians = []
    round_p99s = []
    all_latencies = []

    for round_number in range(BENCHMARK_ROUNDS):

        start_index = round_number * MEASURED_OPERATIONS
        end_index = start_index + MEASURED_OPERATIONS

        cases = measured_cases[start_index:end_index]

        latencies = run_round(cases)

        average = statistics.mean(latencies)
        median = statistics.median(latencies)
        p99 = percentile(latencies, 99)

        round_averages.append(average)
        round_medians.append(median)
        round_p99s.append(p99)
        all_latencies.extend(latencies)

        print(
            f"Round {round_number + 1}: "
            f"Average={average:.2f} us | "
            f"Median={median:.2f} us | "
            f"P99={p99:.2f} us"
        )

    print("-" * 65)
    print("FINAL BENCHMARK RESULTS")
    print("-" * 65)

    print(f"Total Measured Operations : {len(all_latencies):,}")
    print(f"Median Round Average      : {statistics.median(round_averages):.2f} us")
    print(f"Median Round Median       : {statistics.median(round_medians):.2f} us")
    print(f"Median Round P99          : {statistics.median(round_p99s):.2f} us")

    print(f"Overall Average Latency   : {statistics.mean(all_latencies):.2f} us")
    print(f"Overall Median Latency    : {statistics.median(all_latencies):.2f} us")
    print(f"Overall P99 Latency       : {percentile(all_latencies, 99):.2f} us")
    print(f"Minimum Latency           : {min(all_latencies):.2f} us")
    print(f"Maximum Latency           : {max(all_latencies):.2f} us")

    avg_latency = statistics.mean(all_latencies)
    throughput = 1_000_000 / avg_latency

    print(f"Estimated Matching Rate   : {throughput:,.0f} ops/sec")

    print("=" * 65)


if __name__ == "__main__":
    main()
