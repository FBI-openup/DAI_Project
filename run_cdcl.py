# Read a dimacs file and call the CDCL solver

import argparse
import sys
import os

from cdcl import read_dimacs, CDCL

def main():
    parser = argparse.ArgumentParser(
        description="Run CDCL on a DIMACS file"
    )
    parser.add_argument(
        "input_file",
        help="Path to the DIMACS input file"
    )

    args = parser.parse_args()
    if (not os.path.isfile(args.input_file)):
        print("File not found")
        sys.exit(1)

    clauses = read_dimacs(args.input_file)
    cdcl = CDCL(clauses)

    res = cdcl.solve()

    if (res):
        print("SAT")
    else:
        print("UNSAT")

if __name__ == "__main__":
    main()
