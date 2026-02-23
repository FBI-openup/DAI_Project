# Read a dimacs file and call the CDCL solver

import argparse
import sys
import os
import time

from cdcl import read_dimacs, CDCL

def main():
    parser = argparse.ArgumentParser(
        description="Run CDCL on a DIMACS file"
    )
    parser.add_argument(
        "input_file",
        help="Path to the DIMACS input file"
    )
    parser.add_argument(
        "--proof", "-p",
        default=None,
        metavar="PROOF_FILE",
        help="Output resolution proof to this file (UNSAT only)"
    )

    args = parser.parse_args()
    if (not os.path.isfile(args.input_file)):
        print("File not found")
        sys.exit(1)

    clauses = read_dimacs(args.input_file)

    t_solve_start = time.perf_counter()
    cdcl = CDCL(clauses, proof_file=args.proof)
    res  = cdcl.solve()
    t_solve_end = time.perf_counter()

    if (res):
        print("SAT")
        cdcl.proof.close()
    else:
        print("UNSAT")
        cdcl.proof.close()
        if args.proof is not None:
            print("Proof written to: %s" % args.proof)

    print("Solver time: %.6fs" % (t_solve_end - t_solve_start))

if __name__ == "__main__":
    main()
