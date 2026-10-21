"""
CSC2107: Design & Analysis of Algorithms - Assignment 5.1
Naive vs. Memoized Fibonacci

Part 1: Implement Algorithm A (plain recursion) and Algorithm B (memoized
        recursion), each with a global call counter, and verify both return
        the same values for n = 0..20.
Part 2: Measure execution time (time.perf_counter) and call counts for a
        range of n values, tabulate results, and plot n against calls
        (log-scale y-axis) for both algorithms.
Part 4: Attempt Algorithm B at n = 1000 with default recursion settings,
        demonstrate the RecursionError, and implement two fixes (iterative
        fast path and sys.setrecursionlimit) with a discussion of trade-offs.

Run:  python assignment_5_1.py
Outputs:
  - results_table.csv   (Part 2 table: algorithm, n, calls, time)
  - calls_plot.png      (Part 2 plot, log scale)
  - time_plot.png       (Part 2 plot, log scale)
  - console report      (Parts 1 and 4 findings)
"""

import csv
import math
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# Part 1: Implementation
# ---------------------------------------------------------------------------

# Global counters recording how many times each function is called.
calls_a = 0
calls_b = 0

# Memoization table shared by Algorithm B. Cleared before each timed run.
fibtable = {}


def fib_a(n: int) -> int:
    """Algorithm A: plain recursion.

    F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2).
    """
    global calls_a
    calls_a += 1
    if n == 0 or n == 1:
        value = n
    else:
        value = fib_a(n - 1) + fib_a(n - 2)
    return value


def fib_b(n: int) -> int:
    """Algorithm B: recursion with memoization.

    Mirrors the assignment pseudocode, including the fibtable[n] lookup
    discussed in Part 4.3.
    """
    global calls_b
    calls_b += 1
    if n in fibtable:
        return fibtable[n]
    if n == 0 or n == 1:
        value = n
    else:
        value = fib_b(n - 1) + fib_b(n - 2)
    fibtable[n] = value
    return value


def clear_fibtable() -> None:
    """Clear the memoization table (required before every Algorithm B run)."""
    fibtable.clear()


def part1_verify() -> None:
    """Check both functions agree for n = 0..20 and report the counters."""
    print("Part 1: verifying fib_a(n) == fib_b(n) for n = 0..20")
    ok = True
    for n in range(21):
        clear_fibtable()
        calls_a = 0
        calls_b = 0
        ra, rb = fib_a(n), fib_b(n)
        if ra != rb:
            ok = False
            print(f"  MISMATCH at n={n}: A={ra}, B={rb}")
    clear_fibtable()
    print(f"  All values match: {ok}")
    print()


# ---------------------------------------------------------------------------
# Part 2: Experiments
# ---------------------------------------------------------------------------

N_A = [5, 10, 15, 20, 25, 30, 35]
N_B = [10, 50, 100, 200, 500, 1000]
TIME_LIMIT_S = 60.0


def time_run(algorithm: str, n: int) -> tuple[int, int, float]:
    """Run one timed experiment.

    Returns (calls, result_value, elapsed_seconds). Stops early (calls = -1)
    when the 60-second limit is exceeded for Algorithm A.
    """
    global calls_a, calls_b
    calls_a = 0
    calls_b = 0
    if algorithm == "A":
        calls_a = 0
        start = time.perf_counter()
        try:
            result = fib_a(n)
        except RecursionError:
            return -1, None, time.perf_counter() - start
        elapsed = time.perf_counter() - start
        return calls_a, result, elapsed
    else:
        clear_fibtable()
        start = time.perf_counter()
        try:
            result = fib_b(n)
        except RecursionError:
            # Expected at n=1000 with default settings (see Part 4.1).
            return -1, None, time.perf_counter() - start
        elapsed = time.perf_counter() - start
        return calls_b, result, elapsed


def run_experiments() -> list[dict]:
    """Collect (algorithm, n, calls, time) rows for all Part 2 runs."""
    rows = []

    print("Part 2a: Algorithm A")
    for n in N_A:
        calls, _result, elapsed = time_run("A", n)
        rows.append({"algorithm": "A", "n": n, "calls": calls, "time": elapsed})
        print(f"  n={n:4d}  calls={calls:10d}  time={elapsed:.6f} s")
        if elapsed > TIME_LIMIT_S:
            print(f"  Stopping Algorithm A: run exceeded {TIME_LIMIT_S:.0f} s.")
            break
    print()

    print("Part 2b: Algorithm B")
    for n in N_B:
        calls, _result, elapsed = time_run("B", n)
        rows.append({"algorithm": "B", "n": n, "calls": calls, "time": elapsed})
        if calls == -1:
            print(f"  n={n:4d}  RecursionError with default recursion limit"
                  f" (analyzed in Part 4)")
        else:
            print(f"  n={n:4d}  calls={calls:10d}  time={elapsed:.6f} s")
    print()
    return rows


