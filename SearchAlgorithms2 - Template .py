from __future__ import annotations

import argparse
import heapq
import random
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


def validate_state(values: Sequence[int] | str, label: str = "state") -> State:
    if isinstance(values, str):
        cleaned = values.replace(",", " ").replace(";", " ")
        parts = cleaned.split()
        if len(parts) == 1 and len(parts[0]) == TILE_COUNT and parts[0].isdigit():
            parsed = tuple(int(part) for part in parts[0])
        else:
            try:
                parsed = tuple(int(part) for part in parts)
            except ValueError as exc:
                raise ValueError(label + " must contain only numbers from 0 to 8.") from exc
    else:
        parsed = tuple(int(value) for value in values)

    if len(parsed) != TILE_COUNT:
        raise ValueError(label + " must contain exactly 9 numbers.")
    if sorted(parsed) != list(range(TILE_COUNT)):
        raise ValueError(label + " must contain each number from 0 to 8 exactly once.")
    return parsed


def format_state(state: Sequence[int]) -> str:
    state = validate_state(state)
    rows = []
    for row in range(BOARD_SIZE):
        start = row * BOARD_SIZE
        rows.append(" ".join(str(tile) for tile in state[start : start + BOARD_SIZE]))
    return "\n".join(rows)


def count_inversions(state: Sequence[int]) -> int:
    tiles = [tile for tile in state if tile != 0]
    inversions = 0
    for left in range(len(tiles)):
        for right in range(left + 1, len(tiles)):
            if tiles[left] > tiles[right]:
                inversions += 1
    return inversions


def is_solvable(start: Sequence[int], goal: Sequence[int] = GOAL) -> bool:
    start_state = validate_state(start, "start")
    goal_state = validate_state(goal, "goal")
    return count_inversions(start_state) % 2 == count_inversions(goal_state) % 2


def goal_positions(goal: Sequence[int]) -> dict[int, tuple[int, int]]:
    goal_state = validate_state(goal, "goal")
    positions = {}
    for index, tile in enumerate(goal_state):
        positions[tile] = divmod(index, BOARD_SIZE)
    return positions


