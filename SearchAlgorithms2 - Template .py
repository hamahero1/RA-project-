from __future__ import annotations

import argparse
import heapq
import random
import sys
import time
from collections.abc import Iterable, Sequence
from typing import Callable

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # Allows command-line use on systems without Tk installed.
    tk = None
    ttk = None
    messagebox = None


BOARD_SIZE = 3
TILE_COUNT = BOARD_SIZE * BOARD_SIZE
GOAL = (1, 2, 3, 4, 5, 6, 7, 8, 0)
DEFAULT_START = (1, 2, 3, 4, 0, 6, 7, 5, 8)

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
            parsed = tuple(int(part) for part in cleaned.split())
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
        return self._search("ucs", "zero")

    def Astar(self, heuristic: str | None = None):
        return self._search("astar", heuristic or self.heuristic_name)

    def Greedy(self, heuristic: str | None = None):
        return self._search("greedy", heuristic or self.heuristic_name)

    def _search(self, algorithm: str, heuristic_name: str):
        started_at = time.perf_counter()
        if not is_solvable(self.start, self.end):
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

        start_h = self._heuristic(self.start, heuristic_name)
        start_node = Node(self.start, gOfN=0, hOfN=start_h, heuristicFn=heuristic_name)
        frontier: list[tuple[int, int, int, Node]] = []
        counter = 0
        heapq.heappush(frontier, (self._priority(algorithm, 0, start_h), start_h, counter, start_node))
        best_g = {self.start: 0}
        expanded = 0
        generated = 1
        frontier_max = 1

        while frontier:
            _, _, _, current = heapq.heappop(frontier)
            if current.gOfN > best_g.get(current.state, sys.maxsize):
                continue

            if current.state == self.end:
                self.Path, self.fullPath, self.totalCost = self._reconstruct(current)
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

            expanded += 1
            for action, next_state in successors(current.state):
                new_g = current.gOfN + 1
                if new_g >= best_g.get(next_state, sys.maxsize):
                    continue

                best_g[next_state] = new_g
                next_h = self._heuristic(next_state, heuristic_name)
                counter += 1
                generated += 1
                child = Node(
                    next_state,
                    parent=current,
                    action=action,
                    edgeCost=1,
                    gOfN=new_g,
                    hOfN=next_h,
                    heuristicFn=heuristic_name,
                )
                heapq.heappush(
                    frontier,
                    (self._priority(algorithm, new_g, next_h), next_h, counter, child),
                )
            frontier_max = max(frontier_max, len(frontier))

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

    @staticmethod
    def _priority(algorithm: str, g_value: int, h_value: int) -> int:
        if algorithm == "ucs":
            return g_value
        if algorithm == "astar":
            return g_value + h_value
        if algorithm == "greedy":
            return h_value
        raise ValueError(f"Unknown algorithm: {algorithm}")

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
    }
    return aliases.get(key, key)


def heuristic_values(state: Sequence[int], goal: Sequence[int] = GOAL) -> dict[str, int]:
    return {
        "misplaced": misplaced(state, goal),
        "manhattan": manhattan(state, goal),
        "linear_conflict": linear_conflict(state, goal),
    }


