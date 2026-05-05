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
    gOfN = None
    hOfN = None
    heuristicFn = None

    def __init__(
        self,
        value: Sequence[int],
        parent: Node | None = None,
        action: str | None = None,
        edgeCost: int = 0,
        gOfN: int = 0,
        hOfN: int = 0,
        heuristicFn: str | None = None,
    ):
        self.state = tuple(value)
        self.value = list(self.state)
        self.parent = parent
        self.parentstate = list(parent.state) if parent else None
        self.action = action
        self.edgeCost = edgeCost
        self.gOfN = gOfN
        self.hOfN = hOfN
        self.heuristicFn = heuristicFn


def validate_state(values: Sequence[int] | str, label: str = "state") -> State:
    if isinstance(values, str):
        cleaned = values.replace(",", " ").replace(";", " ")
        try:
            parts = cleaned.split()
            if len(parts) == 1 and len(parts[0]) == TILE_COUNT and parts[0].isdigit():
                parsed = tuple(int(part) for part in parts[0])
            else:
                parsed = tuple(int(part) for part in parts)
        except ValueError as exc:
            raise ValueError(f"{label} must contain only numbers from 0 to 8.") from exc
    else:
        parsed = tuple(int(value) for value in values)

    if len(parsed) != TILE_COUNT:
        raise ValueError(f"{label} must contain exactly 9 numbers.")
    if sorted(parsed) != list(range(TILE_COUNT)):
        raise ValueError(f"{label} must contain each number from 0 to 8 exactly once.")
    return parsed


def format_state(state: Sequence[int]) -> str:
    rows = []
    for row in range(BOARD_SIZE):
        start = row * BOARD_SIZE
        rows.append(" ".join(str(tile) for tile in state[start : start + BOARD_SIZE]))
    return "\n".join(rows)


def count_inversions(state: Sequence[int]) -> int:
    tiles = [tile for tile in state if tile != 0]
    return sum(
        1
        for left_index in range(len(tiles))
        for right_index in range(left_index + 1, len(tiles))
        if tiles[left_index] > tiles[right_index]
    )


def is_solvable(start: Sequence[int], goal: Sequence[int] = GOAL) -> bool:
    start_state = validate_state(start, "start")
    goal_state = validate_state(goal, "goal")
    return count_inversions(start_state) % 2 == count_inversions(goal_state) % 2


def goal_positions(goal: Sequence[int]) -> dict[int, tuple[int, int]]:
    return {
        tile: divmod(index, BOARD_SIZE)
        for index, tile in enumerate(goal)
    }


