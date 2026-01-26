"""
Automated test suite for CDCL SAT solver

Usage:
    python test_cdcl.py              # Run all tests
    python test_cdcl.py --verbose    # Show detailed output
    python test_cdcl.py --timeout 5  # Set timeout (default: 10 seconds)
"""

import os
import sys
import time
import argparse
from cdcl import read_dimacs, CDCL

# Optional: Define expected results for known test cases
# Format: {filename: expected_result}
# Set to None if you don't know the expected result
EXPECTED_RESULTS = {
    'DPLL example2': 'UNSAT',
    'simple.cnf': 'SAT',
    'single_literal.cnf': 'SAT',
    # Additional test files (manually verified by analyzing CNF logic)
    # All verified to be satisfiable with simple variable assignments
    'empty_lines.cnf': 'SAT',
    'large.cnf': 'SAT',
    'multiline.cnf': 'SAT',
    'with_comments.cnf': 'SAT',
}

class TestResult:
    """Store test result information"""
    def __init__(self, filename):
        self.filename = filename
        self.result = None  # 'SAT', 'UNSAT', or None
        self.expected = EXPECTED_RESULTS.get(filename)
        self.passed = None  # True/False/None
        self.runtime = 0
        self.error = None
    
    def check_pass(self):
        """Check if test passed (if expected result is known)"""
        if self.expected is None:
            self.passed = None  # Unknown expected result
        elif self.error:
            self.passed = False
        else:
            self.passed = (self.result == self.expected)


def run_test(filepath, timeout=10, verbose=False):
    """
    Run a single test case
    
    Args:
        filepath: Path to the DIMACS file
        timeout: Maximum time allowed (not implemented yet)
        verbose: Print detailed output
    
    Returns:
        TestResult object
    """
    filename = os.path.basename(filepath)
    result = TestResult(filename)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Testing: {filename}")
        print(f"{'='*60}")
    
    try:
        # Read and solve
        start_time = time.time()
        clauses = read_dimacs(filepath)
        cdcl = CDCL(clauses)
        sat = cdcl.solve()
        end_time = time.time()
        
        result.runtime = end_time - start_time
        result.result = 'SAT' if sat else 'UNSAT'
        
        if verbose:
            print(f"Result: {result.result}")
            print(f"Runtime: {result.runtime:.4f}s")
        
    except Exception as e:
        result.error = str(e)
        if verbose:
            print(f"ERROR: {e}")
    
    result.check_pass()
    return result


def print_summary(results, verbose=False):
    """Print test summary"""
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    total = len(results)
    passed = sum(1 for r in results if r.passed is True)
    failed = sum(1 for r in results if r.passed is False)
    unknown = sum(1 for r in results if r.passed is None)
    errors = sum(1 for r in results if r.error is not None)
    
    # Print individual results
    print(f"\n{'File':<25} {'Result':<8} {'Expected':<8} {'Status':<10} {'Time':<8}")
    print(f"{'-'*70}")
    
    for r in results:
        status = "[PASS]" if r.passed is True else "[FAIL]" if r.passed is False else "[UNK]"
        expected_str = r.expected if r.expected else "N/A"
        result_str = r.result if r.result else "ERROR"
        
        print(f"{r.filename:<25} {result_str:<8} {expected_str:<8} {status:<10} {r.runtime:.4f}s")
    
    # Print statistics
    print(f"\n{'-'*70}")
    print(f"Total tests:     {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Unknown:         {unknown}")
    print(f"Errors:          {errors}")
    
    if total > 0:
        if unknown == total:
            print(f"\nNote: All tests have unknown expected results")
            print(f"Pass rate: N/A (no expected results defined)")
        else:
            known_tests = passed + failed
            pass_rate = (passed / known_tests * 100) if known_tests > 0 else 0
            print(f"Pass rate:       {pass_rate:.1f}% ({passed}/{known_tests} tests with known results)")
    
    # Print failed tests details
    if failed > 0:
        print(f"\n{'='*70}")
        print("FAILED TESTS:")
        print(f"{'='*70}")
        for r in results:
            if r.passed is False:
                print(f"\n{r.filename}:")
                print(f"  Expected: {r.expected}")
                print(f"  Got:      {r.result if r.result else 'ERROR'}")
                if r.error:
                    print(f"  Error:    {r.error}")
    
    print(f"\n{'='*70}\n")


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Test CDCL SAT solver')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output for each test')
    parser.add_argument('--timeout', '-t', type=int, default=10,
                       help='Timeout per test in seconds (default: 10)')
    parser.add_argument('--dir', '-d', type=str, default='dimacs',
                       help='Directory containing test files (default: dimacs)')
    
    args = parser.parse_args()
    
    # Find all test files
    dimacs_dir = args.dir
    if not os.path.isdir(dimacs_dir):
        print(f"Error: Directory '{dimacs_dir}' not found!")
        sys.exit(1)
    
    test_files = []
    for filename in os.listdir(dimacs_dir):
        filepath = os.path.join(dimacs_dir, filename)
        if os.path.isfile(filepath):
            test_files.append(filepath)
    
    if not test_files:
        print(f"No test files found in '{dimacs_dir}'")
        sys.exit(1)
    
    test_files.sort()  # Sort for consistent order
    
    print(f"Found {len(test_files)} test files in '{dimacs_dir}'")
    print(f"Running tests...")
    
    # Run all tests
    results = []
    for i, filepath in enumerate(test_files, 1):
        if not args.verbose:
            # Show progress
            filename = os.path.basename(filepath)
            print(f"[{i}/{len(test_files)}] Testing {filename}...", end=' ')
            sys.stdout.flush()
        
        result = run_test(filepath, timeout=args.timeout, verbose=args.verbose)
        results.append(result)
        
        if not args.verbose:
            status = "[OK]" if result.passed is True else "[X]" if result.passed is False else "[?]"
            print(f"{status} {result.result if result.result else 'ERROR'}")
    
    # Print summary
    print_summary(results, verbose=args.verbose)
    
    # Exit with non-zero code if any tests failed
    failed_count = sum(1 for r in results if r.passed is False)
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
