"""
run_experiments.py -- Automated experiment runner for Project 1.

Usage:
    python run_experiments.py                  # basic SAT tests only
    python run_experiments.py --pigeon         # basic + pigeon-hole hole6..8
    python run_experiments.py --pigeon --hole 9 10  # include hole9, hole10
    python run_experiments.py --all            # everything including hole9/10

Output:
    - Console: ASCII results table
    - proof_<name>.txt for each UNSAT instance
    - Calls proof_checker.py to verify each proof automatically
"""

import argparse
import os
import sys
import time
import subprocess

from cdcl import read_dimacs, CDCL


# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

BASIC_TESTS = [
    # (display_name, cnf_path, expected_result)
    ("prop.cnf",           "prop.cnf",                       "SAT"),
    ("simple.cnf",         "dimacs/simple.cnf",              "SAT"),
    ("single_literal.cnf", "dimacs/single_literal.cnf",      "SAT"),
    ("empty_lines.cnf",    "dimacs/empty_lines.cnf",         "SAT"),
    ("with_comments.cnf",  "dimacs/with_comments.cnf",       "SAT"),
    ("multiline.cnf",      "dimacs/multiline.cnf",           "SAT"),
    ("large.cnf",          "dimacs/large.cnf",               "SAT"),
    ("DPLL example2",      "dimacs/DPLL example2",           "UNSAT"),
]

PIGEON_TESTS = {
    6:  ("hole6.cnf",  "dimacs/pigeon-hole/hole6.cnf",  "UNSAT"),
    7:  ("hole7.cnf",  "dimacs/pigeon-hole/hole7.cnf",  "UNSAT"),
    8:  ("hole8.cnf",  "dimacs/pigeon-hole/hole8.cnf",  "UNSAT"),
    9:  ("hole9.cnf",  "dimacs/pigeon-hole/hole9.cnf",  "UNSAT"),
    10: ("hole10.cnf", "dimacs/pigeon-hole/hole10.cnf", "UNSAT"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_one(name, cnf_path, expected):
    """Run solver on one instance; return result dict."""
    if not os.path.isfile(cnf_path):
        return {
            "name": name, "vars": "?", "clauses": "?",
            "result": "ERROR", "expected": expected,
            "time_s": None, "proof_steps": None,
            "proof_file": None, "checker": "n/a", "ok": False,
        }

    clauses = read_dimacs(cnf_path)
    nvars   = max((abs(l) for cl in clauses for l in cl), default=0)

    proof_file = None
    if expected == "UNSAT":
        proof_file = "proof_%s.txt" % name.replace(" ", "_").replace("/", "_")

    t0 = time.perf_counter()
    solver = CDCL(clauses, proof_file=proof_file)
    sat    = solver.solve()
    solver.proof.close()
    t1 = time.perf_counter()

    result = "SAT" if sat else "UNSAT"

    # Count proof steps
    proof_steps = None
    if proof_file and os.path.isfile(proof_file):
        with open(proof_file) as f:
            proof_steps = sum(1 for line in f if line and line[0].isdigit())

    # Verify proof
    checker_result = "n/a"
    if proof_file and os.path.isfile(proof_file):
        proc = subprocess.run(
            [sys.executable, "proof_checker.py", cnf_path, proof_file],
            capture_output=True, text=True
        )
        checker_result = "VALID" if proc.returncode == 0 else "INVALID"

    return {
        "name":       name,
        "vars":       nvars,
        "clauses":    len(clauses),
        "result":     result,
        "expected":   expected,
        "time_s":     t1 - t0,
        "proof_steps": proof_steps,
        "proof_file": proof_file,
        "checker":    checker_result,
        "ok":         result == expected,
    }


def print_table(rows):
    """Print a nicely formatted ASCII results table."""
    print()
    print("=" * 90)
    print("EXPERIMENT RESULTS")
    print("=" * 90)
    header = "%-22s %5s %7s %6s %9s %11s %8s %7s" % (
        "Instance", "Vars", "Clauses", "Result", "Time (s)", "ProofSteps", "Checker", "Status"
    )
    print(header)
    print("-" * 90)

    passed = 0
    failed = 0
    errors = 0
    for r in rows:
        time_str   = ("%.4f" % r["time_s"])   if r["time_s"]    is not None else "ERROR"
        steps_str  = ("%d"   % r["proof_steps"]) if r["proof_steps"] is not None else "---"
        status     = "[OK]"   if r["ok"] else ("[ERROR]" if r["result"] == "ERROR" else "[FAIL]")
        if r["ok"]:
            passed += 1
        elif r["result"] == "ERROR":
            errors += 1
        else:
            failed += 1

        print("%-22s %5s %7s %6s %9s %11s %8s %7s" % (
            r["name"][:22],
            str(r["vars"])[:5],
            str(r["clauses"])[:7],
            r["result"],
            time_str,
            steps_str,
            r["checker"],
            status,
        ))

    print("-" * 90)
    total = passed + failed + errors
    print("Total: %d    Passed: %d    Failed: %d    Errors: %d" % (total, passed, failed, errors))
    print("=" * 90)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run CDCL solver experiments and verify proofs automatically."
    )
    parser.add_argument(
        "--pigeon", action="store_true",
        help="Include pigeon-hole instances hole6, hole7, hole8 (default: off)"
    )
    parser.add_argument(
        "--hole", type=int, nargs="+", metavar="N",
        help="Include specific pigeon-hole instances (e.g. --hole 6 7 8 9)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Run all instances including hole9 and hole10 (slow)"
    )
    args = parser.parse_args()

    # Build test list
    tests = list(BASIC_TESTS)

    if args.all:
        for n in [6, 7, 8, 9, 10]:
            tests.append(PIGEON_TESTS[n])
    elif args.hole:
        for n in args.hole:
            if n in PIGEON_TESTS:
                tests.append(PIGEON_TESTS[n])
            else:
                print("Warning: hole%d not defined, skipping." % n)
    elif args.pigeon:
        for n in [6, 7, 8]:
            tests.append(PIGEON_TESTS[n])

    # Run all tests
    results = []
    for name, path, expected in tests:
        print("Running %-22s ..." % name, end=" ", flush=True)
        r = run_one(name, path, expected)
        status = "OK" if r["ok"] else ("ERROR" if r["result"] == "ERROR" else "FAIL")
        print("%s  (%.4fs)" % (status, r["time_s"] if r["time_s"] else 0))
        results.append(r)

    print_table(results)


if __name__ == "__main__":
    main()
