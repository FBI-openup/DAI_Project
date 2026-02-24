# COMMANDS
# --------
#   python run_experiments.py                     basic SAT/UNSAT tests (9 instances)
#   python run_experiments.py --hole 6          specific hole instances
#   python run_experiments.py --all               all instances incl. hole9/10 (slow!)
#   python run_experiments.py --all12             exactly the 12 instances from Table 1
#
#   python run_experiments.py --check-only        verify existing proof files (no solver)
#
#   python run_experiments.py --clean             delete generated proof_*.txt files
#                                                 (proof_example.txt is preserved as
#                                                  a format illustration)

import argparse
import glob
import os
import sys
import time
import subprocess

from cdcl import read_dimacs, CDCL
from proof_checker import check_proof


BASIC_TESTS = [
    ("prop.cnf",           "prop.cnf",                       "SAT"),
    ("simple.cnf",         "dimacs/simple.cnf",              "SAT"),
    ("single_literal.cnf", "dimacs/single_literal.cnf",      "SAT"),
    ("empty_lines.cnf",    "dimacs/empty_lines.cnf",         "SAT"),
    ("with_comments.cnf",  "dimacs/with_comments.cnf",       "SAT"),
    ("multiline.cnf",      "dimacs/multiline.cnf",           "SAT"),
    ("large.cnf",          "dimacs/large.cnf",               "SAT"),
    ("DPLL example2",      "dimacs/DPLL example2",           "UNSAT"),
    ("border_level0.cnf",  "dimacs/border_level0.cnf",       "UNSAT"),
]

PIGEON_TESTS = {
    6:  ("hole6.cnf",  "dimacs/pigeon-hole/hole6.cnf",  "UNSAT"),
    7:  ("hole7.cnf",  "dimacs/pigeon-hole/hole7.cnf",  "UNSAT"),
    8:  ("hole8.cnf",  "dimacs/pigeon-hole/hole8.cnf",  "UNSAT"),
    9:  ("hole9.cnf",  "dimacs/pigeon-hole/hole9.cnf",  "UNSAT"),
    10: ("hole10.cnf", "dimacs/pigeon-hole/hole10.cnf", "UNSAT"),
}

REPORT_TESTS = BASIC_TESTS + [
    PIGEON_TESTS[6],
    PIGEON_TESTS[7],
    PIGEON_TESTS[8],
]


def proof_filename(name):
    return "proof_%s.txt" % name.replace(" ", "_").replace("/", "_")


def cmd_clean():
    files = [f for f in glob.glob("proof_*.txt") if f != "proof_example.txt"]
    if not files:
        print("No proof files found.")
        return
    for f in files:
        os.remove(f)
        print("Deleted %s" % f)
    print("Cleaned %d file(s)." % len(files))


def cmd_check_only(tests):
    print("\nPROOF VERIFICATION")
    print("-" * 90)
    passed = failed = missing = 0
    for name, cnf_path, expected in tests:
        if expected == "SAT":
            continue
        pf = proof_filename(name)
        if not os.path.isfile(pf):
            missing += 1
            continue
        
        t_start = time.perf_counter()
        valid, _, _ = check_proof(cnf_path, pf)
        t_check = time.perf_counter() - t_start

        print("%-22s  %-8s (%.4fs)" % (name, "VALID" if valid else "INVALID", t_check))
        if valid: passed += 1
        else: failed += 1
    print("-" * 90)
    print("Result: %d valid, %d invalid, %d missing" % (passed, failed, missing))


def run_one(name, cnf_path, expected):
    if not os.path.isfile(cnf_path):
        return {"name": name, "ok": False, "result": "ERROR"}

    clauses = read_dimacs(cnf_path)
    nvars      = max((abs(l) for cl in clauses for l in cl), default=0)
    n_clauses  = len(clauses)          # snapshot BEFORE solve() appends learned clauses
    pf = proof_filename(name) if expected == "UNSAT" else None

    t0 = time.perf_counter()
    solver = CDCL(clauses, proof_file=pf)
    sat    = solver.solve()
    solver.proof.close()
    t1 = time.perf_counter()

    result = "SAT" if sat else "UNSAT"
    proof_steps = None
    checker_time = None
    checker_result = "n/a"
    if pf and os.path.isfile(pf):
        with open(pf) as f:
            proof_steps = sum(1 for line in f if line and line[0].isdigit())
        
        t_c0 = time.perf_counter()
        valid, _, _ = check_proof(cnf_path, pf)
        checker_time = time.perf_counter() - t_c0
        checker_result = "VALID" if valid else "INVALID"

    return {
        "name": name, "vars": nvars, "clauses": n_clauses,
        "result": result, "time": t1 - t0, "steps": proof_steps,
        "checker_time": checker_time, "checker": checker_result,
        "ok": result == expected,
    }


def print_table(rows):
    print("\n" + "=" * 95)
    header = "%-20s %5s %5s %7s %10s %10s %12s %7s" % (
        "Instance", "Vars", "Cls", "Res", "Time(s)", "Steps", "Check Time", "Status"
    )
    print(header)
    print("-" * 95)
    for r in rows:
        status = "[OK]" if r["ok"] else "[FAIL]"
        ctime_str = "%.4f" % r["checker_time"] if r["checker_time"] is not None else "---"
        steps_str = str(r["steps"]) if r["steps"] is not None else "---"
        print("%-20s %5d %5d %7s %10.4f %10s %12s %7s" % (
            r["name"][:20], r["vars"], r["clauses"],
            r["result"], r["time"], steps_str, ctime_str, status
        ))
    print("=" * 95)


def build_test_list(args):
    if args.all12:
        return REPORT_TESTS
        
    tests = list(BASIC_TESTS)
    if args.all:
        for n in [6, 7, 8, 9, 10]: tests.append(PIGEON_TESTS[n])
    elif args.hole:
        for n in args.hole:
            if n in PIGEON_TESTS: tests.append(PIGEON_TESTS[n])
    elif args.pigeon:
        for n in [6, 7, 8]: tests.append(PIGEON_TESTS[n])
    return tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pigeon", action="store_true")
    parser.add_argument("--hole", type=int, nargs="+")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--all12", action="store_true", help="Run the 12 instances from Table 1")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if args.clean:
        cmd_clean()
        return

    tests = build_test_list(args)
    if args.check_only:
        cmd_check_only(tests)
        return

    results = []
    for name, path, expected in tests:
        print("Running %-22s ..." % name, end=" ", flush=True)
        r = run_one(name, path, expected)
        print("OK" if r["ok"] else "FAIL")
        results.append(r)
    print_table(results)


if __name__ == "__main__":
    main()
