import heapq


class Node:
    state = None
    parentstate = None
    action = None
    edgeCost = None
    gOfN = None  # total edge cost
    hOfN = None  # heuristic value
    heuristicFn = None

    def __init__(self, value):
        self.value = value


class SearchAlgorithms:
    Path = []
    fullPath = []
    totalCost = -1

    def __init__(self, start, end):
        self.start = self._validate_puzzle(start, "start")
        self.end = self._validate_puzzle(end, "end")
        self.Path = []
        self.fullPath = []
        self.totalCost = -1

    def UCS(self):
        return self._priority_search("ucs")

    def Astar(self):
        return self._priority_search("astar")

    def Greedy(self):
        return self._priority_search("greedy")

    def _priority_search(self, algorithm):
        if not self._can_reach_goal():
            self.Path = []
            self.fullPath = []
            self.totalCost = -1
            return self.Path, self.fullPath, self.totalCost

        start_node = self._make_node(
            state=self.start,
            parent=None,
            action=None,
            edge_cost=0,
            g_of_n=0,
            h_of_n=self._heuristic(self.start),
            heuristic_name="Manhattan",
        )

        frontier = []
        counter = 0
        heapq.heappush(
            frontier,
            (self._priority(start_node, algorithm), counter, start_node),
        )

        best_cost = {self.start: 0}

        while frontier:
            _, _, current_node = heapq.heappop(frontier)
            current_state = current_node.state

            if current_node.gOfN > best_cost[current_state]:
                continue

            if current_state == self.end:
                self.Path, self.fullPath = self._build_solution(current_node)
                self.totalCost = current_node.gOfN
                return self.Path, self.fullPath, self.totalCost

            for next_state, action, edge_cost in self._children(current_state):
                new_cost = current_node.gOfN + edge_cost

                if next_state in best_cost and new_cost >= best_cost[next_state]:
                    continue

                best_cost[next_state] = new_cost
                next_node = self._make_node(
                    state=next_state,
                    parent=current_node,
                    action=action,
                    edge_cost=edge_cost,
                    g_of_n=new_cost,
                    h_of_n=self._heuristic(next_state),
                    heuristic_name="Manhattan",
                )
                counter += 1
                heapq.heappush(
                    frontier,
                    (self._priority(next_node, algorithm), counter, next_node),
                )

        self.Path = []
        self.fullPath = []
        self.totalCost = -1
        return self.Path, self.fullPath, self.totalCost

    def _priority(self, node, algorithm):
        if algorithm == "ucs":
            return node.gOfN
        if algorithm == "astar":
            return node.gOfN + node.hOfN
        return node.hOfN

    def _make_node(self, state, parent, action, edge_cost, g_of_n, h_of_n, heuristic_name):
        node = Node(list(state))
        node.state = state
        node.parent = parent
        node.parentstate = list(parent.state) if parent is not None else None
        node.action = action
        node.edgeCost = edge_cost
        node.gOfN = g_of_n
        node.hOfN = h_of_n
        node.heuristicFn = heuristic_name
        return node

    def _build_solution(self, goal_node):
        path = []
        full_path = []
        current = goal_node

        while current is not None:
            full_path.append(list(current.state))
            if current.action is not None:
                path.append(current.action)
            current = current.parent

        path.reverse()
        full_path.reverse()
        return path, full_path

    def _children(self, state):
        zero_index = state.index(0)
        row = zero_index // 3
        col = zero_index % 3
        moves = [
            ("UP", -1, 0),
            ("DOWN", 1, 0),
            ("LEFT", 0, -1),
            ("RIGHT", 0, 1),
        ]

        for action, row_change, col_change in moves:
            next_row = row + row_change
            next_col = col + col_change

            if 0 <= next_row < 3 and 0 <= next_col < 3:
                swap_index = next_row * 3 + next_col
                next_state = list(state)
                next_state[zero_index], next_state[swap_index] = (
                    next_state[swap_index],
                    next_state[zero_index],
                )
                yield tuple(next_state), action, 1

    def _heuristic(self, state):
        total = 0
        for index, value in enumerate(state):
            if value == 0:
                continue

            goal_index = self.end.index(value)
            current_row = index // 3
            current_col = index % 3
            goal_row = goal_index // 3
            goal_col = goal_index % 3
            total += abs(current_row - goal_row) + abs(current_col - goal_col)

        return total

    def _can_reach_goal(self):
        return self._inversion_count(self.start) % 2 == self._inversion_count(self.end) % 2

    def _inversion_count(self, state):
        numbers = [number for number in state if number != 0]
        inversions = 0

        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                if numbers[i] > numbers[j]:
                    inversions += 1

        return inversions

    def _validate_puzzle(self, puzzle, name):
        if len(puzzle) != 9:
            raise ValueError(name + " puzzle must contain exactly 9 numbers")

        state = tuple(puzzle)
        if sorted(state) != list(range(9)):
            raise ValueError(name + " puzzle must contain numbers 0 through 8 exactly once")

        return state
    
def main():
    s3 = SearchAlgorithms([1, 2, 3, 4, 0, 6, 7, 5, 8], [1,2,3,4,5,6,7,8,0])
    path, fullPath, cost = s3.UCS()
    print('UCS Path: ' + str(path), end='\nFull Path is: ')
    print(fullPath)
    print(" + total Cost = " + str(cost))

    s4 = SearchAlgorithms([1, 2, 3, 4, 0, 6, 7, 5, 8], [1,2,3,4,5,6,7,8,0])
    path, fullPath, cost = s4.Astar()
    print('AstarHeuristic Path: ' + str(path), end='\nFull Path is: ')
    print(fullPath)
    print(" + total Cost = " + str(cost))

    s4 = SearchAlgorithms([1, 2, 3, 4, 0, 6, 7, 5, 8], [1,2,3,4,5,6,7,8,0])
    path, fullPath, cost = s4.Greedy()
    print('GreedyHeuristic Path: ' + str(path), end='\nFull Path is: ')
    print(fullPath)
    print(" + total Cost = " + str(cost))

main()
