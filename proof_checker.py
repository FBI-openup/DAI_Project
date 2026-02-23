# =============================================================================
# proof_checker.py -- Independent Resolution Proof Verifier for Project 1
# =============================================================================
#
# USAGE:
#   python proof_checker.py <dimacs_file> <proof_file>
#
# =============================================================================

import sys
import time


def read_dimacs(filename):
    clauses = []
    num_vars = 0
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                if len(parts) >= 4 and parts[1] == 'cnf':
                    num_vars = int(parts[2])
                continue
            lits = [int(x) for x in line.split() if int(x) != 0]
            if lits:
                clauses.append(lits)
    return num_vars, clauses


def parse_proof_line(line):
    line = line.strip()
    if not line or line.startswith('c') or line.startswith('p'):
        return None

    if ':' not in line:
        raise ValueError("Malformed proof line")

    left, right = line.split(':', 1)
    left_parts = left.split()

    if len(left_parts) < 4:
        raise ValueError("Malformed proof line")

    new_id = int(left_parts[0])
    pivot  = int(left_parts[1])
    id1    = int(left_parts[2])
    id2    = int(left_parts[3])

    resolvent_lits = [int(x) for x in right.split() if int(x) != 0]
    resolvent = frozenset(resolvent_lits)

    return new_id, pivot, id1, id2, resolvent


def check_proof(dimacs_file, proof_file):
    _, init_clauses = read_dimacs(dimacs_file)
    clause_db = {}

    for idx, c in enumerate(init_clauses):
        clause_db[idx + 1] = frozenset(c)

    n_initial = len(init_clauses)
    steps_verified = 0
    last_resolvent = None
    last_new_id    = None

    with open(proof_file, 'r', encoding='utf-8') as f:
        for lineno, raw_line in enumerate(f, 1):
            stripped = raw_line.strip()
            if not stripped or stripped.startswith('c') or stripped.startswith('p'):
                continue

            try:
                parsed = parse_proof_line(stripped)
            except ValueError as e:
                return False, "Line %d: %s" % (lineno, e), {}

            if parsed is None:
                continue

            new_id, pivot, id1, id2, resolvent_declared = parsed

            if id1 not in clause_db:
                return False, "Line %d: ID %d missing" % (lineno, id1), {}
            if id2 not in clause_db:
                return False, "Line %d: ID %d missing" % (lineno, id2), {}

            c1 = clause_db[id1]
            c2 = clause_db[id2]

            if -pivot not in c1 or pivot not in c2:
                return False, "Line %d: Invalid pivot" % lineno, {}

            expected_resolvent = (c1 - {-pivot}) | (c2 - {pivot})

            if resolvent_declared != expected_resolvent:
                return False, "Line %d: Resolvent mismatch" % lineno, {}

            clause_db[new_id] = resolvent_declared
            last_resolvent    = resolvent_declared
            last_new_id       = new_id
            steps_verified   += 1

    if last_resolvent is None:
        return False, "Empty proof", {}
    if last_resolvent != frozenset():
        return False, "Proof does not end with empty clause (ID %d)" % last_new_id, {}

    return True, "PROOF VALID", {"n_initial": n_initial, "steps": steps_verified}


def main():
    if len(sys.argv) != 3:
        print("Usage: python proof_checker.py <dimacs_file> <proof_file>")
        sys.exit(1)

    dimacs_file = sys.argv[1]
    proof_file  = sys.argv[2]

    t_start = time.perf_counter()
    valid, message, stats = check_proof(dimacs_file, proof_file)
    t_end   = time.perf_counter()

    if valid:
        print("PROOF VALID (%.4fs)" % (t_end - t_start))
        print("Initial: %d, Steps: %d" % (stats["n_initial"], stats["steps"]))
        sys.exit(0)
    else:
        print("PROOF INVALID: %s" % message)
        sys.exit(1)


if __name__ == "__main__":
    main()
