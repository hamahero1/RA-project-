from __future__ import annotations

import argparse
import json
import random
import threading
import webbrowser
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    tk = None
    ttk = None
    messagebox = None

from search_algorithms import (
    BOARD_SIZE,
    DEFAULT_START,
    GOAL,
    NOT_USED_LABEL,
    TILE_COUNT,
    UI_HEURISTIC_LABELS,
    SearchAlgorithms,
    heuristic_values,
    is_solvable,
    normalize_heuristic_name,
    run_selected_algorithm,
    successors,
    validate_state,
)

WEB_APP_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>8-Puzzle Solver</title>
  <style>
    :root {
      --page: #e9eef5;
      --panel: #ffffff;
      --ink: #0f172a;
      --muted: #64748b;
      --line: #d8e0eb;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --green: #16a34a;
      --amber: #d97706;
      --tile: #ffffff;
      --tile-hot: #dbeafe;
      --blank: #0f172a;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--page);
      color: var(--ink);
      font-family: "Segoe UI", Arial, sans-serif;
    }

    .app {
      width: min(1180px, calc(100vw - 32px));
      margin: 20px auto;
    }

    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      background: #111827;
      color: #ffffff;
      padding: 20px 22px;
      border-radius: 8px;
    }

    h1 {
      margin: 0;
      font-size: 30px;
      line-height: 1.1;
      letter-spacing: 0;
    }

    .subtitle {
      margin-top: 6px;
      color: #bfdbfe;
      font-size: 14px;
    }

    .status {
      min-width: 140px;
      text-align: center;
      background: var(--primary);
      color: #ffffff;
      padding: 8px 14px;
      border-radius: 6px;
      font-weight: 700;
    }

    .layout {
      display: grid;
      grid-template-columns: minmax(360px, 0.95fr) minmax(460px, 1.15fr);
      gap: 20px;
      margin-top: 20px;
    }

    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
    }

    .panel-title {
      margin: 0 0 14px;
      font-size: 18px;
      font-weight: 800;
    }

    .board-shell {
      display: grid;
      place-items: center;
      background: #dbe4f0;
      padding: 12px;
      border-radius: 8px;
      width: min(100%, 398px);
      margin: 0 auto 18px;
    }

    .board {
      display: grid;
      grid-template-columns: repeat(3, 112px);
      gap: 10px;
    }

    .tile {
      width: 112px;
      aspect-ratio: 1;
      border: 0;
      border-radius: 8px;
      background: var(--tile);
      color: var(--ink);
      font-size: 40px;
      font-weight: 800;
      cursor: default;
      box-shadow: 0 8px 18px rgba(15, 23, 42, 0.11);
    }

    .tile.movable {
      background: var(--tile-hot);
      cursor: pointer;
    }

    .tile.solved {
      background: #bbf7d0;
    }

    .tile.blank {
      background: var(--blank);
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
    }

    .row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }

    .field-row {
      display: grid;
      grid-template-columns: 1fr auto auto auto;
      gap: 10px;
      align-items: end;
      margin-bottom: 18px;
    }

    label {
      display: block;
      margin-bottom: 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }

    input,
    select {
      width: 100%;
      min-height: 40px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #ffffff;
      color: var(--ink);
      padding: 8px 10px;
      font: inherit;
    }

    select:disabled {
      color: #334155;
      background: #eef2f7;
      cursor: not-allowed;
    }

    button {
      min-height: 40px;
      border: 0;
      border-radius: 6px;
      padding: 9px 14px;
      color: var(--ink);
      background: #e2e8f0;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }

    button:hover {
      filter: brightness(0.98);
    }

    .primary {
      color: #ffffff;
      background: var(--primary);
    }

    .primary:hover {
      background: var(--primary-dark);
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
    }

    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #f8fafc;
    }

    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      text-transform: uppercase;
    }

    .metric strong {
      display: block;
      margin-top: 4px;
      color: var(--primary-dark);
      font-size: 26px;
    }

    .controls {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-bottom: 18px;
    }

    .actions {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 18px;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
      margin-bottom: 18px;
    }

    .moves {
      min-height: 82px;
      border-radius: 8px;
      background: #f8fafc;
      border: 1px solid var(--line);
      padding: 12px;
      color: #172033;
      font-family: Consolas, "Courier New", monospace;
      line-height: 1.55;
      overflow: auto;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 18px;
      overflow: hidden;
      border-radius: 8px;
      font-size: 14px;
    }

    th,
    td {
      border-bottom: 1px solid var(--line);
      padding: 10px;
      text-align: center;
    }

    th {
      background: #eff6ff;
      color: #1e3a8a;
      font-weight: 800;
    }

    tr:last-child td {
      border-bottom: 0;
    }

    @media (max-width: 900px) {
      .layout,
      .field-row,
      .controls,
      .actions,
      .stats,
      .metrics {
        grid-template-columns: 1fr;
      }

      .header {
        align-items: flex-start;
        flex-direction: column;
      }

      .board {
        grid-template-columns: repeat(3, minmax(86px, 1fr));
      }

      .tile {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <section class="header">
      <div>
        <h1>8-Puzzle Solver</h1>
        <div class="subtitle">Uniform Cost Search, A*, and Greedy Best-First Search</div>
      </div>
      <div id="status" class="status">Ready</div>
    </section>

    <section class="layout">
      <section class="panel">
        <h2 class="panel-title">Puzzle board</h2>
        <div class="board-shell">
          <div id="board" class="board"></div>
        </div>

        <div class="field-row">
          <div>
            <label for="state-input">State input</label>
            <input id="state-input" type="text">
          </div>
          <button id="load-btn">Load</button>
          <button id="shuffle-btn">Shuffle</button>
          <button id="reset-btn">Reset</button>
        </div>

        <div class="metrics">
          <div class="metric"><span>h1 misplaced</span><strong id="h-misplaced">0</strong></div>
          <div class="metric"><span>h2 manhattan</span><strong id="h-manhattan">0</strong></div>
          <div class="metric"><span>h3 conflict</span><strong id="h-linear">0</strong></div>
        </div>
      </section>

      <section class="panel">
        <h2 class="panel-title">Solver controls</h2>
        <div class="controls">
          <div>
            <label for="algorithm">Algorithm</label>
            <select id="algorithm">
              <option value="UCS">UCS</option>
              <option value="A*" selected>A*</option>
              <option value="Greedy">Greedy</option>
            </select>
          </div>
          <div>
            <label for="heuristic">Heuristic</label>
            <select id="heuristic">
              <option id="not-used-option" value="zero" hidden>Not used</option>
              <option value="misplaced">Misplaced Tiles</option>
              <option value="manhattan" selected>Manhattan Distance</option>
              <option value="linear_conflict">Linear Conflict</option>
            </select>
          </div>
        </div>

        <div class="actions">
          <button id="solve-btn" class="primary">Solve</button>
          <button id="step-btn">Step</button>
          <button id="animate-btn">Animate</button>
          <button id="benchmark-btn">Benchmark</button>
        </div>

        <div class="stats">
          <div class="metric"><span>Cost</span><strong id="stat-cost">-</strong></div>
          <div class="metric"><span>Expanded</span><strong id="stat-expanded">-</strong></div>
          <div class="metric"><span>Generated</span><strong id="stat-generated">-</strong></div>
          <div class="metric"><span>Runtime ms</span><strong id="stat-runtime">-</strong></div>
        </div>

        <h2 class="panel-title">Solution moves</h2>
        <div id="moves" class="moves">Already solved</div>

        <table>
          <thead>
            <tr>
              <th>Algorithm</th>
              <th>Heuristic</th>
              <th>Cost</th>
              <th>Expanded</th>
              <th>Generated</th>
              <th>Runtime</th>
            </tr>
          </thead>
          <tbody id="benchmark-body"></tbody>
        </table>
      </section>
    </section>
  </main>

  <script>
    const goal = [1, 2, 3, 4, 5, 6, 7, 8, 0];
    const defaultStart = [1, 2, 3, 4, 0, 6, 7, 5, 8];
    let state = [...defaultStart];
    let solutionStates = [];
    let solutionActions = [];
    let solutionIndex = 0;
    let animating = false;
    let lastHeuristic = "manhattan";

    const board = document.getElementById("board");
    const stateInput = document.getElementById("state-input");
    const algorithmSelect = document.getElementById("algorithm");
    const heuristicSelect = document.getElementById("heuristic");
    const notUsedOption = document.getElementById("not-used-option");
    const statusEl = document.getElementById("status");
    const movesEl = document.getElementById("moves");
    const benchmarkBody = document.getElementById("benchmark-body");

    function setStatus(text) {
      statusEl.textContent = text;
    }

    function syncStateInput() {
      stateInput.value = state.join(" ");
    }

    function sameState(a, b) {
      return a.length === b.length && a.every((value, index) => value === b[index]);
    }

    function adjacent(a, b) {
      const ar = Math.floor(a / 3);
      const ac = a % 3;
      const br = Math.floor(b / 3);
      const bc = b % 3;
      return Math.abs(ar - br) + Math.abs(ac - bc) === 1;
    }

    function parseState(text) {
      const parts = text.trim().replaceAll(",", " ").replaceAll(";", " ").split(/\s+/).filter(Boolean);
      const values = parts.length === 1 && /^[0-9]{9}$/.test(parts[0])
        ? parts[0].split("").map(Number)
        : parts.map(Number);
      if (values.length !== 9 || values.some((value) => !Number.isInteger(value))) {
        throw new Error("State must contain exactly 9 numbers.");
      }
      const sorted = [...values].sort((a, b) => a - b);
      if (!sorted.every((value, index) => value === index)) {
        throw new Error("State must contain each number from 0 to 8 exactly once.");
      }
      return values;
    }

    function inversionCount(values) {
      const tiles = values.filter((value) => value !== 0);
      let count = 0;
      for (let i = 0; i < tiles.length; i += 1) {
        for (let j = i + 1; j < tiles.length; j += 1) {
          if (tiles[i] > tiles[j]) count += 1;
        }
      }
      return count;
    }

    function isSolvable(values) {
      return inversionCount(values) % 2 === inversionCount(goal) % 2;
    }

    function goalIndex(tile) {
      return goal.indexOf(tile);
    }

    function misplaced(values) {
      return values.reduce((total, tile, index) => total + (tile !== 0 && tile !== goal[index] ? 1 : 0), 0);
    }

    function manhattan(values) {
      return values.reduce((total, tile, index) => {
        if (tile === 0) return total;
        const target = goalIndex(tile);
        return total + Math.abs(Math.floor(index / 3) - Math.floor(target / 3)) + Math.abs((index % 3) - (target % 3));
      }, 0);
    }

    function countInversions(values) {
      let total = 0;
      for (let i = 0; i < values.length; i += 1) {
        for (let j = i + 1; j < values.length; j += 1) {
          if (values[i] > values[j]) total += 1;
        }
      }
      return total;
    }

    function linearConflict(values) {
      let conflicts = 0;
      for (let row = 0; row < 3; row += 1) {
        const goalColumns = [];
        for (let col = 0; col < 3; col += 1) {
          const tile = values[row * 3 + col];
          const target = goalIndex(tile);
          if (tile !== 0 && Math.floor(target / 3) === row) goalColumns.push(target % 3);
        }
        conflicts += countInversions(goalColumns);
      }
      for (let col = 0; col < 3; col += 1) {
        const goalRows = [];
        for (let row = 0; row < 3; row += 1) {
          const tile = values[row * 3 + col];
          const target = goalIndex(tile);
          if (tile !== 0 && target % 3 === col) goalRows.push(Math.floor(target / 3));
        }
        conflicts += countInversions(goalRows);
      }
      return manhattan(values) + (2 * conflicts);
    }

    function renderHeuristics() {
      document.getElementById("h-misplaced").textContent = misplaced(state);
      document.getElementById("h-manhattan").textContent = manhattan(state);
      document.getElementById("h-linear").textContent = linearConflict(state);
    }

    function clearSolution() {
      solutionStates = [];
      solutionActions = [];
      solutionIndex = 0;
      document.getElementById("stat-cost").textContent = "-";
      document.getElementById("stat-expanded").textContent = "-";
      document.getElementById("stat-generated").textContent = "-";
      document.getElementById("stat-runtime").textContent = "-";
      movesEl.textContent = "Already solved";
    }

    function renderBoard() {
      board.innerHTML = "";
      const blank = state.indexOf(0);
      const solved = sameState(state, goal);
      state.forEach((tile, index) => {
        const button = document.createElement("button");
        button.className = "tile";
        if (tile === 0) {
          button.classList.add("blank");
          button.disabled = true;
        } else {
          button.textContent = tile;
          if (solved) button.classList.add("solved");
          if (!solved && adjacent(index, blank)) {
            button.classList.add("movable");
            button.addEventListener("click", () => moveTile(index));
          }
        }
        board.appendChild(button);
      });
      syncStateInput();
      renderHeuristics();
    }

    function moveTile(index) {
      const blank = state.indexOf(0);
      if (!adjacent(index, blank)) return;
      const next = [...state];
      [next[index], next[blank]] = [next[blank], next[index]];
      state = next;
      clearSolution();
      renderBoard();
      setStatus("Manual move");
    }

    function loadState() {
      try {
        const next = parseState(stateInput.value);
        if (!isSolvable(next)) throw new Error("This puzzle cannot reach the goal state.");
        state = next;
        clearSolution();
        renderBoard();
        setStatus("State loaded");
      } catch (error) {
        alert(error.message);
      }
    }

    function successors(values) {
      const blank = values.indexOf(0);
      const row = Math.floor(blank / 3);
      const col = blank % 3;
      const targets = [];
      if (row > 0) targets.push(blank - 3);
      if (row < 2) targets.push(blank + 3);
      if (col > 0) targets.push(blank - 1);
      if (col < 2) targets.push(blank + 1);
      return targets.map((target) => {
        const next = [...values];
        [next[blank], next[target]] = [next[target], next[blank]];
        return next;
      });
    }

    function shufflePuzzle() {
      let current = [...goal];
      let previous = null;
      for (let i = 0; i < 60; i += 1) {
        const options = successors(current).filter((item) => !previous || !sameState(item, previous));
        previous = current;
        current = options[Math.floor(Math.random() * options.length)];
      }
      state = current;
      clearSolution();
      renderBoard();
      setStatus("Shuffled");
    }

    function resetPuzzle() {
      state = [...defaultStart];
      clearSolution();
      renderBoard();
      setStatus("Reset");
    }

    function updateAlgorithmUI() {
      if (algorithmSelect.value === "UCS") {
        if (heuristicSelect.value !== "zero") lastHeuristic = heuristicSelect.value;
        notUsedOption.hidden = false;
        heuristicSelect.value = "zero";
        heuristicSelect.disabled = true;
        return;
      }
      heuristicSelect.disabled = false;
      notUsedOption.hidden = true;
      heuristicSelect.value = lastHeuristic;
    }

    async function apiPost(path, payload) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Request failed.");
      return data;
    }

    async function solvePuzzle() {
      setStatus("Solving");
      const algorithm = algorithmSelect.value;
      const heuristic = algorithm === "UCS" ? "zero" : heuristicSelect.value;
      try {
        const data = await apiPost("/api/solve", { start: state, goal, algorithm, heuristic });
        solutionActions = data.path;
        solutionStates = data.fullPath;
        solutionIndex = 0;
        document.getElementById("stat-cost").textContent = data.totalCost;
        document.getElementById("stat-expanded").textContent = data.stats.expanded;
        document.getElementById("stat-generated").textContent = data.stats.generated;
        document.getElementById("stat-runtime").textContent = data.stats.runtime_ms;
        movesEl.textContent = data.path.length ? data.path.join(" -> ") : "Already solved";
        setStatus(data.totalCost < 0 ? "No solution" : "Solved");
      } catch (error) {
        setStatus("Error");
        alert(error.message);
      }
    }

    function stepSolution() {
      if (!solutionStates.length) {
        solvePuzzle().then(() => stepSolution());
        return;
      }
      if (solutionIndex < solutionStates.length - 1) {
        solutionIndex += 1;
        state = [...solutionStates[solutionIndex]];
        renderBoard();
        setStatus(`Step ${solutionIndex}/${solutionStates.length - 1}`);
      } else {
        setStatus("Goal reached");
      }
    }

    function animateSolution() {
      if (animating) return;
      if (!solutionStates.length) {
        solvePuzzle().then(() => animateSolution());
        return;
      }
      animating = true;
      solutionIndex = 0;
      const tick = () => {
        if (solutionIndex >= solutionStates.length) {
          animating = false;
          setStatus("Animation complete");
          return;
        }
        state = [...solutionStates[solutionIndex]];
        renderBoard();
        setStatus(`Animating ${solutionIndex}/${solutionStates.length - 1}`);
        solutionIndex += 1;
        setTimeout(tick, 420);
      };
      tick();
    }

    async function benchmarkPuzzle() {
      setStatus("Benchmarking");
      try {
        const data = await apiPost("/api/benchmark", { start: state, goal });
        benchmarkBody.innerHTML = "";
        data.results.forEach((row) => {
          const tr = document.createElement("tr");
          tr.innerHTML = `<td>${row.algorithm}</td><td>${row.heuristic}</td><td>${row.cost}</td><td>${row.expanded}</td><td>${row.generated}</td><td>${row.runtime_ms}</td>`;
          benchmarkBody.appendChild(tr);
        });
        setStatus("Benchmark done");
      } catch (error) {
        setStatus("Error");
        alert(error.message);
      }
    }

    algorithmSelect.addEventListener("change", updateAlgorithmUI);
    heuristicSelect.addEventListener("change", () => {
      if (heuristicSelect.value !== "zero") lastHeuristic = heuristicSelect.value;
    });
    document.getElementById("load-btn").addEventListener("click", loadState);
    document.getElementById("shuffle-btn").addEventListener("click", shufflePuzzle);
    document.getElementById("reset-btn").addEventListener("click", resetPuzzle);
    document.getElementById("solve-btn").addEventListener("click", solvePuzzle);
    document.getElementById("step-btn").addEventListener("click", stepSolution);
    document.getElementById("animate-btn").addEventListener("click", animateSolution);
    document.getElementById("benchmark-btn").addEventListener("click", benchmarkPuzzle);

    syncStateInput();
    updateAlgorithmUI();
    renderBoard();
  </script>
</body>
</html>
"""


class PuzzleWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path in {"/", "/index.html"}:
            self._send_html(WEB_APP_HTML)
            return
        self.send_error(404, "Not found")

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/solve":
                self._send_json(self._solve_payload(payload))
                return
            if path == "/api/benchmark":
                self._send_json(self._benchmark_payload(payload))
                return
            self.send_error(404, "Not found")
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)
        except Exception as exc:
            self._send_json({"error": f"Unexpected server error: {exc}"}, status=500)

    def log_message(self, format, *args):
        return

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _send_html(self, html: str):
        encoded = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict, status: int = 200):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    @staticmethod
    def _solve_payload(payload: dict) -> dict:
        start = validate_state(payload.get("start", DEFAULT_START), "start")
        goal = validate_state(payload.get("goal", GOAL), "goal")
        algorithm = str(payload.get("algorithm", "A*"))
        heuristic = normalize_heuristic_name(str(payload.get("heuristic", "manhattan")))
        solver = SearchAlgorithms(start, goal)
        path, full_path, cost = run_selected_algorithm(solver, algorithm, heuristic)
        return {
            "path": path,
            "fullPath": full_path,
            "totalCost": cost,
            "stats": solver.last_stats,
        }

    @staticmethod
    def _benchmark_payload(payload: dict) -> dict:
        start = validate_state(payload.get("start", DEFAULT_START), "start")
        goal = validate_state(payload.get("goal", GOAL), "goal")
        jobs = [
            ("UCS", NOT_USED_LABEL, "zero"),
            ("A*", "Misplaced", "misplaced"),
            ("A*", "Manhattan", "manhattan"),
            ("A*", "Linear Conflict", "linear_conflict"),
            ("Greedy", "Misplaced", "misplaced"),
            ("Greedy", "Manhattan", "manhattan"),
            ("Greedy", "Linear Conflict", "linear_conflict"),
        ]
        results = []
        for algorithm, label, heuristic in jobs:
            solver = SearchAlgorithms(start, goal)
            _, _, cost = run_selected_algorithm(solver, algorithm, heuristic)
            stats = solver.last_stats
            results.append(
                {
                    "algorithm": algorithm,
                    "heuristic": label,
                    "cost": cost,
                    "expanded": stats.get("expanded", "-"),
                    "generated": stats.get("generated", "-"),
                    "runtime_ms": stats.get("runtime_ms", "-"),
                }
            )
        return {"results": results}


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
        self.last_heuristic_label = "Manhattan Distance"

        self._configure_window()
        self._build_layout()
        self._render_state()

    def _configure_window(self):
        self.root.title("8-Puzzle Solver")
        self.root.geometry("1120x720")
        self.root.minsize(980, 640)
        self.root.configure(bg="#e9eef5")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#e9eef5")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("TLabel", background="#e9eef5", foreground="#172033", font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background="#ffffff", foreground="#172033", font=("Segoe UI", 10))
        style.configure("PanelTitle.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 12, "bold"))
        style.configure("Header.TLabel", background="#111827", foreground="#ffffff", font=("Segoe UI", 24, "bold"))
        style.configure("Subheader.TLabel", background="#111827", foreground="#bfdbfe", font=("Segoe UI", 10))
        style.configure("Small.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 9))
        style.configure("Metric.TLabel", background="#ffffff", foreground="#1d4ed8", font=("Segoe UI", 18, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 8), borderwidth=0)
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(12, 9), background="#2563eb", foreground="#ffffff")
        style.map("Primary.TButton", background=[("active", "#1d4ed8"), ("pressed", "#1e40af")])
        style.configure("TEntry", padding=(8, 6))
        style.configure("TCombobox", padding=(8, 6))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _build_layout(self):
        shell = ttk.Frame(self.root, padding=20)
        shell.pack(fill=tk.BOTH, expand=True)
        shell.columnconfigure(0, weight=1)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(1, weight=1)

        header = tk.Frame(shell, bg="#111827", padx=20, pady=16, highlightthickness=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text="8-Puzzle Solver", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(header, text="UCS, A*, and Greedy search comparison", style="Subheader.TLabel").grid(row=1, column=0, sticky="w", pady=(3, 0))
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            header,
            textvariable=self.status_var,
            bg="#2563eb",
            fg="#ffffff",
            padx=14,
            pady=6,
            font=("Segoe UI", 10, "bold"),
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        left = tk.Frame(shell, bg="#ffffff", padx=20, pady=20, highlightbackground="#d8e0eb", highlightthickness=1)
        left.grid(row=1, column=0, sticky="nsew", pady=(18, 0), padx=(0, 12))
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Puzzle board", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 12))
        board_frame = tk.Frame(left, bg="#dbe4f0", padx=10, pady=10)
        board_frame.grid(row=1, column=0, pady=(0, 18))
        for index in range(TILE_COUNT):
            button = tk.Button(
                board_frame,
                width=4,
                height=2,
                bd=0,
                relief=tk.FLAT,
                font=("Segoe UI", 28, "bold"),
                highlightthickness=0,
                cursor="hand2",
                command=lambda i=index: self._move_clicked_tile(i),
            )
            button.grid(row=index // BOARD_SIZE, column=index % BOARD_SIZE, padx=7, pady=7, sticky="nsew")
            self.tile_buttons.append(button)

        state_panel = ttk.Frame(left, style="Panel.TFrame")
        state_panel.grid(row=2, column=0, sticky="ew")
        state_panel.columnconfigure(0, weight=1)
        ttk.Label(state_panel, text="State input", style="PanelTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.state_entry = ttk.Entry(state_panel)
        self.state_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 10))
        self.state_entry.insert(0, " ".join(str(tile) for tile in self.state))
        ttk.Button(state_panel, text="Load", command=self._load_state).grid(row=2, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(state_panel, text="Shuffle", command=self._shuffle).grid(row=2, column=1, sticky="ew", padx=6)
        ttk.Button(state_panel, text="Reset", command=self._reset).grid(row=2, column=2, sticky="ew", padx=(6, 0))

        h_panel = ttk.Frame(left, style="Panel.TFrame")
        h_panel.grid(row=3, column=0, sticky="ew", pady=(18, 0))
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
            ttk.Label(box, textvariable=self.heuristic_vars[key], style="Metric.TLabel").pack(anchor="w")

        right = tk.Frame(shell, bg="#ffffff", padx=20, pady=20, highlightbackground="#d8e0eb", highlightthickness=1)
        right.grid(row=1, column=1, sticky="nsew", pady=(18, 0), padx=(12, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(4, weight=1)

        controls = ttk.Frame(right, style="Panel.TFrame")
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure((0, 1), weight=1)

        ttk.Label(controls, text="Solver controls", style="PanelTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Label(controls, text="Algorithm", style="Panel.TLabel").grid(row=1, column=0, sticky="w")
        self.algorithm_combo = ttk.Combobox(controls, state="readonly", values=["UCS", "A*", "Greedy"])
        self.algorithm_combo.current(1)
        self.algorithm_combo.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(4, 10))
        self.algorithm_combo.bind("<<ComboboxSelected>>", self._on_algorithm_changed)

        ttk.Label(controls, text="Heuristic", style="Panel.TLabel").grid(row=1, column=1, sticky="w")
        self.heuristic_combo = ttk.Combobox(
            controls,
            state="readonly",
            values=UI_HEURISTIC_LABELS,
        )
        self.heuristic_combo.set(self.last_heuristic_label)
        self.heuristic_combo.grid(row=2, column=1, sticky="ew", padx=(8, 0), pady=(4, 10))
        self.heuristic_combo.bind("<<ComboboxSelected>>", self._on_heuristic_changed)

        ttk.Button(controls, text="Solve", style="Primary.TButton", command=self._solve).grid(row=3, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(controls, text="Step", command=self._step_solution).grid(row=3, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(controls, text="Animate", command=self._animate_solution).grid(row=4, column=0, sticky="ew", padx=(0, 8), pady=(10, 0))
        ttk.Button(controls, text="Benchmark", command=self._benchmark).grid(row=4, column=1, sticky="ew", padx=(8, 0), pady=(10, 0))
        self._on_algorithm_changed()

        stats = ttk.Frame(right, style="Panel.TFrame")
        stats.grid(row=1, column=0, sticky="ew", pady=(18, 0))
        stats.columnconfigure((0, 1, 2, 3), weight=1)
        for column, key in enumerate(["cost", "expanded", "generated", "runtime_ms"]):
            self.stat_vars[key] = tk.StringVar(value="-")
            ttk.Label(stats, text=key.replace("_", " "), style="Small.TLabel").grid(row=0, column=column, sticky="w")
            ttk.Label(stats, textvariable=self.stat_vars[key], style="Panel.TLabel", font=("Segoe UI", 13, "bold")).grid(row=1, column=column, sticky="w")

        ttk.Label(right, text="Solution moves", style="PanelTitle.TLabel").grid(row=2, column=0, sticky="w", pady=(18, 6))
        self.moves_text = tk.Text(
            right,
            height=5,
            wrap=tk.WORD,
            bd=0,
            bg="#f8fafc",
            fg="#172033",
            padx=12,
            pady=10,
            font=("Consolas", 10),
            insertbackground="#172033",
        )
        self.moves_text.grid(row=3, column=0, sticky="ew")
        self.moves_text.configure(state=tk.DISABLED)

        columns = ("algorithm", "heuristic", "cost", "expanded", "generated", "runtime")
        self.benchmark_table = ttk.Treeview(right, columns=columns, show="headings", height=8)
        for column in columns:
            self.benchmark_table.heading(column, text=column)
            width = 120 if column == "heuristic" else 86
            self.benchmark_table.column(column, anchor=tk.CENTER, width=width)
        self.benchmark_table.grid(row=4, column=0, sticky="nsew", pady=(18, 0))

    def _on_algorithm_changed(self, _event=None):
        algorithm = self.algorithm_combo.get()
        current = self.heuristic_combo.get()
        if current in UI_HEURISTIC_LABELS:
            self.last_heuristic_label = current

        if algorithm == "UCS":
            self.heuristic_combo.configure(values=[NOT_USED_LABEL], state="disabled")
            self.heuristic_combo.set(NOT_USED_LABEL)
            return

        self.heuristic_combo.configure(values=UI_HEURISTIC_LABELS, state="readonly")
        if self.last_heuristic_label not in UI_HEURISTIC_LABELS:
            self.last_heuristic_label = "Manhattan Distance"
        self.heuristic_combo.set(self.last_heuristic_label)

    def _on_heuristic_changed(self, _event=None):
        current = self.heuristic_combo.get()
        if current in UI_HEURISTIC_LABELS:
            self.last_heuristic_label = current

    def _render_state(self):
        solved = self.state == self.goal
        blank = self.state.index(0)
        for index, tile in enumerate(self.state):
            button = self.tile_buttons[index]
            if tile == 0:
                button.configure(
                    text="",
                    bg="#0f172a",
                    activebackground="#0f172a",
                    state=tk.DISABLED,
                    cursor="arrow",
                    disabledforeground="#0f172a",
                )
            else:
                adjacent = self._is_adjacent(index, blank)
                bg = "#bbf7d0" if solved else ("#dbeafe" if adjacent else "#ffffff")
                button.configure(
                    text=str(tile),
                    bg=bg,
                    fg="#0f172a",
                    activebackground="#bfdbfe" if adjacent else "#f8fafc",
                    state=tk.NORMAL,
                    cursor="hand2" if adjacent else "arrow",
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
        heuristic = "zero" if algorithm == "UCS" else normalize_heuristic_name(self.heuristic_combo.get())
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
            ("UCS", NOT_USED_LABEL, "zero"),
            ("A*", "Misplaced", "misplaced"),
            ("A*", "Manhattan", "manhattan"),
            ("A*", "Linear Conflict", "linear_conflict"),
            ("Greedy", "Misplaced", "misplaced"),
            ("Greedy", "Manhattan", "manhattan"),
            ("Greedy", "Linear Conflict", "linear_conflict"),
        ]
        for algorithm, heuristic, search_heuristic in jobs:
            solver = SearchAlgorithms(self.state, self.goal)
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


def launch_ui():
    if tk is None:
        raise RuntimeError("Tkinter is not available. Run with --cli to use command-line mode.")
    root = tk.Tk()
    EightPuzzleApp(root)
    root.mainloop()


def launch_web_ui(port: int = 8000, open_browser: bool = True):
    try:
        server = HTTPServer(("127.0.0.1", port), PuzzleWebHandler)
    except OSError:
        if port == 0:
            raise
        server = HTTPServer(("127.0.0.1", 0), PuzzleWebHandler)
    host, actual_port = server.server_address
    url = f"http://{host}:{actual_port}"

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    print(f"8-Puzzle Solver UI running at {url}")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Browser UI for the 8-puzzle solver.")
    parser.add_argument("--tk", action="store_true", help="Run the older Tkinter desktop UI.")
    parser.add_argument("--port", type=int, default=8000, help="Port for the browser UI.")
    parser.add_argument("--no-browser", action="store_true", help="Start the browser UI without opening a browser tab.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.tk:
        launch_ui()
        return

    launch_web_ui(args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
