import sys
import puzz
import pdqpq

GOAL_STATE = puzz.EightPuzzleBoard("012345678")


def solve_puzzle(start_state, flavor):
    """Perform a search to find a solution to a puzzle.
    
    Args:
        start_state (EightPuzzleBoard): the start state for the search
        flavor (str): tag that indicate which type of search to run.  Can be one of the following:
            'bfs' - breadth-first search
            'ucost' - uniform-cost search
            'greedy-h1' - Greedy best-first search using a misplaced tile count heuristic
            'greedy-h2' - Greedy best-first search using a Manhattan distance heuristic
            'greedy-h3' - Greedy best-first search using a weighted Manhattan distance heuristic
            'astar-h1' - A* search using a misplaced tile count heuristic
            'astar-h2' - A* search using a Manhattan distance heuristic
            'astar-h3' - A* search using a weighted Manhattan distance heuristic
    
    Returns: 
        A dictionary containing describing the search performed, containing the following entries:
        'path' - list of 2-tuples representing the path from the start to the goal state (both 
            included).  Each entry is a (str, EightPuzzleBoard) pair indicating the move and 
            resulting successor state for each action.  Omitted if the search fails.
        'path_cost' - the total cost of the path, taking into account the costs associated with 
            each state transition.  Omitted if the search fails.
        'frontier_count' - the number of unique states added to the search frontier at any point 
            during the search.
        'expanded_count' - the number of unique states removed from the frontier and expanded 
            (successors generated)

    """
    if flavor.find('-') > -1:
        strat, heur = flavor.split('-')
    else:
        strat, heur = flavor, None

    if strat == 'bfs':
        return BreadthFirstSolver().solve(start_state)
    elif strat == 'ucost':
        return UniformCostSolver().solve(start_state)
    elif strat == 'greedy':
        return GreedySolver(heur).solve(start_state)
    elif strat == 'astar':
        return AstarSolver(heur).solve(start_state)
    else:
        raise ValueError("Unknown search flavor '{}'".format(flavor))


class BreadthFirstSolver:
    """Implementation of Breadth-First Search based puzzle solver"""

    def __init__(self):
        self.goal = GOAL_STATE
        self.parents = {}  # state -> parent_state
        self.frontier = pdqpq.FifoQueue()
        self.explored = set()
        self.frontier_count = 0  # increment when we add something to frontier
        self.expanded_count = 0  # increment when we pull something off frontier and expand
    
    def solve(self, start_state):
        """Carry out the search for a solution path to the goal state.
        
        Args:
            start_state (EightPuzzleBoard): start state for the search 
        
        Returns:
            A dictionary describing the search from the start state to the goal state.

        """
        self.parents[start_state] = None
        self.add_to_frontier(start_state)

        if start_state == self.goal:  # edge case        
            return self.get_results_dict(start_state)

        while not self.frontier.is_empty():
            node = self.frontier.pop()  # get the next node in the frontier queue
            succs = self.expand_node(node)

            for move, succ in succs.items():
                if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node

                    # BFS checks for goal state _before_ adding to frontier
                    if succ == self.goal:
                        self.add_to_frontier(succ)
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ)

        # if we get here, the search failed
        return self.get_results_dict(None) 

    def add_to_frontier(self, node):
        """Add state to frontier and increase the frontier count."""
        self.frontier.add(node)
        self.frontier_count += 1

    def expand_node(self, node):
        """Get the next state from the frontier and increase the expanded count."""
        self.explored.add(node)
        self.expanded_count += 1
        return node.successors()

    def get_results_dict(self, state):
        """Construct the output dictionary for solve_puzzle()
        
        Args:
            state (EightPuzzleBoard): final state in the search tree
        
        Returns:
            A dictionary describing the search performed (see solve_puzzle())

        """
        results = {}
        results['frontier_count'] = self.frontier_count
        results['expanded_count'] = self.expanded_count
        if state:
            results['path_cost'] = self.get_cost(state)
            path = self.get_path(state)
            moves = ['start'] + [ path[i-1].get_move(path[i]) for i in range(1, len(path)) ]
            results['path'] = list(zip(moves, path))
        return results

    def get_path(self, state):
        """Return the solution path from the start state of the search to a target.
        
        Results are obtained by retracing the path backwards through the parent tree to the start
        state for the serach at the root.
        
        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            A list of EightPuzzleBoard objects representing the path from the start state to the
            target state

        """
        path = []
        while state is not None:
            path.append(state)
            state = self.parents[state]
        path.reverse()
        return path

    def get_cost(self, state): 
        """Calculate the path cost from start state to a target state.
        
        Transition costs between states are equal to the square of the number on the tile that 
        was moved. 

        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            Integer indicating the cost of the solution path

        """
        cost = 0
        path = self.get_path(state)
        for i in range(1, len(path)):
            x, y = path[i-1].find(None)  # the most recently moved tile leaves the blank behind
            tile = path[i].get_tile(x, y)        
            cost += int(tile)**2
        return cost


