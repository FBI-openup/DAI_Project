"""
Proof Checker for CDCL Resolution Proofs
Author: ZHANG Boyuan
Course: CSC_54656 Project 1

Usage:
    python proof_checker.py <dimacs_file> <proof_file>

Algorithm (Linear Time):
    1. Read DIMACS → build initial clause dict {id: frozenset(lits)}
    2. Read proof header → get n (number of initial clauses)
    3. Scan proof line-by-line (one forward pass, no backtracking):
       for each resolution step:
           - retrieve parent clauses by ID (O(1) dict lookup)
           - verify pivot literals are complementary
           - verify the declared resolvent matches the computed one
           - add resolvent to dict
    4. After full scan: verify the last produced clause is the empty clause
    5. Print PROOF VALID or PROOF INVALID + timing

Time complexity: O(n * k) where n = number of proof steps, k = max clause size.
This is linear in the size of the proof (total literal occurrences).

此 checker 完全独立于 cdcl.py，不 import 任何 solver 代码。
线性扫描：每行只读一次，不回溯，满足 linear time 验证要求。
"""

import sys
import time


# ─────────────────────────────────────────────────────────────────────────────
# DIMACS Reader
# ─────────────────────────────────────────────────────────────────────────────

def read_dimacs(filename):
    """Parse a DIMACS CNF file.

    Returns:
        (num_vars, clauses_list)
        clauses_list: list of lists of integers (DIMACS format)
    """
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
            # 子句行：以 0 结尾，解析所有非零整数
            lits = [int(x) for x in line.split() if int(x) != 0]
            if lits:
                clauses.append(lits)
    return num_vars, clauses


# ─────────────────────────────────────────────────────────────────────────────
# Proof Reader & Verifier
# ─────────────────────────────────────────────────────────────────────────────

def parse_proof_line(line):
    """Parse one resolution step line from the proof file.

    Expected format:
        <new_id> <pivot> <id1> <id2> : <lit1> <lit2> ... 0

    Returns:
        (new_id, pivot, id1, id2, resolvent_frozenset)
        or None if the line is a comment / header / blank.

    一行格式：new_id pivot id1 id2 : lit1 lit2 ... 0
    ':'  是分隔符，右边是 resolvent 字面量，0 终止。
    """
    line = line.strip()
    if not line or line.startswith('c') or line.startswith('p'):
        return None  # skip header / comments

    # Split on ':' to separate metadata from resolvent literals
    # 用 ':' 分割左右两部分
    if ':' not in line:
        raise ValueError(f"Malformed proof line (no ':'): {line!r}")

    left, right = line.split(':', 1)
    left_parts = left.split()

    if len(left_parts) < 4:
        raise ValueError(f"Malformed proof line (expected 4 fields before ':'): {line!r}")

    new_id = int(left_parts[0])
    pivot  = int(left_parts[1])
    id1    = int(left_parts[2])
    id2    = int(left_parts[3])

    # Parse resolvent literals (terminated by 0)
    # 解析 resolvent 字面量（0 终止，空子句即 resolvent = {}）
    resolvent_lits = [int(x) for x in right.split() if int(x) != 0]
    resolvent = frozenset(resolvent_lits)

    return new_id, pivot, id1, id2, resolvent


