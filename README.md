# CDCL SAT Solver — Project 1

**Author:** ZHANG Boyuan  
**Course:** CSC_54656 Tutorial 2 / Project 1  
**Date:** February 2026

---

## 📦 Submission Files

| File | Description |
|------|-------------|
| `cdcl.py` | Main CDCL solver + resolution proof production (required) |
| `proof_checker.py` | Independent linear-time proof verifier (Project 1) |
| `test_cdcl.py` | Automated test suite (optional) |
| `proof_example.txt` | Hand-crafted proof format illustration |

---

## 🚀 Quick Start

### Solve a CNF (SAT/UNSAT only)

```bash
python run_cdcl.py prop.cnf
python run_cdcl.py "dimacs/DPLL example2"
python run_cdcl.py dimacs/pigeon-hole/hole6.cnf
```

### Solve + Generate Resolution Proof (Project 1)

```bash
# Generate proof
python run_cdcl.py dimacs/pigeon-hole/hole6.cnf --proof proof_hole6.txt

# Verify proof independently
python proof_checker.py dimacs/pigeon-hole/hole6.cnf proof_hole6.txt
```

### Run All Tests

```bash
python test_cdcl.py            # all files in dimacs/
python test_cdcl.py --verbose  # detailed output
```

---

## 📐 Resolution Proof Format

Each line in the proof file encodes **one resolution step**:

```
p proof <n>
<new_id> <pivot> <id1> <id2> : <lit1> <lit2> ... 0
```

| Field | Meaning |
|-------|---------|
| `n` | Number of initial clauses (IDs `1..n`) |
| `new_id` | ID assigned to the new resolvent clause |
| `pivot` | Literal resolved away: `id1` contains `-pivot`, `id2` contains `+pivot` |
| `id1` | Parent clause containing `-pivot` |
| `id2` | Parent clause containing `+pivot` |
| `lits... 0` | Resolvent literals (just `0` = empty clause = UNSAT witness) |

**Example** — formula `{[1], [-1]}`:

```
p proof 2
3 1 2 1 : 0
```

`id2=1` is `[1]`, `id1=2` is `[-1]`, pivot=`1` → resolvent = `[]` (empty = UNSAT).

### Proof Format Properties

- **Checkable in O(N·K)** time where N = steps, K = max clause size
- No back-references; single linear scan suffices
- Last step must produce the empty clause

---

## 🔧 Implementation Details

### Core Solver (`cdcl.py`)

| Component | Description |
|-----------|-------------|
| `ClauseDb` | Clause storage + proof ID tables (`clause_id`, `content_to_id`) |
| `ProofLogger` | Writes `p proof n` header + one line per resolution step |
| `_NullLogger` | No-op sentinel — zero overhead when proof disabled |
| `CDCL.analyze()` | 1st-UIP conflict analysis + proof step logging |
| `CDCL._proof_resolve_step()` | Central helper: log + resolve + register new clause ID |
| `CDCL._finish_proof_to_empty()` | Derives empty clause from a level-0 BCP conflict |
| `CDCL.learn()` | Registers learned clause in proof ID maps |

**Backward compatibility:** `CDCL(clauses).solve()` works identically to before.  
The `proof_file` kwarg defaults to `None`, making proof production opt-in.

### Data Structures

- **Trail:** `[(literal, reason_clause, decision_level), ...]`
- **Assignments:** `{variable: bool}`
- **`clause_id`:** `{id(list_object): proof_id}` — fast lookup by object identity
- **`content_to_id`:** `{tuple(sorted(lits)): proof_id}` — lookup by clause content

---

## 🧪 Test Results

### Correctness (7/7 pass)

```
Found 7 test files in 'dimacs'
Total tests:  7
Passed:       7
```

### Proof Verification

| Instance | Variables | Clauses | Solver time | Proof steps | Checker time | Result |
|----------|-----------|---------|-------------|-------------|--------------|--------|
| `[1] [-1]` (trivial) | 1 | 2 | <1ms | 1 | <1ms | ✅ VALID |
| `DPLL example2` | 2 | 4 | <1ms | 4 | <1ms | ✅ VALID |
| `hole6.cnf` | 42 | 133 | 0.29s | 5124 | 0.018s | ✅ VALID |

### Pigeon-Hole Problems

| File | Variables | Clauses | Result |
|------|-----------|---------|--------|
| `hole6.cnf` | 42 | 133 | UNSAT ✅ |
| `hole7.cnf` | 56 | 204 | UNSAT ✅ |
| `hole8.cnf` | 72 | 297 | UNSAT ✅ |
| `hole9.cnf` | 90 | 415 | UNSAT* |
| `hole10.cnf` | 110 | 561 | UNSAT* |

*Larger instances may take extended time (unoptimised implementation, acceptable per assignment).

---

## 📋 Assignment Requirements Checklist

### Tutorial 2 (CDCL Solver)

- ✅ Trail & Deduction (BCP)
- ✅ Decision heuristic
- ✅ Conflict analysis (1st-UIP with resolution)
- ✅ Non-chronological backtracking
- ✅ Clause learning
- ✅ Interface: `__init__()` and `solve()` unchanged

### Project 1 (Resolution Proof)

- ✅ Proof generated during conflict analysis
- ✅ Proof format: one resolution step per line
- ✅ Handles level-0 conflicts (trivially UNSAT)
- ✅ Handles 1st-UIP learning → backtrack → level-0 BCP conflict
- ✅ Independent linear-time `proof_checker.py`
- ✅ Verified on `hole6.cnf` (5124 steps, PROOF VALID)
- ✅ `proof_file` kwarg — backward-compatible

---

## 📝 Notes

- Implementation prioritises correctness over efficiency (per assignment instructions)
- All tested cases return correct SAT/UNSAT results
- Proof checker has no imports from `cdcl.py` — fully independent