class UniformCostSolver:
    """Implementation of Breadth-First Search based puzzle solver"""

    def __init__(self):
        self.goal = GOAL_STATE
        self.parents = {}  # state -> parent_state
        self.frontier = pdqpq.PriorityQueue()
        self.explored = set()
        self.frontier_count = 0  # increment when we add something to frontier
        self.expanded_count = 0  # increment when we pull something off frontier and expand
    
    def solve(self, start_state):
        """Carry out the search for a solution path to the goal state.
        
        Args:
            start_state (EightPuzzleBoard): start state for the search 
        
        Returns:
            A dictionary describing the search from the start state to the goal state.

        """
        self.parents[start_state] = None
        self.add_to_frontier(start_state, 0)

        while not self.frontier.is_empty():
            node = self.frontier.pop()  # get the next node in the frontier queue

            if node == self.goal:  # edge case        
                return self.get_results_dict(start_state)

            succs = self.expand_node(node)

            for move, succ in succs.items():

                if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 

                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ))

                elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.get_cost(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ,self.get_cost(succ))
                    else:
                        self.parents[succ] = old_parent
                
# if succ in frontier:
# store a reference to the current parent
# change the parent to node
# check if the cost of the stored reference is > this change
#      if yes: add succ to the frontier with new cost
#   otherwise: change the parent back to original reference
                            
                # elif (succ in self.frontier) and (self.frontier.get(succ) > self.get_cost(succ)):

                #     self.parents[succ] = node
                    
                #     self.frontier.add(succ,self.get_cost(succ))

        # if we get here, the search failed
        return self.get_results_dict(None) 

    def add_to_frontier(self, node, priority):
        """Add state to frontier and increase the frontier count."""
        self.frontier.add(node, priority)
        self.frontier_count += 1

    def expand_node(self, node):
        """Get the next state from the frontier and increase the expanded count."""
        self.explored.add(node)
        self.expanded_count += 1
        return node.successors()

    def get_results_dict(self, state):
        """Construct the output dictionary for solve_puzzle()
        
        Args:
            state (EightPuzzleBoard): final state in the search tree
        
        Returns:
            A dictionary describing the search performed (see solve_puzzle())

        """
        results = {}
        results['frontier_count'] = self.frontier_count
        results['expanded_count'] = self.expanded_count
        if state:
            results['path_cost'] = self.get_cost(state)
            path = self.get_path(state)
            moves = ['start'] + [ path[i-1].get_move(path[i]) for i in range(1, len(path)) ]
            results['path'] = list(zip(moves, path))
        return results

    def get_path(self, state):
        """Return the solution path from the start state of the search to a target.
        
        Results are obtained by retracing the path backwards through the parent tree to the start
        state for the serach at the root.
        
        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            A list of EightPuzzleBoard objects representing the path from the start state to the
            target state

        """
        path = []
        while state is not None:
            path.append(state)
            state = self.parents[state]
        path.reverse()
        return path

    def get_cost(self, state): 
        """Calculate the path cost from start state to a target state.
        
        Transition costs between states are equal to the square of the number on the tile that 
        was moved. 

        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            Integer indicating the cost of the solution path

        """
        cost = 0
        path = self.get_path(state)
        #print(path)
        for i in range(1, len(path)):
            x, y = path[i-1].find(None)  # the most recently moved tile leaves the blank behind
            tile = path[i].get_tile(x, y)        
            cost += int(tile)**2
        return cost