class EightPuzzleApp:
    def __init__(self, root):
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter is not available on this Python installation.")

        self.root = root
        self.state = DEFAULT_START
        self.goal = GOAL
        self.solution_states: list[list[int]] = []
        self.solution_actions: list[str] = []
        self.solution_index = 0
        self.animating = False
        self.tile_buttons: list[tk.Button] = []
        self.stat_vars: dict[str, tk.StringVar] = {}
        self.heuristic_vars: dict[str, tk.StringVar] = {}

        self._configure_window()
        self._build_layout()
        self._render_state()

    def _configure_window(self):
        self.root.title("8-Puzzle Solver")
        self.root.geometry("1040x680")
        self.root.minsize(920, 600)
        self.root.configure(bg="#f4f6f8")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6f8")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TLabel", background="#f4f6f8", foreground="#172033", font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#172033", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#f4f6f8", foreground="#111827", font=("Segoe UI", 20, "bold"))
        style.configure("Small.TLabel", background="#ffffff", foreground="#5b6575", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 7))
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_layout(self):
        shell = ttk.Frame(self.root, padding=22)
        shell.pack(fill=tk.BOTH, expand=True)
        shell.columnconfigure(0, weight=1)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(1, weight=1)

        ttk.Label(shell, text="8-Puzzle Solver", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(shell, textvariable=self.status_var).grid(row=0, column=1, sticky="e")

        left = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        left.grid(row=1, column=0, sticky="nsew", pady=(18, 0), padx=(0, 12))
        left.columnconfigure(0, weight=1)

        board_frame = ttk.Frame(left, style="Panel.TFrame")
        board_frame.grid(row=0, column=0, pady=(0, 18))
        for index in range(TILE_COUNT):
            button = tk.Button(
                board_frame,
                width=5,
                height=2,
                bd=0,
                relief=tk.FLAT,
                font=("Segoe UI", 24, "bold"),
                command=lambda i=index: self._move_clicked_tile(i),
            )
            button.grid(row=index // BOARD_SIZE, column=index % BOARD_SIZE, padx=6, pady=6, sticky="nsew")
            self.tile_buttons.append(button)

        state_panel = ttk.Frame(left, style="Panel.TFrame")
        state_panel.grid(row=1, column=0, sticky="ew")
        state_panel.columnconfigure(0, weight=1)
        ttk.Label(state_panel, text="State input", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        self.state_entry = ttk.Entry(state_panel)
        self.state_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 10))
        self.state_entry.insert(0, " ".join(str(tile) for tile in self.state))
        ttk.Button(state_panel, text="Load", command=self._load_state).grid(row=2, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(state_panel, text="Shuffle", command=self._shuffle).grid(row=2, column=1, sticky="ew", padx=6)
        ttk.Button(state_panel, text="Reset", command=self._reset).grid(row=2, column=2, sticky="ew", padx=(6, 0))

        h_panel = ttk.Frame(left, style="Panel.TFrame")
        h_panel.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        h_panel.columnconfigure((0, 1, 2), weight=1)
        for column, (key, label) in enumerate(
            [
                ("misplaced", "h1 misplaced"),
                ("manhattan", "h2 manhattan"),
                ("linear_conflict", "h3 conflict"),
            ]
        ):
            self.heuristic_vars[key] = tk.StringVar(value="0")
            box = ttk.Frame(h_panel, style="Panel.TFrame")
            box.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0))
            ttk.Label(box, text=label, style="Small.TLabel").pack(anchor="w")
            ttk.Label(box, textvariable=self.heuristic_vars[key], style="Panel.TLabel", font=("Segoe UI", 18, "bold")).pack(anchor="w")

        right = ttk.Frame(shell, style="Panel.TFrame", padding=18)
        right.grid(row=1, column=1, sticky="nsew", pady=(18, 0), padx=(12, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        controls = ttk.Frame(right, style="Panel.TFrame")
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure((0, 1), weight=1)

        ttk.Label(controls, text="Algorithm", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        self.algorithm_combo = ttk.Combobox(controls, state="readonly", values=["UCS", "A*", "Greedy"])
        self.algorithm_combo.current(1)
        self.algorithm_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(4, 10))

        ttk.Label(controls, text="Heuristic", style="Panel.TLabel").grid(row=0, column=1, sticky="w")
        self.heuristic_combo = ttk.Combobox(
            controls,
            state="readonly",
            values=["misplaced", "manhattan", "linear_conflict"],
        )
        self.heuristic_combo.current(1)
        self.heuristic_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(4, 10))

        ttk.Button(controls, text="Solve", style="Primary.TButton", command=self._solve).grid(row=2, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(controls, text="Step", command=self._step_solution).grid(row=2, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(controls, text="Animate", command=self._animate_solution).grid(row=3, column=0, sticky="ew", padx=(0, 8), pady=(10, 0))
        ttk.Button(controls, text="Benchmark", command=self._benchmark).grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(10, 0))

        stats = ttk.Frame(right, style="Panel.TFrame")
        stats.grid(row=1, column=0, sticky="ew", pady=(18, 0))
        stats.columnconfigure((0, 1, 2, 3), weight=1)
        for column, key in enumerate(["cost", "expanded", "generated", "runtime_ms"]):
            self.stat_vars[key] = tk.StringVar(value="-")
            ttk.Label(stats, text=key.replace("_", " "), style="Small.TLabel").grid(row=0, column=column, sticky="w")
            ttk.Label(stats, textvariable=self.stat_vars[key], style="Panel.TLabel", font=("Segoe UI", 12, "bold")).grid(row=1, column=column, sticky="w")

        ttk.Label(right, text="Solution moves", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=(18, 6))
        self.moves_text = tk.Text(right, height=5, wrap=tk.WORD, bd=0, padx=10, pady=8, font=("Consolas", 10))
        self.moves_text.grid(row=3, column=0, sticky="ew")
        self.moves_text.configure(state=tk.DISABLED)

        columns = ("algorithm", "heuristic", "cost", "expanded", "generated", "runtime")
        self.benchmark_table = ttk.Treeview(right, columns=columns, show="headings", height=8)
        for column in columns:
            self.benchmark_table.heading(column, text=column)
            self.benchmark_table.column(column, anchor=tk.CENTER, width=86)
        self.benchmark_table.grid(row=4, column=0, sticky="nsew", pady=(18, 0))

    def _render_state(self):
        solved = self.state == self.goal
        blank = self.state.index(0)
        for index, tile in enumerate(self.state):
            button = self.tile_buttons[index]
            if tile == 0:
                button.configure(text="", bg="#172033", activebackground="#172033", state=tk.DISABLED)
            else:
                adjacent = self._is_adjacent(index, blank)
                bg = "#d1fae5" if solved else ("#e8f1ff" if adjacent else "#ffffff")
                button.configure(
                    text=str(tile),
                    bg=bg,
                    fg="#111827",
                    activebackground="#bfdbfe",
                    state=tk.NORMAL,
                )

        values = heuristic_values(self.state, self.goal)
        for key, value in values.items():
            self.heuristic_vars[key].set(str(value))

    def _move_clicked_tile(self, index: int):
        blank = self.state.index(0)
        if not self._is_adjacent(index, blank):
            return
        next_state = list(self.state)
        next_state[index], next_state[blank] = next_state[blank], next_state[index]
        self.state = tuple(next_state)
        self._clear_solution()
        self._sync_entry()
        self._render_state()
        self.status_var.set("Manual move applied")

    @staticmethod
    def _is_adjacent(left: int, right: int) -> bool:
        left_row, left_col = divmod(left, BOARD_SIZE)
        right_row, right_col = divmod(right, BOARD_SIZE)
        return abs(left_row - right_row) + abs(left_col - right_col) == 1

    def _load_state(self):
        try:
            candidate = validate_state(self.state_entry.get(), "state input")
            if not is_solvable(candidate, self.goal):
                messagebox.showerror("Invalid puzzle", "This state cannot reach the goal state.")
                return
        except ValueError as exc:
            messagebox.showerror("Invalid puzzle", str(exc))
            return
        self.state = candidate
        self._clear_solution()
        self._render_state()
        self.status_var.set("State loaded")

    def _shuffle(self):
        state = self.goal
        last_state = None
        for _ in range(60):
            options = [next_state for _, next_state in successors(state) if next_state != last_state]
            last_state, state = state, random.choice(options)
        self.state = state
        self._clear_solution()
        self._sync_entry()
        self._render_state()
        self.status_var.set("Shuffled solvable state")

    def _reset(self):
        self.state = DEFAULT_START
        self._clear_solution()
        self._sync_entry()
        self._render_state()
        self.status_var.set("Reset to sample puzzle")

    def _solve(self):
        self.status_var.set("Solving...")
        self.root.update_idletasks()

        solver = SearchAlgorithms(self.state, self.goal)
        algorithm = self.algorithm_combo.get()
        heuristic = normalize_heuristic_name(self.heuristic_combo.get())
        path, full_path, cost = run_selected_algorithm(solver, algorithm, heuristic)

        self.solution_actions = path
        self.solution_states = full_path
        self.solution_index = 0
        self._show_stats(solver.last_stats)
        self._show_moves(path)

        if cost < 0:
            self.status_var.set("No solution found")
            messagebox.showerror("No solution", "The selected puzzle is unsolvable.")
            return

        self.status_var.set(f"Solved with {algorithm}: {cost} moves")

    def _step_solution(self):
        if not self.solution_states:
            self._solve()
            if not self.solution_states:
                return

        if self.solution_index < len(self.solution_states) - 1:
            self.solution_index += 1
            self.state = tuple(self.solution_states[self.solution_index])
            self._sync_entry()
            self._render_state()
            self.status_var.set(f"Step {self.solution_index}/{len(self.solution_states) - 1}")
        else:
            self.status_var.set("Goal reached")

    def _animate_solution(self):
        if self.animating:
            return
        if not self.solution_states:
            self._solve()
            if not self.solution_states:
                return
        self.animating = True
        self.solution_index = 0
        self._animate_next()

    def _animate_next(self):
        if self.solution_index >= len(self.solution_states):
            self.animating = False
            self.status_var.set("Animation complete")
            return
        self.state = tuple(self.solution_states[self.solution_index])
        self._sync_entry()
        self._render_state()
        self.status_var.set(f"Animating {self.solution_index}/{len(self.solution_states) - 1}")
        self.solution_index += 1
        self.root.after(420, self._animate_next)

    def _benchmark(self):
        for row in self.benchmark_table.get_children():
            self.benchmark_table.delete(row)

        jobs = [
            ("UCS", "not used"),
            ("A*", "misplaced"),
            ("A*", "manhattan"),
            ("A*", "linear_conflict"),
            ("Greedy", "misplaced"),
            ("Greedy", "manhattan"),
            ("Greedy", "linear_conflict"),
        ]
        for algorithm, heuristic in jobs:
            solver = SearchAlgorithms(self.state, self.goal)
            search_heuristic = "zero" if algorithm == "UCS" else heuristic
            run_selected_algorithm(solver, algorithm, search_heuristic)
            stats = solver.last_stats
            self.benchmark_table.insert(
                "",
                tk.END,
                values=(
                    algorithm,
                    heuristic,
                    stats.get("cost", "-"),
                    stats.get("expanded", "-"),
                    stats.get("generated", "-"),
                    stats.get("runtime_ms", "-"),
                ),
            )
        self.status_var.set("Benchmark complete")

    def _show_stats(self, stats: dict[str, int | float | str | bool]):
        for key, variable in self.stat_vars.items():
            variable.set(str(stats.get(key, "-")))

    def _show_moves(self, moves: Sequence[str]):
        self.moves_text.configure(state=tk.NORMAL)
        self.moves_text.delete("1.0", tk.END)
        self.moves_text.insert(tk.END, " -> ".join(moves) if moves else "Already solved")
        self.moves_text.configure(state=tk.DISABLED)

    def _clear_solution(self):
        self.solution_states = []
        self.solution_actions = []
        self.solution_index = 0
        for variable in self.stat_vars.values():
            variable.set("-")
        if hasattr(self, "moves_text"):
            self._show_moves([])

    def _sync_entry(self):
        self.state_entry.delete(0, tk.END)
        self.state_entry.insert(0, " ".join(str(tile) for tile in self.state))


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
    raise ValueError(f"Unknown algorithm: {algorithm}")


def run_demo(start: State = DEFAULT_START, goal: State = GOAL):
    print("Start state:")
    print(format_state(start))
    print("\nGoal state:")
    print(format_state(goal))
    print()

    for algorithm, heuristic in [("UCS", "zero"), ("A*", "manhattan"), ("Greedy", "manhattan")]:
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
    print("Self-test passed.")


def launch_ui():
    if tk is None:
        raise RuntimeError("Tkinter is not available. Run with --cli to use command-line mode.")
    root = tk.Tk()
    EightPuzzleApp(root)
    root.mainloop()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="8-puzzle solver using UCS, A*, and Greedy search.")
    parser.add_argument("--cli", action="store_true", help="Run the command-line demo instead of the UI.")
    parser.add_argument("--benchmark", action="store_true", help="Run all algorithm and heuristic combinations.")
    parser.add_argument("--self-test", action="store_true", help="Run quick correctness checks.")
    parser.add_argument("--start", default=" ".join(str(tile) for tile in DEFAULT_START), help="Start state, for example: '1 2 3 4 0 6 7 5 8'.")
    parser.add_argument("--goal", default=" ".join(str(tile) for tile in GOAL), help="Goal state, for example: '1 2 3 4 5 6 7 8 0'.")
    parser.add_argument("--algorithm", choices=["UCS", "A*", "Greedy"], help="Run one algorithm in CLI mode.")
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

    if args.cli:
        run_demo(start, goal)
        return

    launch_ui()


if __name__ == "__main__":
    main()
