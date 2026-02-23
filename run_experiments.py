# =============================================================================
# run_experiments.py -- Automated experiment runner for Project 1 (CDCL solver)
# =============================================================================
#
# COMMANDS
# --------
#   python run_experiments.py                     basic SAT/UNSAT tests (8 instances)
#   python run_experiments.py --pigeon            basic + pigeon-hole hole6/7/8
#   python run_experiments.py --hole 6 7          specific hole instances
#   python run_experiments.py --all               all instances incl. hole9/10 (slow!)
#
#   python run_experiments.py --check-only        verify existing proof files (no solver)
#   python run_experiments.py --check-only --pigeon
#
#   python run_experiments.py --clean             delete generated proof_*.txt files
#                                                 (proof_example.txt is preserved as
#                                                  a format illustration)
# =============================================================================

import argparse
import glob
import os
import sys
import time
import subprocess

from cdcl import read_dimacs, CDCL
from proof_checker import check_proof


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
    ("border_level0.cnf",  "dimacs/border_level0.cnf",       "UNSAT"),  # edge case: conflict at DL0
]

PIGEON_TESTS = {
    6:  ("hole6.cnf",  "dimacs/pigeon-hole/hole6.cnf",  "UNSAT"),
    7:  ("hole7.cnf",  "dimacs/pigeon-hole/hole7.cnf",  "UNSAT"),
    8:  ("hole8.cnf",  "dimacs/pigeon-hole/hole8.cnf",  "UNSAT"),
    9:  ("hole9.cnf",  "dimacs/pigeon-hole/hole9.cnf",  "UNSAT"),
    10: ("hole10.cnf", "dimacs/pigeon-hole/hole10.cnf", "UNSAT"),
}


def proof_filename(name):
    return "proof_%s.txt" % name.replace(" ", "_").replace("/", "_")


# ---------------------------------------------------------------------------
# --clean
# ---------------------------------------------------------------------------

def cmd_clean():
    """Delete all proof_*.txt files in the current directory (except proof_example.txt)."""
    files = [f for f in glob.glob("proof_*.txt") if f != "proof_example.txt"]
    if not files:
        print("No proof files found.")
        return
    for f in files:
        size_kb = os.path.getsize(f) // 1024
        os.remove(f)
        print("Deleted %s (%d KB)" % (f, size_kb))
    print("Cleaned %d proof file(s)." % len(files))


# ---------------------------------------------------------------------------
# --check-only: verify existing proof files without re-running solver
# ---------------------------------------------------------------------------

def cmd_check_only(tests):
    """Verify pre-generated proof files using proof_checker; skip SAT instances."""
    print()
    print("=" * 70)
    print("PROOF VERIFICATION (check-only mode)")
    print("=" * 70)
    print("%-22s  %-30s  %7s  %8s" % ("Instance", "Proof file", "Steps", "Result"))
    print("-" * 70)

    passed = failed = missing = 0
    for name, cnf_path, expected in tests:
        if expected == "SAT":
            print("%-22s  %-30s  %7s  %8s" % (name, "(SAT, no proof)", "---", "SKIP"))
            continue

        pf = proof_filename(name)
        if not os.path.isfile(pf):
            print("%-22s  %-30s  %7s  %8s" % (name, pf, "---", "MISSING"))
            missing += 1
            continue

        # Count steps
        with open(pf) as f:
            steps = sum(1 for line in f if line and line[0].isdigit())

        # Call checker
        t0 = time.perf_counter()
        valid, message, stats = check_proof(cnf_path, pf)
        t1 = time.perf_counter()

        result = "VALID (%.3fs)" % (t1 - t0) if valid else "INVALID"
        print("%-22s  %-30s  %7d  %8s" % (name, pf, steps, "VALID" if valid else "INVALID"))
        if not valid:
            print("  -> %s" % message)
            failed += 1
        else:
            passed += 1

    print("-" * 70)
    print("Checked: %d valid, %d invalid, %d missing" % (passed, failed, missing))
    print("=" * 70)