class GreedySolver:
    """Implementation of Breadth-First Search based puzzle solver"""

    def __init__(self,heur):
        self.goal = GOAL_STATE
        self.parents = {}  # state -> parent_state
        self.frontier = pdqpq.PriorityQueue()
        self.explored = set()
        self.frontier_count = 0  # increment when we add something to frontier
        self.expanded_count = 0  # increment when we pull something off frontier and expand
        self.heur = heur
    
    def solve(self, start_state):
        """Carry out the search for a solution path to the goal state.
        
        Args:
            start_state (EightPuzzleBoard): start state for the search 
        
        Returns:
            A dictionary describing the search from the start state to the goal state.

        """

        self.parents[start_state] = None
        self.add_to_frontier(start_state, 0)

        while not self.frontier.is_empty():
            node = self.frontier.pop()  # get the next node in the frontier queue

            if node == self.goal:  # edge case        
                return self.get_results_dict(start_state)

            succs = self.expand_node(node)

            if (self.heur == 'h1'):
                for move, succ in succs.items():

                  if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 

                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h1(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h1(succ))
                
                  elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.h1(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ, self.h1(succ))
                    else:
                        self.parents[succ] = old_parent            
            elif (self.heur == 'h2'):
                 for move, succ in succs.items():

                  if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 

                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h2(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h2(succ))
                
                  elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.h2(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ, self.h2(succ))
                    else:
                        self.parents[succ] = old_parent
            elif (self.heur == 'h3'):
                for move, succ in succs.items():

                  if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 

                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h3(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h3(succ))
                
                  elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.h3(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ, self.h3(succ))
                    else:
                        self.parents[succ] = old_parent

                # elif (succ in self.frontier) and (self.frontier.get(succ) > self.h3(succ)):
                #     self.frontier.remove(succ)
                #     self.frontier.add(succ,self.h3(succ))

        # if we get here, the search failed
        return self.get_results_dict(None) 

    def add_to_frontier(self, node, priority):
        """Add state to frontier and increase the frontier count."""
        self.frontier.add(node, priority)
        self.frontier_count += 1

    def expand_node(self, node):
        """Get the next state from the frontier and increase the expanded count."""
        self.explored.add(node)
        self.expanded_count += 1
        return node.successors()

    def get_results_dict(self, state):
        """Construct the output dictionary for solve_puzzle()
        
        Args:
            state (EightPuzzleBoard): final state in the search tree
        
        Returns:
            A dictionary describing the search performed (see solve_puzzle())

        """
        results = {}
        results['frontier_count'] = self.frontier_count
        results['expanded_count'] = self.expanded_count
        if state:
            results['path_cost'] = self.get_cost(state)
            path = self.get_path(state)
            moves = ['start'] + [ path[i-1].get_move(path[i]) for i in range(1, len(path)) ]
            results['path'] = list(zip(moves, path))
        return results

    def get_path(self, state):
        """Return the solution path from the start state of the search to a target.
        
        Results are obtained by retracing the path backwards through the parent tree to the start
        state for the serach at the root.
        
        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            A list of EightPuzzleBoard objects representing the path from the start state to the
            target state

        """
        path = []
        while state is not None:
            path.append(state)
            state = self.parents[state]
        path.reverse()
        return path

    def get_cost(self, state): 
        """Calculate the path cost from start state to a target state.
        
        Transition costs between states are equal to the square of the number on the tile that 
        was moved. 

        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            Integer indicating the cost of the solution path

        """
        cost = 0
        path = self.get_path(state)
        for i in range(1, len(path)):
            x, y = path[i-1].find(None)  # the most recently moved tile leaves the blank behind
            tile = path[i].get_tile(x, y)        
            cost += int(tile)**2
        return cost

    def h1(self, state):
        cost = 0
        path = self.get_path(state)
        
        for i in range(1,9):
            if (self.goal.__str__()[i]!=path[len(path)-1].__str__()[i]):
                cost += 1
        
        return cost

    def h2(self, state):
        cost = 0
        path = self.get_path(state)

        for i in range(1,9):
            if (self.goal.__str__()[i]!=path[len(path)-1].__str__()[i]):
                x,y = path[len(path)-1].find(str(i))
                a,b = self.goal.find(str(i))
                cost += (abs(a-x) + abs(b-y))
        return cost

    def h3(self, state):
        cost = 0
        path = self.get_path(state)

        for i in range(1,9):
            if (self.goal.__str__()[i]!=path[len(path)-1].__str__()[i]):
                x,y = path[len(path)-1].find(str(i))
                a,b = self.goal.find(str(i))
                tile = path[len(path)-1].get_tile(x, y) 
                cost += int(tile)**2*(abs(a-x) + abs(b-y))

        return cost