def misplaced(state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
    state = validate_state(state)
    goal = validate_state(goal, "goal")
    return sum(tile != 0 and tile != goal[index] for index, tile in enumerate(state))


def manhattan(state: Sequence[int], goal: Sequence[int] = GOAL) -> int:
    state = validate_state(state)
    positions = goal_positions(validate_state(goal, "goal"))
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
    return sum(
        1
        for left_index in range(len(values))
        for right_index in range(left_index + 1, len(values))
        if values[left_index] > values[right_index]
    )


def successors(state: Sequence[int]) -> list[tuple[str, State]]:
    state = tuple(state)
    blank = state.index(0)
    row, col = divmod(blank, BOARD_SIZE)
    moves: list[tuple[str, int]] = []

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

    def __init__(self, start: Sequence[int], end: Sequence[int]):
        self.start = validate_state(start, "start")
        self.end = validate_state(end, "end")
        self.Path: list[str] = []
        self.fullPath: list[list[int]] = []
        self.totalCost = -1
        self.heuristic_name = "manhattan"
        self.last_stats: dict[str, int | float | str | bool] = {}

    def UCS(self):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("ucs", "zero", started_at)

        frontier: list[tuple[int, int, int, Node]] = []
        start_node = Node(self.start, gOfN=0, hOfN=0, heuristicFn="zero")
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
                child = Node(
                    next_state,
                    parent=current,
                    action=action,
                    edgeCost=1,
                    gOfN=new_cost,
                    hOfN=0,
                    heuristicFn="zero",
                )
                heapq.heappush(frontier, (new_cost, 0, counter, child))
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("ucs", "zero", started_at, expanded, generated, frontier_max)

    def Astar(self, heuristic: str | None = None):
        heuristic_name = heuristic or self.heuristic_name
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("astar", heuristic_name, started_at)

        start_h = self._heuristic(self.start, heuristic_name)
        frontier: list[tuple[int, int, int, Node]] = []
        start_node = Node(self.start, gOfN=0, hOfN=start_h, heuristicFn=heuristic_name)
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
                child = Node(
                    next_state,
                    parent=current,
                    action=action,
                    edgeCost=1,
                    gOfN=new_cost,
                    hOfN=next_h,
                    heuristicFn=heuristic_name,
                )
                heapq.heappush(frontier, (new_cost + next_h, next_h, counter, child))
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("astar", heuristic_name, started_at, expanded, generated, frontier_max)

    def Greedy(self, heuristic: str | None = None):
        heuristic_name = heuristic or self.heuristic_name
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("greedy", heuristic_name, started_at)

        start_h = self._heuristic(self.start, heuristic_name)
        frontier: list[tuple[int, int, int, Node]] = []
        start_node = Node(self.start, gOfN=0, hOfN=start_h, heuristicFn=heuristic_name)
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
                child = Node(
                    next_state,
                    parent=current,
                    action=action,
                    edgeCost=1,
                    gOfN=new_cost,
                    hOfN=next_h,
                    heuristicFn=heuristic_name,
                )
                heapq.heappush(frontier, (next_h, new_cost, counter, child))
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("greedy", heuristic_name, started_at, expanded, generated, frontier_max)

    def BFS(self):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("bfs", "not_used", started_at)

        start_node = Node(self.start, gOfN=0, hOfN=0, heuristicFn="not_used")
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
                child = Node(
                    next_state,
                    parent=current,
                    action=action,
                    edgeCost=1,
                    gOfN=current.gOfN + 1,
                    hOfN=0,
                    heuristicFn="not_used",
                )
                frontier.append(child)
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("bfs", "not_used", started_at, expanded, generated, frontier_max)

    def DFS(self):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
            return self._finish_unsolvable("dfs", "not_used", started_at)

        start_node = Node(self.start, gOfN=0, hOfN=0, heuristicFn="not_used")
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
                child = Node(
                    next_state,
                    parent=current,
                    action=action,
                    edgeCost=1,
                    gOfN=current.gOfN + 1,
                    hOfN=0,
                    heuristicFn="not_used",
                )
                frontier.append(child)
            frontier_max = max(frontier_max, len(frontier))

        return self._finish_failure("dfs", "not_used", started_at, expanded, generated, frontier_max)

    def _heuristic(self, state: State, heuristic_name: str) -> int:
        key = normalize_heuristic_name(heuristic_name)
        if key == "zero":
            return 0
        if key == "misplaced":
            return misplaced(state, self.end)
        if key == "manhattan":
            return manhattan(state, self.end)
        if key == "linear_conflict":
            return linear_conflict(state, self.end)
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    def _finish_unsolvable(self, algorithm: str, heuristic_name: str, started_at: float):
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

    def _finish_success(
        self,
        goal_node: Node,
        algorithm: str,
        heuristic_name: str,
        started_at: float,
        expanded: int,
        generated: int,
        frontier_max: int,
    ):
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

    def _finish_failure(
        self,
        algorithm: str,
        heuristic_name: str,
        started_at: float,
        expanded: int,
        generated: int,
        frontier_max: int,
    ):
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
    def _reconstruct(node: Node) -> tuple[list[str], list[list[int]], int]:
        actions: list[str] = []
        states: list[list[int]] = []
        current: Node | None = node

        while current is not None:
            states.append(list(current.state))
            if current.action is not None:
                actions.append(current.action)
            current = current.parent

        actions.reverse()
        states.reverse()
        return actions, states, len(actions)


def _elapsed_ms(started_at: float) -> float:
    return round((time.perf_counter() - started_at) * 1000, 3)


def normalize_heuristic_name(name: str | None) -> str:
    if not name:
        return "manhattan"
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "h1": "misplaced",
        "misplaced_tiles": "misplaced",
        "h2": "manhattan",
        "manhattan_distance": "manhattan",
        "h3": "linear_conflict",
        "linear": "linear_conflict",
        "linear_conflict": "linear_conflict",
        "zero": "zero",
        "none": "zero",
        "not_used": "zero",
    }
    return aliases.get(key, key)


def heuristic_values(state: Sequence[int], goal: Sequence[int] = GOAL) -> dict[str, int]:
    return {
        "misplaced": misplaced(state, goal),
        "manhattan": manhattan(state, goal),
        "linear_conflict": linear_conflict(state, goal),
    }


def run_selected_algorithm(
    solver: SearchAlgorithms,
    algorithm: str,
    heuristic: str = "manhattan",
) -> tuple[list[str], list[list[int]], int]:
    normalized = algorithm.strip().lower().replace("*", "star")
    if normalized == "ucs":
        return solver.UCS()
    if normalized in {"astar", "a star", "a_star"}:
        return solver.Astar(heuristic)
    if normalized == "greedy":
        return solver.Greedy(heuristic)
    if normalized == "bfs":
        return solver.BFS()
    if normalized == "dfs":
        return solver.DFS()
    raise ValueError(f"Unknown algorithm: {algorithm}")