# ---------------------------------------------------------------------------
# Full run: solve + generate proof + verify
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

    pf = proof_filename(name) if expected == "UNSAT" else None

    t0 = time.perf_counter()
    solver = CDCL(clauses, proof_file=pf)
    sat    = solver.solve()
    solver.proof.close()
    t1 = time.perf_counter()

    result = "SAT" if sat else "UNSAT"

    proof_steps = None
    checker_result = "n/a"
    if pf and os.path.isfile(pf):
        with open(pf) as f:
            proof_steps = sum(1 for line in f if line and line[0].isdigit())
        valid, _, _ = check_proof(cnf_path, pf)
        checker_result = "VALID" if valid else "INVALID"

    return {
        "name":        name,
        "vars":        nvars,
        "clauses":     len(clauses),
        "result":      result,
        "expected":    expected,
        "time_s":      t1 - t0,
        "proof_steps": proof_steps,
        "proof_file":  pf,
        "checker":     checker_result,
        "ok":          result == expected,
    }


def print_table(rows):
    print()
    print("=" * 90)
    print("EXPERIMENT RESULTS")
    print("=" * 90)
    print("%-22s %5s %7s %6s %9s %11s %8s %7s" % (
        "Instance", "Vars", "Clauses", "Result", "Time (s)", "ProofSteps", "Checker", "Status"
    ))
    print("-" * 90)

    passed = failed = errors = 0
    for r in rows:
        time_str  = ("%.4f"  % r["time_s"])      if r["time_s"]    is not None else "ERROR"
        steps_str = ("%d"    % r["proof_steps"])  if r["proof_steps"] is not None else "---"
        status    = "[OK]"   if r["ok"] else ("[ERROR]" if r["result"] == "ERROR" else "[FAIL]")
        if r["ok"]:       passed += 1
        elif r["result"] == "ERROR": errors += 1
        else:             failed += 1

        print("%-22s %5s %7s %6s %9s %11s %8s %7s" % (
            r["name"][:22], str(r["vars"])[:5], str(r["clauses"])[:7],
            r["result"], time_str, steps_str, r["checker"], status,
        ))

    print("-" * 90)
    print("Total: %d    Passed: %d    Failed: %d    Errors: %d" % (
        passed + failed + errors, passed, failed, errors))
    print("=" * 90)


# ---------------------------------------------------------------------------
# Argument parsing + dispatch
# ---------------------------------------------------------------------------

def build_test_list(args):
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
    return tests


def main():
    parser = argparse.ArgumentParser(
        description="Run CDCL Project 1 experiments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_experiments.py                   basic tests (8 instances)
  python run_experiments.py --pigeon          basic + hole6/7/8
  python run_experiments.py --hole 6 7        only hole6 and hole7
  python run_experiments.py --all             all including hole9/10 (slow)
  python run_experiments.py --check-only      verify existing proof files
  python run_experiments.py --check-only --pigeon
  python run_experiments.py --clean           delete all proof_*.txt
"""
    )
    parser.add_argument("--pigeon",     action="store_true",
                        help="Include hole6, hole7, hole8")
    parser.add_argument("--hole",       type=int, nargs="+", metavar="N",
                        help="Include specific hole instances (e.g. --hole 6 7)")
    parser.add_argument("--all",        action="store_true",
                        help="Include hole6 through hole10 (slow!)")
    parser.add_argument("--check-only", action="store_true",
                        help="Verify existing proof files without re-running solver")
    parser.add_argument("--clean",      action="store_true",
                        help="Delete all proof_*.txt files and exit")
    args = parser.parse_args()

    # --clean: delete proofs and exit immediately
    if args.clean:
        cmd_clean()
        return

    tests = build_test_list(args)

    # --check-only: verify existing proofs, no solver invocation
    if args.check_only:
        cmd_check_only(tests)
        return

    # Normal mode: solve + generate proof + verify
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