def check_proof(dimacs_file, proof_file):
    """Verify the resolution proof against the DIMACS instance.

    Returns:
        (valid: bool, message: str, stats: dict)

    证明验证主函数：
    - 逐行读取证明文件（线性时间，无回溯）
    - 每步验证：pivot 是否互补、resolvent 是否正确
    - 最终确认推导出了空子句
    """

    # ── Step 1: Load initial clauses ─────────────────────────────────────────
    # 读取 DIMACS 文件，建立初始子句字典 {clause_id: frozenset of literals}
    _, init_clauses = read_dimacs(dimacs_file)
    clause_db = {}  # {int id -> frozenset}

    for idx, c in enumerate(init_clauses):
        clause_db[idx + 1] = frozenset(c)   # IDs start at 1

    n_initial = len(init_clauses)

    # ── Step 2: Scan proof file ──────────────────────────────────────────────
    steps_verified  = 0
    last_resolvent  = None
    last_new_id     = None
    parse_errors    = []

    with open(proof_file, 'r', encoding='utf-8') as f:
        for lineno, raw_line in enumerate(f, 1):
            # Skip blank / comment / header lines
            stripped = raw_line.strip()
            if not stripped or stripped.startswith('c') or stripped.startswith('p'):
                continue

            # Parse the resolution step
            try:
                parsed = parse_proof_line(stripped)
            except ValueError as e:
                return False, f"Line {lineno}: {e}", {}

            if parsed is None:
                continue  # header/comment already handled above

            new_id, pivot, id1, id2, resolvent_declared = parsed

            # ── Lookup parent clauses ─────────────────────────────────────────
            # 按 ID 查找两个父子句（O(1) 字典查询）
            if id1 not in clause_db:
                return False, (
                    f"Line {lineno}: clause ID {id1} not found in database "
                    f"(step new_id={new_id})"
                ), {}
            if id2 not in clause_db:
                return False, (
                    f"Line {lineno}: clause ID {id2} not found in database "
                    f"(step new_id={new_id})"
                ), {}

            c1 = clause_db[id1]
            c2 = clause_db[id2]

            # ── Check 1: Pivot literals are complementary ─────────────────────
            # 验证 pivot 方向：id1 必须包含 -pivot，id2 必须包含 +pivot
            # 这保证了归结操作是合法的（互补字面量存在）
            if -pivot not in c1:
                return False, (
                    f"Line {lineno}: clause id1={id1} {set(c1)} does not contain "
                    f"-pivot={-pivot}  (pivot={pivot})"
                ), {}
            if pivot not in c2:
                return False, (
                    f"Line {lineno}: clause id2={id2} {set(c2)} does not contain "
                    f"+pivot={pivot}"
                ), {}

            # ── Check 2: Resolvent is correct ─────────────────────────────────
            # 计算期望的 resolvent：从 c1 去掉 -pivot，从 c2 去掉 +pivot，取并集
            # expected = (c1 \ {-pivot}) ∪ (c2 \ {pivot})
            expected_resolvent = (c1 - {-pivot}) | (c2 - {pivot})

            if resolvent_declared != expected_resolvent:
                return False, (
                    f"Line {lineno}: resolvent mismatch for new_id={new_id}.\n"
                    f"  Declared : {set(resolvent_declared)}\n"
                    f"  Expected : {set(expected_resolvent)}"
                ), {}

            # ── Register the new clause ───────────────────────────────────────
            # 将新 resolvent 加入字典，供后续步骤引用
            clause_db[new_id] = resolvent_declared
            last_resolvent    = resolvent_declared
            last_new_id       = new_id
            steps_verified   += 1

    # ── Step 3: Confirm empty clause was derived ──────────────────────────────
    # 最终验证：最后一步必须产生空子句（UNSAT 的 witness）
    if last_resolvent is None:
        return False, "Proof file contains no resolution steps.", {}

    if last_resolvent != frozenset():
        return False, (
            f"Proof does not end with the empty clause.\n"
            f"Last step (id={last_new_id}) produced: {set(last_resolvent)}"
        ), {}

    stats = {
        "n_initial_clauses" : n_initial,
        "n_steps_verified"  : steps_verified,
    }
    return True, "All resolution steps verified. Empty clause derived. PROOF VALID.", stats


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 3:
        print("Usage: python proof_checker.py <dimacs_file> <proof_file>")
        sys.exit(1)

    dimacs_file = sys.argv[1]
    proof_file  = sys.argv[2]

    print(f"Checking proof...")
    print(f"  DIMACS : {dimacs_file}")
    print(f"  Proof  : {proof_file}")
    print()

    t_start = time.perf_counter()
    valid, message, stats = check_proof(dimacs_file, proof_file)
    t_end   = time.perf_counter()
    elapsed = t_end - t_start

    if valid:
        print("=" * 60)
        print("PROOF VALID")
        print("=" * 60)
        print(f"  Initial clauses  : {stats.get('n_initial_clauses', '?')}")
        print(f"  Steps verified   : {stats.get('n_steps_verified', '?')}")
        print(f"  Checker time     : {elapsed:.6f}s")
        sys.exit(0)
    else:
        print("=" * 60)
        print("PROOF INVALID")
        print("=" * 60)
        print(f"  Reason : {message}")
        print(f"  Checker time : {elapsed:.6f}s")
        sys.exit(1)


if __name__ == "__main__":
    main()
