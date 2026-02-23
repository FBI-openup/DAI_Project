"""
Proof Checker for CDCL Resolution Proofs
Author: ZHANG Boyuan
Course: CSC_54656 Project 1

本程序用于独立验证 CDCL 求解器生成的归结证明。
它读取原始 DIMACS 文件和证明文件，通过单次前向扫描验证每一步归结的正确性。

算法思想:
    1. 读取 DIMACS：建立初始子句池。
    2. 逐行读取证明：
        - 验证父子句 ID 是否存在。
        - 验证消解文字（pivot）是否在父子句中以相反符号出现。
        - 计算归结结果，并与证明中声明的结果对比。
        - 将结果加入子句池。
    3. 验证最后一步：检查最后生成的子句是否为空子句（UNSAT 证人）。
"""

import sys
import time


def read_dimacs(filename):
    """ 读取 DIMACS 文件并返回子句列表 """
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
            # 解析数字直到 0
            lits = [int(x) for x in line.split() if int(x) != 0]
            if lits:
                clauses.append(lits)
    return num_vars, clauses


def parse_proof_line(line):
    """
    解析证明中的一行。格式: <new_id> <pivot> <id1> <id2> : <lit1> <lit2> ... 0
    """
    line = line.strip()
    if not line or line.startswith('c') or line.startswith('p'):
        return None

    if ':' not in line:
        raise ValueError("Malformed proof line (no ':'): %r" % line)

    left, right = line.split(':', 1)
    left_parts = left.split()

    if len(left_parts) < 4:
        raise ValueError("Malformed proof line (expected 4 fields before ':'): %r" % line)

    new_id = int(left_parts[0])
    pivot  = int(left_parts[1])
    id1    = int(left_parts[2])
    id2    = int(left_parts[3])

    resolvent_lits = [int(x) for x in right.split() if int(x) != 0]
    resolvent = frozenset(resolvent_lits)

    return new_id, pivot, id1, id2, resolvent


def check_proof(dimacs_file, proof_file):
    """
    核心校验逻辑。Linear-time O(N*K)
    """
    _, init_clauses = read_dimacs(dimacs_file)
    clause_db = {}

    # 初始化 ID 映射
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

            # 1. 检查父子句是否存在
            if id1 not in clause_db:
                return False, "Line %d: clause ID %d not found" % (lineno, id1), {}
            if id2 not in clause_db:
                return False, "Line %d: clause ID %d not found" % (lineno, id2), {}

            c1 = clause_db[id1]
            c2 = clause_db[id2]

            # 2. 检查 pivot 是否合法 (id1 包含 -pivot, id2 包含 +pivot)
            if -pivot not in c1:
                return False, "Line %d: id1=%d does not contain -pivot=%d" % (lineno, id1, -pivot), {}
            if pivot not in c2:
                return False, "Line %d: id2=%d does not contain +pivot=%d" % (lineno, id2, pivot), {}

            # 3. 计算归结结果并比对
            expected_resolvent = (c1 - {-pivot}) | (c2 - {pivot})

            if resolvent_declared != expected_resolvent:
                return False, (
                    "Line %d: resolvent mismatch.\n"
                    "  Declared : %s\n"
                    "  Expected : %s" % (lineno, set(resolvent_declared), set(expected_resolvent))
                ), {}

            # 4. 存入库中
            clause_db[new_id] = resolvent_declared
            last_resolvent    = resolvent_declared
            last_new_id       = new_id
            steps_verified   += 1

    if last_resolvent is None:
        return False, "Proof file contains no resolution steps.", {}

    # 5. 二次检查最后是否推导出了空子句
    if last_resolvent != frozenset():
        return False, (
            "Proof does not end with the empty clause.\n"
            "Last step (id=%d) produced: %s" % (last_new_id, set(last_resolvent))
        ), {}

    stats = {
        "n_initial_clauses" : n_initial,
        "n_steps_verified"  : steps_verified,
    }
    return True, "PROOF VALID.", stats


def main():
    if len(sys.argv) != 3:
        print("Usage: python proof_checker.py <dimacs_file> <proof_file>")
        sys.exit(1)

    dimacs_file = sys.argv[1]
    proof_file  = sys.argv[2]

    print("Checking proof...")
    print("  DIMACS : %s" % dimacs_file)
    print("  Proof  : %s" % proof_file)
    print()

    t_start = time.perf_counter()
    valid, message, stats = check_proof(dimacs_file, proof_file)
    t_end   = time.perf_counter()
    elapsed = t_end - t_start

    if valid:
        print("=" * 60)
        print("PROOF VALID")
        print("=" * 60)
        print("  Initial clauses  : %s" % stats.get("n_initial_clauses", "?"))
        print("  Steps verified   : %s" % stats.get("n_steps_verified", "?"))
        print("  Checker time     : %.6fs" % elapsed)
        sys.exit(0)
    else:
        print("=" * 60)
        print("PROOF INVALID")
        print("=" * 60)
        print("  Reason : %s" % message)
        print("  Checker time : %.6fs" % elapsed)
        sys.exit(1)


if __name__ == "__main__":
    main()
