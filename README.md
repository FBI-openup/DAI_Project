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
| `test_cdcl.py` | Automated experiment runner: solve, verify, and print results table |
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

`test_cdcl.py` automates the full pipeline: solve, generate proof, verify, and print a results table.

```bash
# Basic tests (SAT instances + UNSAT edge cases, 9 instances)
python test_cdcl.py

# Add pigeon-hole hole6, hole7, hole8
python test_cdcl.py --pigeon

# Choose specific hole instances
python test_cdcl.py --hole 6 7

# Exactly the 12 instances from Table 1 in the report
python test_cdcl.py --all12

# All instances including hole9 and hole10 (slow)
python test_cdcl.py --all

# Verify already-generated proof files without re-running solver
python test_cdcl.py --check-only

# Delete all generated proof_*.txt files (proof_example.txt is preserved)
python test_cdcl.py --clean
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

- `CDCL(clauses).solve()` is unchanged from Tutorial 2.
- Pass `proof_file="path.txt"` to enable proof production.
- `proof_checker.py` has no imports from `cdcl.py`: fully independent.
- The solver uses a `_NullLogger` when proof production is off, avoiding conditional branches in the main loop.
- The `clean` branch contains minimal comments (original handout comments only for existing files).
