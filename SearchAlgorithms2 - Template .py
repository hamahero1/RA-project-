from __future__ import annotations

import heapq
import time
from collections import deque

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


def _minimum_conflict_removals(goal_indexes):
    """Return the fewest tiles to move out so the line is in goal order."""
    if not goal_indexes:
        return 0

    best = 1
    lengths = [1] * len(goal_indexes)
    for right in range(len(goal_indexes)):
        for left in range(right):
            if goal_indexes[left] < goal_indexes[right]:
                lengths[right] = max(lengths[right], lengths[left] + 1)
        best = max(best, lengths[right])
    return len(goal_indexes) - best


def _linear_conflict_penalty(state, goal_positions):
    conflicts = 0
    for row in range(BOARD_SIZE):
        row_tiles = state[row * BOARD_SIZE : (row + 1) * BOARD_SIZE]
        goal_columns = [
            goal_positions[tile][1]
            for tile in row_tiles
            if tile != 0 and goal_positions[tile][0] == row
        ]
        conflicts += _minimum_conflict_removals(goal_columns)

    for col in range(BOARD_SIZE):
        column_tiles = [state[row * BOARD_SIZE + col] for row in range(BOARD_SIZE)]
        goal_rows = [
            goal_positions[tile][0]
            for tile in column_tiles
            if tile != 0 and goal_positions[tile][1] == col
        ]
        conflicts += _minimum_conflict_removals(goal_rows)

    return 2 * conflicts