class AstarSolver:
    """Implementation of Breadth-First Search based puzzle solver"""

    def __init__(self,heur):
        self.goal = GOAL_STATE
        self.parents = {}  # state -> parent_state
        self.frontier = pdqpq.PriorityQueue()
        self.explored = set()
        self.frontier_count = 0  # increment when we add something to frontier
        self.expanded_count = 0  # increment when we pull something off frontier and expand
        self.heur = heur
    
    def solve(self, start_state):
        """Carry out the search for a solution path to the goal state.
        
        Args:
            start_state (EightPuzzleBoard): start state for the search 
        
        Returns:
            A dictionary describing the search from the start state to the goal state.

        """

        self.parents[start_state] = None
        self.add_to_frontier(start_state, 0)

        while not self.frontier.is_empty():
            
            node = self.frontier.pop()  # get the next node in the frontier queue

            if node == self.goal:  # edge case        
                return self.get_results_dict(start_state)

            succs = self.expand_node(node)

            if (self.heur == 'h1'):
                for move, succ in succs.items():

                  if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 
                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h1(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h1(succ))
                
                  elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.get_cost(succ)+self.h1(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ, self.get_cost(succ)+self.h1(succ))
                    else:
                        self.parents[succ] = old_parent      
            elif (self.heur == 'h2'):
                 for move, succ in succs.items():

                  if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 

                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h2(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h2(succ))
                
                  elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.get_cost(succ)+self.h2(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ, self.get_cost(succ)+self.h2(succ))
                    else:
                        self.parents[succ] = old_parent
            elif (self.heur == 'h3'):
                for move, succ in succs.items():

                  if (succ not in self.frontier) and (succ not in self.explored):
                    self.parents[succ] = node 

                    if succ == self.goal:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h3(succ))
                        return self.get_results_dict(succ)
                    else:
                        self.add_to_frontier(succ, self.get_cost(succ)+self.h3(succ))
                
                  elif (succ in self.frontier):
                    old_parent = self.parents[succ]
                    old_priority = self.frontier.get(succ)
                    self.parents[succ] = node
                    new_priority = self.get_cost(succ)+self.h3(succ)

                    if(old_priority > new_priority):
                        self.frontier.add(succ, self.get_cost(succ)+self.h3(succ))
                    else:
                        self.parents[succ] = old_parent

                # elif (succ in self.frontier) and (self.frontier.get(succ) > self.get_cost(succ)+self.h1(succ)):
                #     self.frontier.remove(succ)
                #     self.frontier.add(succ,self.get_cost(succ)+self.h1(succ))

        # if we get here, the search failed
        return self.get_results_dict(None) 

    def add_to_frontier(self, node, priority):
        """Add state to frontier and increase the frontier count."""
        self.frontier.add(node, priority)
        self.frontier_count += 1

    def expand_node(self, node):
        """Get the next state from the frontier and increase the expanded count."""
        self.explored.add(node)
        self.expanded_count += 1
        return node.successors()

    def get_results_dict(self, state):
        """Construct the output dictionary for solve_puzzle()
        
        Args:
            state (EightPuzzleBoard): final state in the search tree
        
        Returns:
            A dictionary describing the search performed (see solve_puzzle())

        """
        results = {}
        results['frontier_count'] = self.frontier_count
        results['expanded_count'] = self.expanded_count
        if state:
            results['path_cost'] = self.get_cost(state)
            path = self.get_path(state)
            moves = ['start'] + [ path[i-1].get_move(path[i]) for i in range(1, len(path)) ]
            results['path'] = list(zip(moves, path))
        return results

    def get_path(self, state):
        """Return the solution path from the start state of the search to a target.
        
        Results are obtained by retracing the path backwards through the parent tree to the start
        state for the serach at the root.
        
        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            A list of EightPuzzleBoard objects representing the path from the start state to the
            target state

        """
        path = []
        while state is not None:
            path.append(state)
            state = self.parents[state]
        path.reverse()
        return path

    def get_cost(self, state): 
        """Calculate the path cost from start state to a target state.
        
        Transition costs between states are equal to the square of the number on the tile that 
        was moved. 

        Args:
            state (EightPuzzleBoard): target state in the search tree
        
        Returns:
            Integer indicating the cost of the solution path

        """
        cost = 0
        path = self.get_path(state)
        for i in range(1, len(path)):
            x, y = path[i-1].find(None)  # the most recently moved tile leaves the blank behind
            tile = path[i].get_tile(x, y)        
            cost += int(tile)**2
        return cost

    
    def h1(self, state):
        cost = 0
        path = self.get_path(state)
        for i in range(1,9):
            if (self.goal.__str__()[i]!=path[len(path)-1].__str__()[i]):
                cost += 1
        
        return cost

    def h2(self, state):
        cost = 0
        path = self.get_path(state)
        #print(path)
        #print(path[len(path)-1].pretty())
        # print(path[len(path)-1].find('1'))
        # print(self.goal.find('1'))
        #print(self.goal.pretty())

        for i in range(1,9):
            if (self.goal.__str__()[i]!=path[len(path)-1].__str__()[i]):
                x,y = path[len(path)-1].find(str(i))
                a,b = self.goal.find(str(i))
                cost += (abs(a-x) + abs(b-y))
        
        return cost

    # def h3(self, state):
    #     costList = []
    #     paths = self.get_path(state)
    #     print(paths)
    #     # print(path[len(path)-1].pretty())

    #     for path in paths:
    #         cost = 0
    #         for i in range(1,8):
    #             if (self.goal.__str__()[i]!=path.__str__()[i]):
    #                 # print(path.__str__()[i])
    #                 x,y = path.find(str(i))
    #                 a,b = self.goal.find(str(i))
    #                 tile = path.get_tile(x, y) 
    #             cost += int(tile)*int(tile)*(abs(a-x) + abs(b-y))
    #         costList.append(cost)
    #     # print(costList)

    #     return min(costList)
    def h3(self, state):
        cost = 0
        path = self.get_path(state)

        for i in range(1,9):
            if (self.goal.__str__()[i]!=path[len(path)-1].__str__()[i]):
                x,y = path[len(path)-1].find(str(i))
                a,b = self.goal.find(str(i))
                tile = path[len(path)-1].get_tile(x, y) 
                cost += int(tile)**2*(abs(a-x) + abs(b-y))

        return cost


