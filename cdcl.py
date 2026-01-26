"""
CDCL SAT Solver Implementation
Author: ZHANG Boyuan
Submission includes:
    cdcl.py (main implementation - required for submission)
    test_cdcl.py (automated test suite - optional)

For complete project files and testing documentation, see:
https://github.com/FBI-openup/DAI-TD2-3.git

For usage and testing instructions, see README.md

You should keep the interface of the constructor of the CDCL class and the 
method solve() in CDCL unchanged.
"""

import logging

# Create a logger for this module
logger = logging.getLogger(__name__)

class CDCL:
    """ Assume the input is as follows:

    A list of clauses, each clause is a list of literals, each literal an integer, either positive or negative.

    All variables are named 1..n, a positive number is a positive literal, a negative number is a negative literal.
    """

    def __init__(self, clauses):
        self.num_vars = 0
        for c in clauses:
            for i in c:
                if abs(i) > self.num_vars:
                    self.num_vars = abs(i)

        self.clauses = ClauseDb(self.num_vars, clauses)

        # Store the trail of assignments
        # Each element should be (lit, reason), with lit a literal 
        # and reason either None (for decisions) or a clause (for deductions)
        #
        # You will also need to store the decision level (either in the trail
        # directly or in another field)
        self.trail = [] # the trail of assignments list[Tuple[lit:int, reason:Clause, desision_level:int]]

        # Current decision level
        self.decision_level = 0

        # Map of current VARIABLE assignment, useful to evaluate a clause
        # Either contains a variable assigned to true or false, or does not when
        # the variable is unassigned
        # Should be kept in sync with decisions and deductions.
        self.assignments = {} # the dict of assignments {int: bool }


    def solve(self):
        """
        Main CDCL loop.

        Returns true if satisfiable, false if unsatisfiable
        """

        logging.info("CDCL Search started")
        while (True):
            # MODIFIED: deduce() now returns None or conflicting clause
            conflicting_clause = self.deduce()
            
            if conflicting_clause is None:  # MODIFIED: check if no conflict
                if (self.all_assigned()):  # MODIFIED: fixed from self.trail.all_assigned()
                    logging.info("All literals assigned, SAT")
                    return True
                else:
                    self.decide()
            else:  # MODIFIED: conflict detected and returned
                level, learned_clause = self.analyze(conflicting_clause) 
                if (level == 0):
                    return False
                else:
                    self.backtrack(level)
                    self.learn(learned_clause) 
                    
    def is_unit_clause(self, clause):
        """
        check if a clause is a unit clause
        return: (status, literal)
        - ("satisfied", None): SAT
        - ("unit", lit): unit clause, lit is the only unassigned literal
        - ("conflict", None): conflict (all literals are false)
        - ("normal", None): normal clause (multiple unassigned literals)
        """
        unassigned = []
        
        for lit in clause:
            var = abs(lit)  # index of var
            if var in self.assignments: 
                var_value = self.assignments[var]  # (True/False)
                lit_value = var_value if lit > 0 else not var_value
                
                if lit_value:  
                    return ("satisfied", None)  
            else:  
                unassigned.append(lit)
        
        # Checked all literals
        if len(unassigned) == 0:
            return ("conflict", None)  # conflict
        elif len(unassigned) == 1:
            return ("unit", unassigned[0])  # unit clause
        else:
            return ("normal", None) 
    #TODO
    def deduce(self):
        """
        Implement Boolean Constraint Propagation (BCP).

        MODIFIED: Returns None if no conflict, otherwise returns the conflicting clause.
        """
        logging.info("Deduce")
        while True:
            found_unit = False
            for c in self.clauses.clauses:
                status, lit = self.is_unit_clause(c)
                if status == "conflict":
                    logging.info(f"Conflict detected in clause {c}")
                    return c  # MODIFIED: return conflicting clause instead of False
                elif status == "unit":
                    # unit propagation
                    var = abs(lit)
                    value = (lit > 0)
                    
                    logging.info(f"Unit propagation: {lit} from clause {c}")
                
                    self.assignments[var] = value
                    self.trail.append((lit, c, self.decision_level))
                
                    found_unit = True
                    break  
        
            if not found_unit:
                return None  # MODIFIED: return None instead of True  
        
    def all_assigned(self):
        """
        Returns true if all the literals have been assigned (you can use the self.assignments map)
        """
        return len(self.assignments) == self.num_vars
    
    #TODO
    def decide(self):
        """
        Select a new unassigned literal.

        Must update the trail, variable assignments, and decision level accordingly.
        """
        logging.info("Decide a new variable assignment")
        
        self.decision_level += 1
        
        # find a lit unassigned
        for var in range(1, self.num_vars + 1):
            if var not in self.assignments:
                lit = var  #decide positive literal = true
                
                logging.info(f"Decision: variable {var} = True at level {self.decision_level}")
                
                # update assignments and trail
                self.assignments[var] = True
                self.trail.append((lit, None, self.decision_level))  # reason=None means decided
                return
        # A secure print
        logging.warning("decide() called but all variables assigned,check solve() should have all assigned check")
    
    def resolve(self, clause1, clause2, lit):
        """
        Resolute 2 clauses
        clause1 contains -lit, clause2 contains lit
        return resoluted clause
        """
        result = []
        
        # add all literals from clause1 except -lit
        for l in clause1:
            if l != -lit:
                result.append(l)
        
        # add all literals from clause2 except lit (remove duplicates)
        for l in clause2:
            if l != lit and l not in result:
                result.append(l)
        
        return result
    
    #TODO
    def analyze(self, conflicting_clause):
        """
        Analyze the conflicting_clause using the trail.

        Returns the new level to backtrack to and a conflict clause.
        """
        logging.info("Conflict analysis")
        
        if self.decision_level == 0:
            # Conflict at decision level 0 → UNSAT
            return 0, conflicting_clause
        
        # Build mapping (traverse trail only once)
        lit_to_level = {}
        for trail_lit, reason, level in self.trail:
            lit_to_level[trail_lit] = level
            lit_to_level[-trail_lit] = level
        
        conflict = list(conflicting_clause)
        
        # Count literals at current decision level
        current_level_count = sum(1 for lit in conflict 
                                 if lit_to_level.get(lit, 0) == self.decision_level)
        
        # Backward traversal for resolution
        i = len(self.trail) - 1
        while current_level_count > 1:
            lit, reason, level = self.trail[i]
            
            if -lit in conflict and reason is not None:
                # Use resolve() helper function
                conflict = self.resolve(conflict, reason, lit)
                
                # Recount literals at current level
                current_level_count = sum(1 for l in conflict 
                                         if lit_to_level.get(l, 0) == self.decision_level)
            
            i -= 1
        
        # Calculate backtrack level (second highest level in conflict)
        levels = [lit_to_level.get(lit, 0) for lit in conflict]
        levels.sort(reverse=True)
        backtrack_level = levels[1] if len(levels) > 1 else 0
        
        logging.info(f"Learned clause: {conflict}, backtrack to level {backtrack_level}")
        return backtrack_level, conflict

    #TODO
    def backtrack(self,level):
        """
        Undo the trail, assignments, and decision levels.

        Does not return a value.
        """
        while len(self.trail) > 0:
            lit, reason, dec_level = self.trail[-1]
            
            if dec_level <= level:
                break  #skip the lit satisfies
            # delete assignments
            var = abs(lit)
            del self.assignments[var]
            # delete trail tail (-1)
            self.trail.pop()# equal to pop(-1)
        self.decision_level = level

    #TODO
    def learn(self, clause):
        """
        Add a new clause to the set of clauses.

        Does not return a value.
        """
        logging.info(f"Learning a new clause: {clause}")
        # MODIFIED: self.clauses is ClauseDb object, need to access .clauses list
        self.clauses.clauses.append(clause)

class ClauseDb:
    """
    Store the set of clauses Implement 2-watched literals
    """
    def __init__(self, num_vars, clauses):
        self.clauses = clauses
        # you may want to store the unit clauses
        # and use them only at decision level 0
        self.unit = [] 

        # Map from literal to the clauses containing it
        # This is just a suggestion, you can change this data structure as you wish.
        self.lit2clauses = {}


def read_dimacs(filename):
    """
    Read a DIMACS CNF file and return the list of clauses.
    """
    clauses = []

    num_vars = 0
    num_clauses = 0

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                if len(parts) >= 4 and parts[1] == 'cnf':
                    num_vars = int(parts[2])
                    num_clauses = int(parts[3])
                    continue
                else:
                    raise Exception("Malformed header %s" % line)

            # Parse clause line
            literals = []
            for x in line.split():
                lit = int(x)
                if lit != 0:
                    literals.append(lit)

            clauses.append(literals)

    return clauses