class SearchAlgorithms:
    """Required project class. Every algorithm method contains its own full code."""

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
        parsed_states = []
        for label, values in [("start", start), ("end", end)]:
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
            parsed_states.append(parsed)

        self.start = parsed_states[0]
        self.end = parsed_states[1]
        self.Path = []
        self.fullPath = []
        self.totalCost = -1
        self.heuristic_name = "manhattan"
        self.last_stats = {}

    def UCS(self):
        algorithm = "ucs"
        heuristic_name = "zero"
        started_at = time.perf_counter()

        def build_stats(solvable, success, expanded, generated, frontier_max, cost):
            return {
                "algorithm": algorithm,
                "heuristic": heuristic_name,
                "solvable": solvable,
                "success": success,
                "expanded": expanded,
                "generated": generated,
                "frontier_max": frontier_max,
                "cost": cost,
                "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
            }

        def get_inversions(state):
            tiles = [tile for tile in state if tile != 0]
            return sum(
                1
                for left in range(len(tiles))
                for right in range(left + 1, len(tiles))
                if tiles[left] > tiles[right]
            )

        # Part 1: solvability check.
        if get_inversions(self.start) % 2 != get_inversions(self.end) % 2:
            self.Path, self.fullPath, self.totalCost = [], [list(self.start)], -1
            self.last_stats = build_stats(False, False, 0, 1, 1, -1)
            return self.Path, self.fullPath, self.totalCost

        # Part 2: initialize.
        start_node = Node(list(self.start))
        start_node.state, start_node.parent = self.start, None
        start_node.parentstate, start_node.edgeCost = None, 0
        start_node.action, start_node.gOfN, start_node.hOfN = None, 0, 0
        start_node.heuristicFn = heuristic_name

        frontier = [(0, 0, 0, start_node)]
        best_g = {self.start: 0}
        counter = expanded = 0
        generated = frontier_max = 1

        # Part 3: search loop.
        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_g.get(current.state, float("inf")):
                continue

            if current.state == self.end:
                actions, states = [], []
                node = current
                while node:
                    states.append(list(node.state))
                    if node.action:
                        actions.append(node.action)
                    node = node.parent
                self.Path = actions[::-1]
                self.fullPath = states[::-1]
                self.totalCost = len(self.Path)
                self.last_stats = build_stats(True, True, expanded, generated, frontier_max, self.totalCost)
                return self.Path, self.fullPath, self.totalCost

            expanded += 1
            blank = current.state.index(0)
            row, col = divmod(blank, BOARD_SIZE)

            neighbors = []
            if row > 0:
                neighbors.append(("UP", blank - BOARD_SIZE))
            if row < BOARD_SIZE - 1:
                neighbors.append(("DOWN", blank + BOARD_SIZE))
            if col > 0:
                neighbors.append(("LEFT", blank - 1))
            if col < BOARD_SIZE - 1:
                neighbors.append(("RIGHT", blank + 1))

            for action, swap in neighbors:
                next_state = list(current.state)
                next_state[blank], next_state[swap] = next_state[swap], next_state[blank]
                next_state = tuple(next_state)
                new_g = current.gOfN + 1

                if new_g >= best_g.get(next_state, float("inf")):
                    continue

                child = Node(list(next_state))
                child.state, child.parent = next_state, current
                child.parentstate = list(current.state)
                child.edgeCost = 1
                child.action, child.gOfN, child.hOfN = action, new_g, 0
                child.heuristicFn = heuristic_name
                best_g[next_state] = new_g
                counter += 1
                generated += 1
                heapq.heappush(frontier, (new_g, 0, counter, child))

            frontier_max = max(frontier_max, len(frontier))

        # Part 4: failure.
        self.Path, self.fullPath, self.totalCost = [], [], -1
        self.last_stats = build_stats(True, False, expanded, generated, frontier_max, -1)
        return self.Path, self.fullPath, self.totalCost

    def Astar(self, heuristic=None):
        algorithm = "astar"
        heuristic_name = heuristic or self.heuristic_name
        heuristic_name = str(heuristic_name).strip().lower().replace("-", "_").replace(" ", "_")
        heuristic_aliases = {
            "h1": "misplaced",
            "misplaced_tiles": "misplaced",
            "h2": "manhattan",
            "manhattan_distance": "manhattan",
            "h3": "linear_conflict",
            "linear": "linear_conflict",
        }
        heuristic_name = heuristic_aliases.get(heuristic_name, heuristic_name)
        started_at = time.perf_counter()

        # Part 1: check if this puzzle can reach the goal.
        start_tiles = [tile for tile in self.start if tile != 0]
        goal_tiles = [tile for tile in self.end if tile != 0]
        start_inversions = 0
        goal_inversions = 0
        for left in range(len(start_tiles)):
            for right in range(left + 1, len(start_tiles)):
                if start_tiles[left] > start_tiles[right]:
                    start_inversions += 1
                if goal_tiles[left] > goal_tiles[right]:
                    goal_inversions += 1

        if start_inversions % 2 != goal_inversions % 2:
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
                "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
            }
            return self.Path, self.fullPath, self.totalCost

        # Part 2: calculate the selected heuristic for the start state.
        goal_positions = {tile: divmod(index, BOARD_SIZE) for index, tile in enumerate(self.end)}
        start_h = 0
        if heuristic_name == "misplaced":
            for index, tile in enumerate(self.start):
                if tile != 0 and tile != self.end[index]:
                    start_h += 1
        elif heuristic_name in {"manhattan", "linear_conflict"}:
            for index, tile in enumerate(self.start):
                if tile == 0:
                    continue
                row, col = divmod(index, BOARD_SIZE)
                goal_row, goal_col = goal_positions[tile]
                start_h += abs(row - goal_row) + abs(col - goal_col)

            if heuristic_name == "linear_conflict":
                start_h += _linear_conflict_penalty(self.start, goal_positions)
        else:
            raise ValueError("Unknown heuristic: " + str(heuristic_name))

        # Part 3: create the start node and A* priority queue.
        start_node = Node(list(self.start))
        start_node.state = self.start
        start_node.parent = None
        start_node.parentstate = None
        start_node.action = None
        start_node.edgeCost = 0
        start_node.gOfN = 0
        start_node.hOfN = start_h
        start_node.heuristicFn = heuristic_name

        frontier = []
        heapq.heappush(frontier, (start_h, start_h, 0, start_node))
        best_cost_to_state = {self.start: 0}
        counter = 0
        expanded = 0
        generated = 1
        frontier_max = 1

        # Part 4: run A* with f(n) = g(n) + h(n).
        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_cost_to_state.get(current.state, 999999999):
                continue

            if current.state == self.end:
                # Part 5: rebuild path, fullPath, cost, and statistics.
                actions = []
                states = []
                node = current
                while node is not None:
                    states.append(list(node.state))
                    if node.action is not None:
                        actions.append(node.action)
                    node = node.parent
                actions.reverse()
                states.reverse()
                self.Path = actions
                self.fullPath = states
                self.totalCost = len(actions)
                self.last_stats = {
                    "algorithm": algorithm,
                    "heuristic": heuristic_name,
                    "solvable": True,
                    "success": True,
                    "expanded": expanded,
                    "generated": generated,
                    "frontier_max": frontier_max,
                    "cost": self.totalCost,
                    "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
                return self.Path, self.fullPath, self.totalCost

            expanded += 1
            blank = current.state.index(0)
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

            for action, swap_index in moves:
                next_state = list(current.state)
                next_state[blank], next_state[swap_index] = next_state[swap_index], next_state[blank]
                next_state = tuple(next_state)
                new_cost = current.gOfN + 1
                if new_cost >= best_cost_to_state.get(next_state, 999999999):
                    continue

                next_h = 0
                if heuristic_name == "misplaced":
                    for index, tile in enumerate(next_state):
                        if tile != 0 and tile != self.end[index]:
                            next_h += 1
                elif heuristic_name in {"manhattan", "linear_conflict"}:
                    for index, tile in enumerate(next_state):
                        if tile == 0:
                            continue
                        current_row, current_col = divmod(index, BOARD_SIZE)
                        goal_row, goal_col = goal_positions[tile]
                        next_h += abs(current_row - goal_row) + abs(current_col - goal_col)

                    if heuristic_name == "linear_conflict":
                        next_h += _linear_conflict_penalty(next_state, goal_positions)

                child = Node(list(next_state))
                child.state = next_state
                child.parent = current
                child.parentstate = list(current.state)
                child.action = action
                child.edgeCost = 1
                child.gOfN = new_cost
                child.hOfN = next_h
                child.heuristicFn = heuristic_name
                best_cost_to_state[next_state] = new_cost
                counter += 1
                generated += 1
                heapq.heappush(frontier, (new_cost + next_h, next_h, counter, child))

            frontier_max = max(frontier_max, len(frontier))

        # Part 6: return failure if the queue ends without the goal.
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
            "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
        }
        return self.Path, self.fullPath, self.totalCost

    def Greedy(self, heuristic=None):
        algorithm = "greedy"
        heuristic_name = heuristic or self.heuristic_name
        heuristic_name = str(heuristic_name).strip().lower().replace("-", "_").replace(" ", "_")
        heuristic_aliases = {
            "h1": "misplaced",
            "misplaced_tiles": "misplaced",
            "h2": "manhattan",
            "manhattan_distance": "manhattan",
            "h3": "linear_conflict",
            "linear": "linear_conflict",
        }
        heuristic_name = heuristic_aliases.get(heuristic_name, heuristic_name)
        started_at = time.perf_counter()

        # Part 1: check if this puzzle can reach the goal.
        start_tiles = [tile for tile in self.start if tile != 0]
        goal_tiles = [tile for tile in self.end if tile != 0]
        start_inversions = 0
        goal_inversions = 0
        for left in range(len(start_tiles)):
            for right in range(left + 1, len(start_tiles)):
                if start_tiles[left] > start_tiles[right]:
                    start_inversions += 1
                if goal_tiles[left] > goal_tiles[right]:
                    goal_inversions += 1

        if start_inversions % 2 != goal_inversions % 2:
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
                "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
            }
            return self.Path, self.fullPath, self.totalCost

        # Part 2: calculate the selected heuristic for the start state.
        goal_positions = {tile: divmod(index, BOARD_SIZE) for index, tile in enumerate(self.end)}
        start_h = 0
        if heuristic_name == "misplaced":
            for index, tile in enumerate(self.start):
                if tile != 0 and tile != self.end[index]:
                    start_h += 1
        elif heuristic_name in {"manhattan", "linear_conflict"}:
            for index, tile in enumerate(self.start):
                if tile == 0:
                    continue
                row, col = divmod(index, BOARD_SIZE)
                goal_row, goal_col = goal_positions[tile]
                start_h += abs(row - goal_row) + abs(col - goal_col)

            if heuristic_name == "linear_conflict":
                start_h += _linear_conflict_penalty(self.start, goal_positions)
        else:
            raise ValueError("Unknown heuristic: " + str(heuristic_name))

        # Part 3: create the start node and Greedy priority queue.
        start_node = Node(list(self.start))
        start_node.state = self.start
        start_node.parent = None
        start_node.parentstate = None
        start_node.action = None
        start_node.edgeCost = 0
        start_node.gOfN = 0
        start_node.hOfN = start_h
        start_node.heuristicFn = heuristic_name

        frontier = []
        heapq.heappush(frontier, (start_h, 0, 0, start_node))
        best_cost_to_state = {self.start: 0}
        counter = 0
        expanded = 0
        generated = 1
        frontier_max = 1

        # Part 4: run Greedy Best-First Search with h(n) as the priority.
        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_cost_to_state.get(current.state, 999999999):
                continue

            if current.state == self.end:
                # Part 5: rebuild path, fullPath, cost, and statistics.
                actions = []
                states = []
                node = current
                while node is not None:
                    states.append(list(node.state))
                    if node.action is not None:
                        actions.append(node.action)
                    node = node.parent
                actions.reverse()
                states.reverse()
                self.Path = actions
                self.fullPath = states
                self.totalCost = len(actions)
                self.last_stats = {
                    "algorithm": algorithm,
                    "heuristic": heuristic_name,
                    "solvable": True,
                    "success": True,
                    "expanded": expanded,
                    "generated": generated,
                    "frontier_max": frontier_max,
                    "cost": self.totalCost,
                    "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
                return self.Path, self.fullPath, self.totalCost

            expanded += 1
            blank = current.state.index(0)
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

            for action, swap_index in moves:
                next_state = list(current.state)
                next_state[blank], next_state[swap_index] = next_state[swap_index], next_state[blank]
                next_state = tuple(next_state)
                new_cost = current.gOfN + 1
                if new_cost >= best_cost_to_state.get(next_state, 999999999):
                    continue

                next_h = 0
                if heuristic_name == "misplaced":
                    for index, tile in enumerate(next_state):
                        if tile != 0 and tile != self.end[index]:
                            next_h += 1
                elif heuristic_name in {"manhattan", "linear_conflict"}:
                    for index, tile in enumerate(next_state):
                        if tile == 0:
                            continue
                        current_row, current_col = divmod(index, BOARD_SIZE)
                        goal_row, goal_col = goal_positions[tile]
                        next_h += abs(current_row - goal_row) + abs(current_col - goal_col)

                    if heuristic_name == "linear_conflict":
                        next_h += _linear_conflict_penalty(next_state, goal_positions)

                child = Node(list(next_state))
                child.state = next_state
                child.parent = current
                child.parentstate = list(current.state)
                child.action = action
                child.edgeCost = 1
                child.gOfN = new_cost
                child.hOfN = next_h
                child.heuristicFn = heuristic_name
                best_cost_to_state[next_state] = new_cost
                counter += 1
                generated += 1
                heapq.heappush(frontier, (next_h, new_cost, counter, child))

            frontier_max = max(frontier_max, len(frontier))

        # Part 6: return failure if the queue ends without the goal.
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
            "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
        }
        return self.Path, self.fullPath, self.totalCost

    def BFS(self):
        algorithm = "bfs"
        heuristic_name = "not_used"
        started_at = time.perf_counter()

        # Part 1: check if this puzzle can reach the goal.
        start_tiles = [tile for tile in self.start if tile != 0]
        goal_tiles = [tile for tile in self.end if tile != 0]
        start_inversions = 0
        goal_inversions = 0
        for left in range(len(start_tiles)):
            for right in range(left + 1, len(start_tiles)):
                if start_tiles[left] > start_tiles[right]:
                    start_inversions += 1
                if goal_tiles[left] > goal_tiles[right]:
                    goal_inversions += 1

        if start_inversions % 2 != goal_inversions % 2:
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
                "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
            }
            return self.Path, self.fullPath, self.totalCost

        # Part 2: create the start node and FIFO queue.
        start_node = Node(list(self.start))
        start_node.state = self.start
        start_node.parent = None
        start_node.parentstate = None
        start_node.action = None
        start_node.edgeCost = 0
        start_node.gOfN = 0
        start_node.hOfN = 0
        start_node.heuristicFn = heuristic_name

        frontier = deque([start_node])
        discovered_states = {self.start}
        expanded = 0
        generated = 1
        frontier_max = 1

        # Part 3: run BFS level by level.
        while frontier:
            current = frontier.popleft()
            if current.state == self.end:
                # Part 4: rebuild path, fullPath, cost, and statistics.
                actions = []
                states = []
                node = current
                while node is not None:
                    states.append(list(node.state))
                    if node.action is not None:
                        actions.append(node.action)
                    node = node.parent
                actions.reverse()
                states.reverse()
                self.Path = actions
                self.fullPath = states
                self.totalCost = len(actions)
                self.last_stats = {
                    "algorithm": algorithm,
                    "heuristic": heuristic_name,
                    "solvable": True,
                    "success": True,
                    "expanded": expanded,
                    "generated": generated,
                    "frontier_max": frontier_max,
                    "cost": self.totalCost,
                    "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
                return self.Path, self.fullPath, self.totalCost

            expanded += 1
            blank = current.state.index(0)
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

            for action, swap_index in moves:
                next_state = list(current.state)
                next_state[blank], next_state[swap_index] = next_state[swap_index], next_state[blank]
                next_state = tuple(next_state)
                if next_state in discovered_states:
                    continue

                child = Node(list(next_state))
                child.state = next_state
                child.parent = current
                child.parentstate = list(current.state)
                child.action = action
                child.edgeCost = 1
                child.gOfN = current.gOfN + 1
                child.hOfN = 0
                child.heuristicFn = heuristic_name
                discovered_states.add(next_state)
                generated += 1
                frontier.append(child)

            frontier_max = max(frontier_max, len(frontier))

        # Part 5: return failure if the queue ends without the goal.
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
            "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
        }
        return self.Path, self.fullPath, self.totalCost

    def DFS(self):
        algorithm = "dfs"
        heuristic_name = "not_used"
        started_at = time.perf_counter()

        # Part 1: check if this puzzle can reach the goal.
        start_tiles = [tile for tile in self.start if tile != 0]
        goal_tiles = [tile for tile in self.end if tile != 0]
        start_inversions = 0
        goal_inversions = 0
        for left in range(len(start_tiles)):
            for right in range(left + 1, len(start_tiles)):
                if start_tiles[left] > start_tiles[right]:
                    start_inversions += 1
                if goal_tiles[left] > goal_tiles[right]:
                    goal_inversions += 1

        if start_inversions % 2 != goal_inversions % 2:
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
                "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
            }
            return self.Path, self.fullPath, self.totalCost

        # Part 2: create the start node and stack.
        start_node = Node(list(self.start))
        start_node.state = self.start
        start_node.parent = None
        start_node.parentstate = None
        start_node.action = None
        start_node.edgeCost = 0
        start_node.gOfN = 0
        start_node.hOfN = 0
        start_node.heuristicFn = heuristic_name

        frontier = [start_node]
        discovered_states = {self.start}
        expanded = 0
        generated = 1
        frontier_max = 1

        # Part 3: run DFS with a stack.
        while frontier:
            current = frontier.pop()
            if current.state == self.end:
                # Part 4: rebuild path, fullPath, cost, and statistics.
                actions = []
                states = []
                node = current
                while node is not None:
                    states.append(list(node.state))
                    if node.action is not None:
                        actions.append(node.action)
                    node = node.parent
                actions.reverse()
                states.reverse()
                self.Path = actions
                self.fullPath = states
                self.totalCost = len(actions)
                self.last_stats = {
                    "algorithm": algorithm,
                    "heuristic": heuristic_name,
                    "solvable": True,
                    "success": True,
                    "expanded": expanded,
                    "generated": generated,
                    "frontier_max": frontier_max,
                    "cost": self.totalCost,
                    "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
                }
                return self.Path, self.fullPath, self.totalCost

            expanded += 1
            blank = current.state.index(0)
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

            for action, swap_index in reversed(moves):
                next_state = list(current.state)
                next_state[blank], next_state[swap_index] = next_state[swap_index], next_state[blank]
                next_state = tuple(next_state)
                if next_state in discovered_states:
                    continue

                child = Node(list(next_state))
                child.state = next_state
                child.parent = current
                child.parentstate = list(current.state)
                child.action = action
                child.edgeCost = 1
                child.gOfN = current.gOfN + 1
                child.hOfN = 0
                child.heuristicFn = heuristic_name
                discovered_states.add(next_state)
                generated += 1
                frontier.append(child)

            frontier_max = max(frontier_max, len(frontier))

        # Part 5: return failure if the stack ends without the goal.
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
            "runtime_ms": round((time.perf_counter() - started_at) * 1000, 3),
        }
        return self.Path, self.fullPath, self.totalCost


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


if __name__ == "__main__":
    main()
