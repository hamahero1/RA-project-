from __future__ import annotations

import argparse
import heapq
import sys
import time
from collections import deque
from collections.abc import Sequence

BOARD_SIZE = 3
TILE_COUNT = BOARD_SIZE * BOARD_SIZE
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
DEFAULT_START = (1, 2, 3, 4, 0, 6, 7, 5, 8)
UI_HEURISTIC_LABELS = ["Misplaced Tiles", "Manhattan Distance", "Linear Conflict"]
NOT_USED_LABEL = "Not used"

State = tuple[int, ...]


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
    """Required project class for UCS, A*, Greedy, and bonus BFS/DFS."""

    BOARD_SIZE = BOARD_SIZE
    TILE_COUNT = TILE_COUNT
    GOAL = GOAL
    DEFAULT_START = DEFAULT_START
    UI_HEURISTIC_LABELS = UI_HEURISTIC_LABELS
    NOT_USED_LABEL = NOT_USED_LABEL

    Path = []
    fullPath = []
    totalCost = -1

    def __init__(self, start, end):
        self.start = self.validate_state(start, "start")
        self.end = self.validate_state(end, "end")
        self.Path = []
        self.fullPath = []
        self.totalCost = -1
        self.heuristic_name = "manhattan"
        self.last_stats = {}

    # Required algorithms
    def UCS(self):
        algorithm = "ucs"
        heuristic_name = "zero"
        started_at = time.perf_counter()
        if not self.is_solvable(self.start, self.end):
            return self._finish(algorithm, heuristic_name, started_at, solvable=False)

        frontier = []
        start_node = self._make_node(self.start, None, None, 0, 0, 0, heuristic_name)
        heapq.heappush(frontier, (0, 0, 0, start_node))

        best_cost_to_state = {self.start: 0}
        counter = 0
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_cost_to_state.get(current.state, sys.maxsize):
                continue

            if current.state == self.end:
                return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max, current)

            expanded += 1
            for action, next_state in self.successors(current.state):
                new_cost = current.gOfN + 1
                if new_cost >= best_cost_to_state.get(next_state, sys.maxsize):
                    continue

                best_cost_to_state[next_state] = new_cost
                counter += 1
                generated += 1
                child = self._make_node(next_state, current, action, 1, new_cost, 0, heuristic_name)
                heapq.heappush(frontier, (new_cost, 0, counter, child))

            frontier_max = max(frontier_max, len(frontier))

        return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max)

    def Astar(self, heuristic=None):
        algorithm = "astar"
        heuristic_name = self.normalize_heuristic_name(heuristic or self.heuristic_name)
        started_at = time.perf_counter()
        if not self.is_solvable(self.start, self.end):
            return self._finish(algorithm, heuristic_name, started_at, solvable=False)

        start_h = self._heuristic(self.start, heuristic_name)
        start_node = self._make_node(self.start, None, None, 0, 0, start_h, heuristic_name)
        frontier = []
        heapq.heappush(frontier, (start_h, start_h, 0, start_node))

        best_cost_to_state = {self.start: 0}
        counter = 0
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_cost_to_state.get(current.state, sys.maxsize):
                continue

            if current.state == self.end:
                return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max, current)

            expanded += 1
            for action, next_state in self.successors(current.state):
                new_cost = current.gOfN + 1
                if new_cost >= best_cost_to_state.get(next_state, sys.maxsize):
                    continue

                next_h = self._heuristic(next_state, heuristic_name)
                best_cost_to_state[next_state] = new_cost
                counter += 1
                generated += 1
                child = self._make_node(next_state, current, action, 1, new_cost, next_h, heuristic_name)
                heapq.heappush(frontier, (new_cost + next_h, next_h, counter, child))

            frontier_max = max(frontier_max, len(frontier))

        return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max)

    def Greedy(self, heuristic=None):
        algorithm = "greedy"
        heuristic_name = self.normalize_heuristic_name(heuristic or self.heuristic_name)
        started_at = time.perf_counter()
        if not self.is_solvable(self.start, self.end):
            return self._finish(algorithm, heuristic_name, started_at, solvable=False)

        start_h = self._heuristic(self.start, heuristic_name)
        start_node = self._make_node(self.start, None, None, 0, 0, start_h, heuristic_name)
        frontier = []
        heapq.heappush(frontier, (start_h, 0, 0, start_node))

        best_cost_to_state = {self.start: 0}
        counter = 0
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_cost_to_state.get(current.state, sys.maxsize):
                continue

            if current.state == self.end:
                return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max, current)

            expanded += 1
            for action, next_state in self.successors(current.state):
                new_cost = current.gOfN + 1
                if new_cost >= best_cost_to_state.get(next_state, sys.maxsize):
                    continue

                next_h = self._heuristic(next_state, heuristic_name)
                best_cost_to_state[next_state] = new_cost
                counter += 1
                generated += 1
                child = self._make_node(next_state, current, action, 1, new_cost, next_h, heuristic_name)
                heapq.heappush(frontier, (next_h, new_cost, counter, child))

            frontier_max = max(frontier_max, len(frontier))

        return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max)

    # Bonus algorithms
    def BFS(self):
        algorithm = "bfs"
        heuristic_name = "not_used"
        started_at = time.perf_counter()
        if not self.is_solvable(self.start, self.end):
            return self._finish(algorithm, heuristic_name, started_at, solvable=False)

        start_node = self._make_node(self.start, None, None, 0, 0, 0, heuristic_name)
        frontier = deque([start_node])
        discovered_states = {self.start}
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            current = frontier.popleft()
            if current.state == self.end:
                return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max, current)

            expanded += 1
            for action, next_state in self.successors(current.state):
                if next_state in discovered_states:
                    continue

                discovered_states.add(next_state)
                generated += 1
                child = self._make_node(next_state, current, action, 1, current.gOfN + 1, 0, heuristic_name)
                frontier.append(child)

            frontier_max = max(frontier_max, len(frontier))

        return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max)

    def DFS(self):
        algorithm = "dfs"
        heuristic_name = "not_used"
        started_at = time.perf_counter()
        if not self.is_solvable(self.start, self.end):
            return self._finish(algorithm, heuristic_name, started_at, solvable=False)

        start_node = self._make_node(self.start, None, None, 0, 0, 0, heuristic_name)
        frontier = [start_node]
        discovered_states = {self.start}
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            current = frontier.pop()
            if current.state == self.end:
                return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max, current)

            expanded += 1
            for action, next_state in reversed(self.successors(current.state)):
                if next_state in discovered_states:
                    continue

                discovered_states.add(next_state)
                generated += 1
                child = self._make_node(next_state, current, action, 1, current.gOfN + 1, 0, heuristic_name)
                frontier.append(child)

            frontier_max = max(frontier_max, len(frontier))

        return self._finish(algorithm, heuristic_name, started_at, expanded, generated, frontier_max)

    def _make_node(self, state, parent, action, edge_cost, g_of_n, h_of_n, heuristic_name):
        node = Node(list(state))
        node.state = tuple(state)
        node.parent = parent
        node.parentstate = list(parent.state) if parent is not None else None
        node.action = action
        node.edgeCost = edge_cost
        node.gOfN = g_of_n
        node.hOfN = h_of_n
        node.heuristicFn = heuristic_name
        return node

    def _heuristic(self, state, heuristic_name):
        key = self.normalize_heuristic_name(heuristic_name)
        if key == "zero":
            return 0
        if key == "misplaced":
            return self.misplaced(state, self.end)
        if key == "manhattan":
            return self.manhattan(state, self.end)
        if key == "linear_conflict":
            return self.linear_conflict(state, self.end)
        raise ValueError("Unknown heuristic: " + str(heuristic_name))

    def _finish(
        self,
        algorithm,
        heuristic_name,
        started_at,
        expanded=0,
        generated=1,
        frontier_max=1,
        goal_node=None,
        solvable=True,
    ):
        if goal_node is not None:
            actions = []
            states = []
            current = goal_node
            while current is not None:
                states.append(list(current.state))
                if current.action is not None:
                    actions.append(current.action)
                current = current.parent

            actions.reverse()
            states.reverse()
            self.Path = actions
            self.fullPath = states
            self.totalCost = len(actions)
        else:
            self.Path = []
            self.fullPath = [] if solvable else [list(self.start)]
            self.totalCost = -1

        self.last_stats = {
            "algorithm": algorithm,
            "heuristic": heuristic_name,
            "solvable": solvable,
            "success": goal_node is not None,
            "expanded": expanded,
            "generated": generated,
            "frontier_max": frontier_max,
            "cost": self.totalCost,
            "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
        }
        return self.Path, self.fullPath, self.totalCost

    # Everything below is still inside the class: input rules, heuristics, tools, and CLI.
    @classmethod
    def validate_state(cls, values: Sequence[int] | str, label: str = "state") -> State:
        if isinstance(values, str):
            cleaned = values.replace(",", " ").replace(";", " ")
            parts = cleaned.split()
            if len(parts) == 1 and len(parts[0]) == cls.TILE_COUNT and parts[0].isdigit():
                parsed = tuple(int(part) for part in parts[0])
            else:
                try:
                    parsed = tuple(int(part) for part in parts)
                except ValueError as exc:
                    raise ValueError(label + " must contain only numbers from 0 to 8.") from exc
        else:
            parsed = tuple(int(value) for value in values)

        if len(parsed) != cls.TILE_COUNT:
            raise ValueError(label + " must contain exactly 9 numbers.")
        if sorted(parsed) != list(range(cls.TILE_COUNT)):
            raise ValueError(label + " must contain each number from 0 to 8 exactly once.")
        return parsed

    @staticmethod
    def count_inversions(state: Sequence[int], ignore_zero: bool = True) -> int:
        tiles = [tile for tile in state if not ignore_zero or tile != 0]
        inversions = 0
        for left in range(len(tiles)):
            for right in range(left + 1, len(tiles)):
                if tiles[left] > tiles[right]:
                    inversions += 1
        return inversions

    @classmethod
    def is_solvable(cls, start: Sequence[int], goal: Sequence[int] = GOAL) -> bool:
        start_state = cls.validate_state(start, "start")
        goal_state = cls.validate_state(goal, "goal")
        return cls.count_inversions(start_state) % 2 == cls.count_inversions(goal_state) % 2

    @classmethod
    def misplaced(cls, state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
        state = cls.validate_state(state)
        goal = cls.validate_state(goal, "goal")
        total = 0
        for index, tile in enumerate(state):
            if tile != 0 and tile != goal[index]:
                total += 1
        return total

    @classmethod
    def manhattan(cls, state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
        state = cls.validate_state(state)
        positions = {
            tile: divmod(index, cls.BOARD_SIZE)
            for index, tile in enumerate(cls.validate_state(goal, "goal"))
        }
        total = 0
        for index, tile in enumerate(state):
            if tile == 0:
                continue
            row, col = divmod(index, cls.BOARD_SIZE)
            goal_row, goal_col = positions[tile]
            total += abs(row - goal_row) + abs(col - goal_col)
        return total

    @classmethod
    def linear_conflict(cls, state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
        state = cls.validate_state(state)
        goal = cls.validate_state(goal, "goal")
        positions = {tile: divmod(index, cls.BOARD_SIZE) for index, tile in enumerate(goal)}
        conflicts = 0

        for row in range(cls.BOARD_SIZE):
            row_tiles = state[row * cls.BOARD_SIZE : (row + 1) * cls.BOARD_SIZE]
            goal_columns = [
                positions[tile][1]
                for tile in row_tiles
                if tile != 0 and positions[tile][0] == row
            ]
            conflicts += cls.count_inversions(goal_columns, ignore_zero=False)

        for col in range(cls.BOARD_SIZE):
            column_tiles = [state[row * cls.BOARD_SIZE + col] for row in range(cls.BOARD_SIZE)]
            goal_rows = [
                positions[tile][0]
                for tile in column_tiles
                if tile != 0 and positions[tile][1] == col
            ]
            conflicts += cls.count_inversions(goal_rows, ignore_zero=False)

        return cls.manhattan(state, goal) + (2 * conflicts)

    @classmethod
    def successors(cls, state: Sequence[int]) -> list[tuple[str, State]]:
        state = cls.validate_state(state)
        blank = state.index(0)
        row, col = divmod(blank, cls.BOARD_SIZE)
        moves = []

        if row > 0:
            moves.append(("UP", blank - cls.BOARD_SIZE))
        if row < cls.BOARD_SIZE - 1:
            moves.append(("DOWN", blank + cls.BOARD_SIZE))
        if col > 0:
            moves.append(("LEFT", blank - 1))
        if col < cls.BOARD_SIZE - 1:
            moves.append(("RIGHT", blank + 1))

        result = []
        for action, swap_index in moves:
            next_state = list(state)
            next_state[blank], next_state[swap_index] = next_state[swap_index], next_state[blank]
            result.append((action, tuple(next_state)))
        return result

    @staticmethod
    def normalize_heuristic_name(name):
        if not name:
            return "manhattan"
        key = str(name).strip().lower().replace("-", "_").replace(" ", "_")
        aliases = {
            "h1": "misplaced",
            "misplaced": "misplaced",
            "misplaced_tiles": "misplaced",
            "h2": "manhattan",
            "manhattan": "manhattan",
            "manhattan_distance": "manhattan",
            "h3": "linear_conflict",
            "linear": "linear_conflict",
            "linear_conflict": "linear_conflict",
            "zero": "zero",
            "none": "zero",
            "not_used": "zero",
        }
        return aliases.get(key, key)

    @classmethod
    def heuristic_values(cls, state, goal=GOAL):
        return {
            "misplaced": cls.misplaced(state, goal),
            "manhattan": cls.manhattan(state, goal),
            "linear_conflict": cls.linear_conflict(state, goal),
        }

    @staticmethod
    def run_selected_algorithm(solver, algorithm, heuristic="manhattan"):
        normalized = str(algorithm).strip().lower().replace("*", "star").replace(" ", "_")
        if normalized == "ucs":
            return solver.UCS()
        if normalized in {"astar", "a_star"}:
            return solver.Astar(heuristic)
        if normalized == "greedy":
            return solver.Greedy(heuristic)
        if normalized == "bfs":
            return solver.BFS()
        if normalized == "dfs":
            return solver.DFS()
        raise ValueError("Unknown algorithm: " + str(algorithm))

    @classmethod
    def run_benchmark(cls, start=DEFAULT_START, goal=GOAL):
        rows = []
        for algorithm, heuristic in [
            ("UCS", "zero"),
            ("A*", "misplaced"),
            ("A*", "manhattan"),
            ("A*", "linear_conflict"),
            ("Greedy", "misplaced"),
            ("Greedy", "manhattan"),
            ("Greedy", "linear_conflict"),
            ("BFS", "zero"),
            ("DFS", "zero"),
        ]:
            solver = cls(start, goal)
            cls.run_selected_algorithm(solver, algorithm, heuristic)
            rows.append(dict(solver.last_stats))
        return rows

    @classmethod
    def run_self_test(cls):
        start = DEFAULT_START
        goal = GOAL

        for algorithm, heuristic in [
            ("UCS", "zero"),
            ("A*", "manhattan"),
            ("Greedy", "manhattan"),
            ("BFS", "zero"),
            ("DFS", "zero"),
        ]:
            solver = cls(start, goal)
            path, full_path, cost = cls.run_selected_algorithm(solver, algorithm, heuristic)
            assert full_path[0] == list(start)
            assert full_path[-1] == list(goal)
            assert cost == len(path)

        assert cls.is_solvable([1, 2, 3, 4, 0, 6, 7, 5, 8], goal)
        assert not cls.is_solvable([1, 2, 3, 4, 5, 6, 8, 7, 0], goal)
        return True

    @classmethod
    def run_from_args(cls):
        parser = argparse.ArgumentParser(description="Solve the 8-puzzle problem.")
        parser.add_argument("--cli", action="store_true", help="Run all algorithms on the default puzzle.")
        parser.add_argument("--benchmark", action="store_true", help="Run benchmark rows for all algorithms.")
        parser.add_argument("--self-test", action="store_true", help="Run simple solver tests.")
        parser.add_argument("--algorithm", choices=["UCS", "A*", "Greedy", "BFS", "DFS"], help="Run one algorithm.")
        parser.add_argument("--heuristic", default="manhattan", help="A* or Greedy heuristic.")
        parser.add_argument("--start", default=" ".join(str(tile) for tile in cls.DEFAULT_START), help="Start puzzle.")
        parser.add_argument("--goal", default=" ".join(str(tile) for tile in cls.GOAL), help="Goal puzzle.")
        args = parser.parse_args()
        start = cls.validate_state(args.start, "start")
        goal = cls.validate_state(args.goal, "goal")

        if args.self_test:
            cls.run_self_test()
            print("Self-test passed.")
            return

        if args.benchmark:
            rows = cls.run_benchmark(start, goal)
            print("Algorithm | Cost | Expanded | Generated | Runtime ms | Heuristic")
            print("--------- | ---- | -------- | --------- | ---------- | ---------")
            for row in rows:
                print(
                    str(row["algorithm"])
                    + " | "
                    + str(row["cost"])
                    + " | "
                    + str(row["expanded"])
                    + " | "
                    + str(row["generated"])
                    + " | "
                    + str(row["runtime_ms"])
                    + " | "
                    + str(row["heuristic"])
                )
            return

        if args.algorithm:
            solver = cls(start, goal)
            path, full_path, cost = cls.run_selected_algorithm(solver, args.algorithm, args.heuristic)
            print(args.algorithm + " Path: " + str(path))
            print("Full Path is: " + str(full_path))
            print(" + total Cost = " + str(cost))
            print("Stats: " + str(solver.last_stats))
            return

        for algorithm, heuristic in [
            ("UCS", "zero"),
            ("A*", "manhattan"),
            ("Greedy", "manhattan"),
            ("BFS", "zero"),
            ("DFS", "zero"),
        ]:
            solver = cls(start, goal)
            path, full_path, cost = cls.run_selected_algorithm(solver, algorithm, heuristic)
            print(algorithm + " Path: " + str(path))
            print("Full Path is: " + str(full_path))
            print(" + total Cost = " + str(cost))
            print("Stats: " + str(solver.last_stats))


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

if __name__ == "__main__" and len(sys.argv) == 1:
    main()

if __name__ == "__main__" and len(sys.argv) > 1:
    SearchAlgorithms.run_from_args()