def print_table(flav__results, include_path=False):
    """Print out a comparison of search strategy results.

    Args:
        flav__results (dictionary): a dictionary mapping search flavor tags result statistics. See
            solve_puzzle() for detail.
        include_path (bool): indicates whether to include the actual solution paths in the table

    """
    result_tups = sorted(flav__results.items())
    c = len(result_tups)
    na = "{:>12}".format("n/a")
    rows = [  # abandon all hope ye who try to modify the table formatting code...
        "flavor  " + "".join([ "{:>12}".format(tag) for tag, _ in result_tups]),
        "--------" + ("  " + "-"*10)*c,
        "length  " + "".join([ "{:>12}".format(len(res['path'])) if 'path' in res else na 
                                for _, res in result_tups ]),
        "cost    " + "".join([ "{:>12,}".format(res['path_cost']) if 'path_cost' in res else na 
                                for _, res in result_tups ]),
        "frontier" + ("{:>12,}" * c).format(*[res['frontier_count'] for _, res in result_tups]),
        "expanded" + ("{:>12,}" * c).format(*[res['expanded_count'] for _, res in result_tups])
    ]
    if include_path:
        rows.append("path")
        longest_path = max([ len(res['path']) for _, res in result_tups if 'path' in res ] + [0])
        print("longest", longest_path)
        for i in range(longest_path):
            row = "        "
            for _, res in result_tups:
                if len(res.get('path', [])) > i:
                    move, state = res['path'][i]
                    row += " " + move[0] + " " + str(state)
                else:
                    row += " "*12
            rows.append(row)
    print("\n" + "\n".join(rows), "\n")


def get_test_puzzles():
    """Return sample start states for testing the search strategies.
    
    Returns:
        A tuple containing three EightPuzzleBoard objects representing start states that have an
        optimal solution path length of 3-5, 10-15, and >=25 respectively.
    
    """
    # Note: test cases can be hardcoded, and are not required to be programmatically generated.
    #
    # fill in function body here
    #    
    return (puzz.EightPuzzleBoard("120345678"), puzz.EightPuzzleBoard("123045678"), puzz.EightPuzzleBoard("802356174"))


############################################

if __name__ == '__main__':

    # parse the command line args
    start = puzz.EightPuzzleBoard(sys.argv[1])
    if sys.argv[2] == 'all':
        flavors = ['bfs', 'ucost', 'greedy-h1', 'greedy-h2', 
                   'greedy-h3', 'astar-h1', 'astar-h2', 'astar-h3']
    else:
        flavors = sys.argv[2:]

    # run the search(es)
    results = {}
    for flav in flavors:
        print("solving puzzle {} with {}".format(start, flav))
        results[flav] = solve_puzzle(start, flav)

    print_table(results, include_path=False)  # change to True to see the paths!