def write_table(rows: list[dict], path: Path) -> None:
    """Write results table to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["algorithm", "n", "calls", "time"])
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "algorithm": row["algorithm"],
                    "n": row["n"],
                    "calls": row["calls"],
                    "time": f"{row['time']:.6f}",
                }
            )


def plot_results(rows: list[dict], calls_path: Path, time_path: Path) -> None:
    """Plot n against call count and n against time for both algorithms.

    Log scale on the y-axis is needed because Algorithm A's call count grows
    exponentially (it spans many orders of magnitude) while Algorithm B's
    grows only linearly; on a linear axis the B curve would be flat at zero
    and unreadable next to A.
    """
    a_rows = [r for r in rows if r["algorithm"] == "A" and r["calls"] >= 0]
    b_rows = [r for r in rows if r["algorithm"] == "B" and r["calls"] >= 0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r["n"] for r in a_rows], [r["calls"] for r in a_rows],
            "o-", label="Algorithm A (plain recursion)")
    ax.plot([r["n"] for r in b_rows], [r["calls"] for r in b_rows],
            "s-", label="Algorithm B (memoized)")
    ax.set_yscale("log")
    ax.set_xlabel("n")
    ax.set_ylabel("function calls (log scale)")
    ax.set_title("Fibonacci: function calls vs n")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(calls_path, dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot([r["n"] for r in a_rows], [r["time"] for r in a_rows],
            "o-", label="Algorithm A (plain recursion)")
    ax.plot([r["n"] for r in b_rows], [r["time"] for r in b_rows],
            "s-", label="Algorithm B (memoized)")
    ax.set_yscale("log")
    ax.set_xlabel("n")
    ax.set_ylabel("execution time (s, log scale)")
    ax.set_title("Fibonacci: execution time vs n")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(time_path, dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Part 4: Pushing to n = 1000
# ---------------------------------------------------------------------------

def part4() -> None:
    """Demonstrate the default-recursion-limit failure and two fixes."""
    print("Part 4.1: Algorithm B with n=1000, default recursion settings")
    clear_fibtable()
    try:
        fib_b(1000)
        print("  Unexpected: call succeeded with default settings.")
    except RecursionError as exc:
        print(f"  RecursionError: {exc}")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    print()

    print("Part 4.2a: Fix 1 - iterative bottom-up Fibonacci (no recursion)")
    start = time.perf_counter()
    value = fib_iterative(1000)
    elapsed = time.perf_counter() - start
    print(f"  F(1000) computed in {elapsed:.6f} s")
    print(f"  digits in F(1000): {len(str(value))}")
    print(f"  F(1000) mod 10**12 = {value % 10**12}")
    print()

    print("Part 4.2b: Fix 2 - raise the recursion limit, then call Algorithm B")
    old_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(5000)
        clear_fibtable()
        start = time.perf_counter()
        value = fib_b(1000)
        elapsed = time.perf_counter() - start
        print(f"  F(1000) computed in {elapsed:.6f} s")
        print(f"  digits in F(1000): {len(str(value))}")
        print(f"  F(1000) mod 10**12 = {value % 10**12}")
    finally:
        sys.setrecursionlimit(old_limit)
        clear_fibtable()
    print()


def fib_iterative(n: int) -> int:
    """Bottom-up Fibonacci: O(n) time, O(1) space, no recursion."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    here = Path(__file__).resolve().parent

    part1_verify()

    rows = run_experiments()
    table_path = here / "results_table.csv"
    write_table(rows, table_path)
    print(f"  Results table written to {table_path.name}")
    print()

    plot_results(rows, here / "calls_plot.png", here / "time_plot.png")
    print("  Plots written to calls_plot.png and time_plot.png")
    print()

    part4()

    # Sanity check: memoized and iterative results must agree everywhere.
    old_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(5000)
        for n in [200, 500, 1000]:
            clear_fibtable()
            assert fib_b(n) == fib_iterative(n), f"mismatch at n={n}"
    finally:
        sys.setrecursionlimit(old_limit)
        clear_fibtable()
    print("Sanity check passed: memoized and iterative results agree.")


if __name__ == "__main__":
    main()