def misplaced(state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
    state = validate_state(state)
    goal = validate_state(goal, "goal")
    total = 0
    for index, tile in enumerate(state):
        if tile != 0 and tile != goal[index]:
            total += 1
    return total


def manhattan(state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
    state = validate_state(state)
    positions = goal_positions(goal)
    total = 0
    for index, tile in enumerate(state):
        if tile == 0:
            continue
        row, col = divmod(index, BOARD_SIZE)
        goal_row, goal_col = positions[tile]
        total += abs(row - goal_row) + abs(col - goal_col)
    return total


def linear_conflict(state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
    state = validate_state(state)
    goal = validate_state(goal, "goal")
    positions = goal_positions(goal)
    conflicts = 0

    for row in range(BOARD_SIZE):
        row_tiles = state[row * BOARD_SIZE : (row + 1) * BOARD_SIZE]
        goal_columns = [
            positions[tile][1]
            for tile in row_tiles
            if tile != 0 and positions[tile][0] == row
        ]
        conflicts += _inversion_count(goal_columns)

    for col in range(BOARD_SIZE):
        column_tiles = [state[row * BOARD_SIZE + col] for row in range(BOARD_SIZE)]
        goal_rows = [
            positions[tile][0]
            for tile in column_tiles
            if tile != 0 and positions[tile][1] == col
        ]
        conflicts += _inversion_count(goal_rows)

    return manhattan(state, goal) + (2 * conflicts)


def _inversion_count(values: Sequence[int]) -> int:
    inversions = 0
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            if values[left] > values[right]:
                inversions += 1
    return inversions


def successors(state: Sequence[int]) -> list[tuple[str, State]]:
    state = validate_state(state)
    blank = state.index(0)
    row, col = divmod(blank, BOARD_SIZE)
    moves = []

    if row > 0:
        moves.append(("UP", blank - BOARD_SIZE))
    if row < BOARD_SIZE - 1:
        moves.append(("DOWN", blank + BOARD_SIZE))
    if col > 0:
        moves.append(("LEFT", blank - 1))
    if col < BOARD_SIZE - 1:
        moves.append(("RIGHT", blank + 1))

    result = []
    for action, swap_index in moves:
        next_state = list(state)
        next_state[blank], next_state[swap_index] = next_state[swap_index], next_state[blank]
        result.append((action, tuple(next_state)))
    return result


class SearchAlgorithms:
    Path = []
    fullPath = []
    totalCost = -1

    def __init__(self, start, end):
        self.start = validate_state(start, "start")
        self.end = validate_state(end, "end")
        self.Path = []
        self.fullPath = []
        self.totalCost = -1
        self.heuristic_name = "manhattan"
        self.last_stats = {}

    def UCS(self):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("ucs", "zero", started_at)

        frontier = []
        start_node = self._make_node(self.start, None, None, 0, 0, 0, "zero")
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
                return self._finish_success(current, "ucs", "zero", started_at, expanded, generated, frontier_max)

            expanded += 1
            for action, next_state in successors(current.state):
                new_cost = current.gOfN + 1
                if new_cost >= best_cost_to_state.get(next_state, sys.maxsize):
                    continue

                best_cost_to_state[next_state] = new_cost
                counter += 1
                generated += 1
                child = self._make_node(next_state, current, action, 1, new_cost, 0, "zero")
                heapq.heappush(frontier, (new_cost, 0, counter, child))
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("ucs", "zero", started_at, expanded, generated, frontier_max)

    def Astar(self, heuristic=None):
        heuristic_name = normalize_heuristic_name(heuristic or self.heuristic_name)
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("astar", heuristic_name, started_at)

        start_h = self._heuristic(self.start, heuristic_name)
        frontier = []
        start_node = self._make_node(self.start, None, None, 0, 0, start_h, heuristic_name)
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
                return self._finish_success(current, "astar", heuristic_name, started_at, expanded, generated, frontier_max)

            expanded += 1
            for action, next_state in successors(current.state):
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

        return self._finish_failure("astar", heuristic_name, started_at, expanded, generated, frontier_max)

    def Greedy(self, heuristic=None):
        heuristic_name = normalize_heuristic_name(heuristic or self.heuristic_name)
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("greedy", heuristic_name, started_at)

        start_h = self._heuristic(self.start, heuristic_name)
        frontier = []
        start_node = self._make_node(self.start, None, None, 0, 0, start_h, heuristic_name)
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
                return self._finish_success(current, "greedy", heuristic_name, started_at, expanded, generated, frontier_max)

            expanded += 1
            for action, next_state in successors(current.state):
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

        return self._finish_failure("greedy", heuristic_name, started_at, expanded, generated, frontier_max)

    def BFS(self):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("bfs", "not_used", started_at)

        start_node = self._make_node(self.start, None, None, 0, 0, 0, "not_used")
        frontier = deque([start_node])
        discovered_states = {self.start}
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            current = frontier.popleft()
            if current.state == self.end:
                return self._finish_success(current, "bfs", "not_used", started_at, expanded, generated, frontier_max)

            expanded += 1
            for action, next_state in successors(current.state):
                if next_state in discovered_states:
                    continue

                discovered_states.add(next_state)
                generated += 1
                child = self._make_node(next_state, current, action, 1, current.gOfN + 1, 0, "not_used")
                frontier.append(child)
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("bfs", "not_used", started_at, expanded, generated, frontier_max)

    def DFS(self):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("dfs", "not_used", started_at)

        start_node = self._make_node(self.start, None, None, 0, 0, 0, "not_used")
        frontier = [start_node]
        discovered_states = {self.start}
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            current = frontier.pop()
            if current.state == self.end:
                return self._finish_success(current, "dfs", "not_used", started_at, expanded, generated, frontier_max)

            expanded += 1
            for action, next_state in reversed(successors(current.state)):
                if next_state in discovered_states:
                    continue

                discovered_states.add(next_state)
                generated += 1
                child = self._make_node(next_state, current, action, 1, current.gOfN + 1, 0, "not_used")
                frontier.append(child)
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("dfs", "not_used", started_at, expanded, generated, frontier_max)

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
        key = normalize_heuristic_name(heuristic_name)
        if key == "zero":
            return 0
        if key == "misplaced":
            return misplaced(state, self.end)
        if key == "manhattan":
            return manhattan(state, self.end)
        if key == "linear_conflict":
            return linear_conflict(state, self.end)
        raise ValueError("Unknown heuristic: " + str(heuristic_name))

    def _finish_unsolvable(self, algorithm, heuristic_name, started_at):
        self.Path = []
        self.fullPath = [list(self.start)]
        self.totalCost = -1
        self.last_stats = {
            "algorithm": algorithm,
            "heuristic": heuristic_name,
            "solvable": False,
            "success": False,
            "expanded": 0,
            "generated": 1,
            "frontier_max": 1,
            "cost": -1,
            "runtime_ms": _elapsed_ms(started_at),
        }
        return self.Path, self.fullPath, self.totalCost

    def _finish_success(self, goal_node, algorithm, heuristic_name, started_at, expanded, generated, frontier_max):
        self.Path, self.fullPath, self.totalCost = self._reconstruct(goal_node)
        self.last_stats = {
            "algorithm": algorithm,
            "heuristic": heuristic_name,
            "solvable": True,
            "success": True,
            "expanded": expanded,
            "generated": generated,
            "frontier_max": frontier_max,
            "cost": self.totalCost,
            "runtime_ms": _elapsed_ms(started_at),
        }
        return self.Path, self.fullPath, self.totalCost

    def _finish_failure(self, algorithm, heuristic_name, started_at, expanded, generated, frontier_max):
        self.Path = []
        self.fullPath = []
        self.totalCost = -1
        self.last_stats = {
            "algorithm": algorithm,
            "heuristic": heuristic_name,
            "solvable": True,
            "success": False,
            "expanded": expanded,
            "generated": generated,
            "frontier_max": frontier_max,
            "cost": -1,
            "runtime_ms": _elapsed_ms(started_at),
        }
        return self.Path, self.fullPath, self.totalCost

    @staticmethod
    def _reconstruct(node):
        actions = []
        states = []
        current = node

        while current is not None:
            states.append(list(current.state))
            if current.action is not None:
                actions.append(current.action)
            current = current.parent

        actions.reverse()
        states.reverse()
        return actions, states, len(actions)


def _elapsed_ms(started_at):
    return round((time.perf_counter() - started_at) * 1000, 3)


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


def heuristic_values(state, goal=GOAL):
    return {
        "misplaced": misplaced(state, goal),
        "manhattan": manhattan(state, goal),
        "linear_conflict": linear_conflict(state, goal),
    }


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


def random_solvable_state(goal=GOAL, steps=50):
    current = validate_state(goal, "goal")
    previous = None
    for _ in range(steps):
        options = [(action, state) for action, state in successors(current) if state != previous]
        previous = current
        _, current = random.choice(options)
    return current


def run_demo(start=DEFAULT_START, goal=GOAL):
    for algorithm, heuristic in [
        ("UCS", "zero"),
        ("A*", "manhattan"),
        ("Greedy", "manhattan"),
        ("BFS", "zero"),
        ("DFS", "zero"),
    ]:
        solver = SearchAlgorithms(start, goal)
        path, full_path, cost = run_selected_algorithm(solver, algorithm, heuristic)
        print(algorithm + " Path: " + str(path))
        print("Full Path is: " + str(full_path))
        print(" + total Cost = " + str(cost))
        print("Stats: " + str(solver.last_stats))


def run_benchmark(start=DEFAULT_START, goal=GOAL):
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
        solver = SearchAlgorithms(start, goal)
        run_selected_algorithm(solver, algorithm, heuristic)
        rows.append(dict(solver.last_stats))
    return rows


def run_self_test():
    start = DEFAULT_START
    goal = GOAL

    for algorithm, heuristic in [
        ("UCS", "zero"),
        ("A*", "manhattan"),
        ("Greedy", "manhattan"),
        ("BFS", "zero"),
        ("DFS", "zero"),
    ]:
        solver = SearchAlgorithms(start, goal)
        path, full_path, cost = run_selected_algorithm(solver, algorithm, heuristic)
        assert full_path[0] == list(start)
        assert full_path[-1] == list(goal)
        assert cost == len(path)

    assert is_solvable([1, 2, 3, 4, 0, 6, 7, 5, 8], goal)
    assert not is_solvable([1, 2, 3, 4, 5, 6, 8, 7, 0], goal)
    return True


def build_parser():
    parser = argparse.ArgumentParser(description="Solve the 8-puzzle problem.")
    parser.add_argument("--cli", action="store_true", help="Run all algorithms on the default puzzle.")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark rows for all algorithms.")
    parser.add_argument("--self-test", action="store_true", help="Run simple solver tests.")
    parser.add_argument("--algorithm", choices=["UCS", "A*", "Greedy", "BFS", "DFS"], help="Run one algorithm.")
    parser.add_argument("--heuristic", default="manhattan", help="A* or Greedy heuristic.")
    parser.add_argument("--start", default=" ".join(str(tile) for tile in DEFAULT_START), help="Start puzzle.")
    parser.add_argument("--goal", default=" ".join(str(tile) for tile in GOAL), help="Goal puzzle.")
    return parser


def _run_from_args():
    parser = build_parser()
    args = parser.parse_args()
    start = validate_state(args.start, "start")
    goal = validate_state(args.goal, "goal")

    if args.self_test:
        run_self_test()
        print("Self-test passed.")
        return

    if args.benchmark:
        rows = run_benchmark(start, goal)
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
        solver = SearchAlgorithms(start, goal)
        path, full_path, cost = run_selected_algorithm(solver, args.algorithm, args.heuristic)
        print(args.algorithm + " Path: " + str(path))
        print("Full Path is: " + str(full_path))
        print(" + total Cost = " + str(cost))
        print("Stats: " + str(solver.last_stats))
        return

    run_demo(start, goal)
    
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
    _run_from_args()
