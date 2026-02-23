# CDCL SAT Solver -- Project 1

**Author:** ZHANG Boyuan
**Course:** CSC_54656 EP -- Satisfiability and SMT Solving

---

## Files

| File | Description |
|------|-------------|
| `cdcl.py` | CDCL solver with resolution proof production |
| `proof_checker.py` | Independent linear-time proof verifier |
| `run_cdcl.py` | Command-line solver runner |
| `run_experiments.py` | Automated experiment runner (solve + verify + table) |
| `test_cdcl.py` | Unit test suite |
| `proof_example.txt` | Annotated proof format illustration |
| `dimacs/` | Test instances (SAT, UNSAT, pigeon-hole) |

---

## Quick Start

### Solve a CNF

```bash
python run_cdcl.py prop.cnf
python run_cdcl.py "dimacs/DPLL example2"
python run_cdcl.py dimacs/pigeon-hole/hole6.cnf
```

### Generate and Verify a Resolution Proof

```bash
# Solve and write proof
python run_cdcl.py dimacs/pigeon-hole/hole6.cnf --proof proof_hole6.txt

# Verify proof independently
python proof_checker.py dimacs/pigeon-hole/hole6.cnf proof_hole6.txt
```

---

## Running Experiments

`run_experiments.py` automates the full pipeline: solve, generate proof, verify, and print a results table.

```bash
# Basic tests (SAT instances + UNSAT edge cases), fast
python run_experiments.py

# Add pigeon-hole hole6, hole7, hole8
python run_experiments.py --pigeon

# Choose specific hole instances
python run_experiments.py --hole 6 7

# All instances including hole9 and hole10 (slow)
python run_experiments.py --all

# Verify already-generated proof files without re-running solver
python run_experiments.py --check-only
python run_experiments.py --check-only --pigeon

# Delete all generated proof_*.txt files (proof_example.txt is preserved)
python run_experiments.py --clean
```

---

## Running Unit Tests

```bash
python test_cdcl.py           # all files in dimacs/
python test_cdcl.py --verbose # detailed output per instance
```

---

## Proof Format

Each proof file starts with a header and then one resolution step per line:

```
p proof <n>
<new_id> <pivot> <id1> <id2> : <lit1> <lit2> ... 0
```

| Field | Meaning |
|-------|---------|
| `n` | Number of initial clauses (IDs 1..n) |
| `new_id` | ID assigned to the new resolvent |
| `pivot` | Resolved literal: `id1` contains `-pivot`, `id2` contains `+pivot` |
| `id1`, `id2` | Parent clause IDs |
| `lits... 0` | Resolvent literals; bare `0` = empty clause (UNSAT witness) |

See `proof_example.txt` for an annotated worked example.

---

## Implementation Notes

- `CDCL(clauses).solve()` is unchanged from Tutorial 2 (backward compatible).
- Pass `proof_file="path.txt"` to enable proof production.
- `proof_checker.py` has no imports from `cdcl.py` -- fully independent.
- The solver uses a `_NullLogger` when proof production is off, so there are no conditional branches in the main loop.

---

## Requirements Checklist

### Tutorial 2 (CDCL Solver)

- [x] BCP (Boolean Constraint Propagation)
- [x] Decision heuristic
- [x] 1st-UIP conflict analysis with resolution
- [x] Non-chronological backtracking
- [x] Clause learning
- [x] Interface unchanged: `__init__()` and `solve()`

### Project 1 (Resolution Proof)

- [x] Proof recorded during conflict analysis
- [x] One resolution step per line, terminated by 0
- [x] Level-0 conflict handled (`border_level0.cnf`)
- [x] End-of-proof derivation to empty clause via `_finish_proof_to_empty`
- [x] Independent linear-time `proof_checker.py`
- [x] Verified on hole6 (5124 steps), hole7 (18206), hole8 (61077)
- [x] Backward-compatible `proof_file` kwarg