def run_demo(start: State = DEFAULT_START, goal: State = GOAL):
    print("Start state:")
    print(format_state(start))
    print("\nGoal state:")
    print(format_state(goal))
    print()

    for algorithm, heuristic in [
        ("UCS", "zero"),
        ("A*", "manhattan"),
        ("Greedy", "manhattan"),
        ("BFS", "zero"),
        ("DFS", "zero"),
    ]:
        solver = SearchAlgorithms(start, goal)
        path, full_path, cost = run_selected_algorithm(solver, algorithm, heuristic)
        print(f"{algorithm} ({heuristic})")
        print(f"Path: {path}")
        print(f"Full path: {full_path}")
        print(f"Total cost: {cost}")
        print(f"Stats: {solver.last_stats}")
        print()


def run_benchmark(start: State = DEFAULT_START, goal: State = GOAL):
    jobs = [
        ("UCS", "not used"),
        ("A*", "misplaced"),
        ("A*", "manhattan"),
        ("A*", "linear_conflict"),
        ("Greedy", "misplaced"),
        ("Greedy", "manhattan"),
        ("Greedy", "linear_conflict"),
    ]
    print(f"{'Algorithm':<10} {'Heuristic':<16} {'Cost':>5} {'Expanded':>10} {'Generated':>10} {'Runtime ms':>11}")
    print("-" * 70)
    for algorithm, heuristic in jobs:
        solver = SearchAlgorithms(start, goal)
        search_heuristic = "zero" if algorithm == "UCS" else heuristic
        _, _, cost = run_selected_algorithm(solver, algorithm, search_heuristic)
        stats = solver.last_stats
        print(
            f"{algorithm:<10} {heuristic:<16} {cost:>5} "
            f"{stats['expanded']:>10} {stats['generated']:>10} {stats['runtime_ms']:>11}"
        )


def run_self_test():
    sample = DEFAULT_START
    assert validate_state("123406758") == sample
    assert validate_state("1 2 3 4 0 6 7 5 8") == sample
    assert is_solvable(sample, GOAL)
    values = heuristic_values(sample, GOAL)
    assert values["linear_conflict"] >= values["manhattan"] >= values["misplaced"]

    ucs = SearchAlgorithms(sample, GOAL)
    _, full_path, cost = ucs.UCS()
    assert cost == 2
    assert full_path[0] == list(sample)
    assert full_path[-1] == list(GOAL)

    astar = SearchAlgorithms(sample, GOAL)
    _, _, astar_cost = astar.Astar("manhattan")
    assert astar_cost == cost

    unsolvable = (1, 2, 3, 4, 5, 6, 8, 7, 0)
    fail = SearchAlgorithms(unsolvable, GOAL)
    _, _, fail_cost = fail.Astar("manhattan")
    assert fail_cost == -1

    bfs = SearchAlgorithms(sample, GOAL)
    _, _, bfs_cost = bfs.BFS()
    assert bfs_cost == cost

    dfs = SearchAlgorithms(sample, GOAL)
    _, _, dfs_cost = dfs.DFS()
    assert dfs_cost >= cost
    print("Self-test passed.")




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8-puzzle solver using UCS, A*, and Greedy search.")
    parser.add_argument("--cli", action="store_true", help="Run the command-line demo.")
    parser.add_argument("--benchmark", action="store_true", help="Run all algorithm and heuristic combinations.")
    parser.add_argument("--self-test", action="store_true", help="Run quick correctness checks.")
    parser.add_argument("--start", default=" ".join(str(tile) for tile in DEFAULT_START), help="Start state, for example: '1 2 3 4 0 6 7 5 8' or '123406758'.")
    parser.add_argument("--goal", default=" ".join(str(tile) for tile in GOAL), help="Goal state, for example: '1 2 3 4 5 6 7 8 0' or '123456780'.")
    parser.add_argument("--algorithm", choices=["UCS", "A*", "Greedy", "BFS", "DFS"], help="Run one algorithm.")
    parser.add_argument("--heuristic", default="manhattan", choices=["misplaced", "manhattan", "linear_conflict"], help="Heuristic for A* or Greedy.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    start = validate_state(args.start, "start")
    goal = validate_state(args.goal, "goal")

    if args.self_test:
        run_self_test()
        return

    if args.benchmark:
        run_benchmark(start, goal)
        return

    if args.algorithm:
        solver = SearchAlgorithms(start, goal)
        path, full_path, cost = run_selected_algorithm(solver, args.algorithm, args.heuristic)
        print(f"{args.algorithm} Path: {path}")
        print(f"Full Path: {full_path}")
        print(f"Total Cost: {cost}")
        print(f"Stats: {solver.last_stats}")
        return

    run_demo(start, goal)


if __name__ == "__main__":
    main()
