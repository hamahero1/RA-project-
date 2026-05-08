# RA26 8-Puzzle Solver

This project solves the 8-puzzle problem with Uniform Cost Search, A*, Greedy Best-First Search, and the bonus BFS/DFS algorithms. It includes a browser UI for moving tiles, solving a puzzle, stepping through the solution, animating the solution, and benchmarking the algorithms.

## Files

- `SearchAlgorithms2 - Template .py` - the required solver file with `Node`, `SearchAlgorithms`, UCS, A*, Greedy, bonus BFS/DFS, and the assignment `main()` function.
- `UI.py` - the browser UI and optional Tkinter UI.
- `RA26 project.docx` - the original project description.
- `.gitignore` - ignores Python cache files, virtual environments, and local editor files.

## Requirements

No external packages are required. The project uses only the Python standard library.

- Python 3.10 or newer is recommended.
- The default UI runs in the browser from a local Python server, so no UI package installation is needed.
- Tkinter is optional and only needed if you run the older desktop UI with `--tk`.
- If the `python` command opens Microsoft Store or fails on Windows, add Python to `PATH` or run the full path to `python.exe`.

## Run the UI

```powershell
python UI.py
```

The UI opens with the sample puzzle:

```text
1 2 3
4 0 6
7 5 8
```

You can type the state with spaces, commas, or as one compact 9-digit value. These are the same state:

```text
1 2 3 4 0 6 7 5 8
123406758
```

The terminal prints a local URL such as:

```text
http://127.0.0.1:8000
```

Open that URL in a browser if it does not open automatically.

## Command-Line Usage

Run the required assignment file:

```powershell
python "SearchAlgorithms2 - Template .py"
```

Run the optional Tkinter UI:

```powershell
python UI.py --tk
```

## UI Flow

1. Enter a puzzle state in the input box or press `Shuffle`.
2. Choose an algorithm: `UCS`, `A*`, `Greedy`, `BFS`, or `DFS`.
3. Choose a heuristic for A* or Greedy: `Misplaced Tiles`, `Manhattan Distance`, or `Linear Conflict`.
4. Press `Solve`.
5. Use `Step` to move one state at a time, or `Animate` to play the full solution.
6. Press `Benchmark` to compare UCS, A*, and Greedy across the available heuristics.

When `UCS` is selected, the heuristic menu is disabled and shows `Not used`, because UCS uses only path cost. The benchmark table shows `Algorithm`, `Cost`, `Expanded`, and `Settings`. `Reset` returns to the last loaded or shuffled puzzle, not always the built-in sample. `Shuffle` and `Reset` clear old solution and benchmark results. The `Step` button shows the next move before applying it, then records the completed move so the board and movement text stay synced. Tiles next to the blank are highlighted. Clicking a highlighted tile moves it into the blank position.

## State Representation

The puzzle is represented as a flat list or tuple of 9 integers:

```python
[1, 2, 3, 4, 0, 6, 7, 5, 8]
```

The number `0` is the blank tile. The goal state is:

```python
[1, 2, 3, 4, 5, 6, 7, 8, 0]
```

## Solver Flow

1. Validate the start and goal states.
2. Check solvability using inversion parity.
3. Create the start `Node`.
4. Push the node into a priority queue.
5. Repeatedly pop the best-priority node.
6. Stop when the goal state is reached.
7. Generate valid successors by moving the blank up, down, left, or right.
8. Track the best known `g(n)` cost for each state to avoid weaker duplicate paths.
9. Reconstruct the final path by following parent nodes from the goal back to the start.

Every search method returns three values:

```python
path, fullPath, totalCost
```

- `path` is the action list, such as `["DOWN", "RIGHT"]`.
- `fullPath` is the list of board states from start to goal.
- `totalCost` is the number of moves, or `-1` if no solution exists.

## Five Project Parts Without UI

1. State handling: stores the 8-puzzle as a flat 9-number list and validates that the numbers `0` to `8` appear exactly once.
2. Solvability and movement: checks inversion parity and generates legal moves inside each algorithm method.
3. Heuristics: calculates Misplaced Tiles, Manhattan Distance, and Linear Conflict for informed search.
4. Search algorithms: runs UCS, A*, Greedy, BFS, and DFS through the `SearchAlgorithms` class.
5. Results and checks: each algorithm returns `path`, `fullPath`, and `totalCost`.

## Five Person Work Split

| Person | Project part | Main responsibility |
|---|---|---|
| Person 1 | BFS | Explain and test `BFS()`, including the queue, discovered states, full path, and total cost. |
| Person 2 | DFS | Explain and test `DFS()`, including the stack, visited states, full path, and why DFS is not always shortest. |
| Person 3 | Greedy | Explain and test `Greedy()`, including how it uses `h(n)` only and why it is not guaranteed optimal. |
| Person 4 | A* | Explain and test `Astar()`, including `g(n) + h(n)` and the available heuristics. |
| Person 5 | UCS | Explain and test `UCS()`, including path cost `g(n)` and why it gives the shortest solution when every move costs `1`. |

## Algorithms

### UCS

Uniform Cost Search uses:

```text
f(n) = g(n)
```

Because every move costs `1`, UCS finds the shortest solution but may expand many states. UCS does not use Misplaced Tiles, Manhattan Distance, or Linear Conflict. In benchmark results, its heuristic is shown as `not used`.

### A*

A* uses:

```text
f(n) = g(n) + h(n)
```

With an admissible heuristic, A* returns an optimal solution while usually expanding fewer states than UCS.

### Greedy

Greedy Best-First Search uses:

```text
f(n) = h(n)
```

It often reaches a goal quickly but does not guarantee the shortest solution.

## Heuristics

### h1: Misplaced Tiles

Counts tiles that are not in their goal position, ignoring the blank.

### h2: Manhattan Distance

Adds the row and column distance between each tile and its goal position.

### h3: Linear Conflict

Adds Manhattan distance plus `2` for each tile that must temporarily leave its current row or column to resolve reversed goal-order conflicts.

The expected dominance order is:

```text
linear_conflict >= manhattan >= misplaced
```

## Main Solver Code Parts

- `Node` stores one search-tree state, its parent, the action that produced it, `g(n)`, and `h(n)`.
- `SearchAlgorithms` exposes only `UCS`, `Astar`, `Greedy`, `BFS`, and `DFS` after `__init__`.
- Each algorithm method contains its own validation, solvability check, successor generation, search loop, path reconstruction, and stats.
- The required `main()` function stays outside the class and runs UCS, A*, and Greedy.

## GitHub Setup

This folder can be published with:

```powershell
git init
git add .
git commit -m "Complete 8-puzzle solver project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ra26-8-puzzle-solver.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username, or create the repository with GitHub Desktop/GitHub CLI and push this folder.
