# RA26 8-Puzzle Solver

This project solves the 8-puzzle problem with Uniform Cost Search, A*, and Greedy Best-First Search. It also includes a Tkinter UI for moving tiles, solving a puzzle, stepping through the solution, animating the solution, and benchmarking the algorithms.

## Files

- `SearchAlgorithms2 - Template .py` - the complete solver, heuristics, command-line mode, tests, benchmark, and UI.
- `RA26 project.docx` - the original project description.
- `.gitignore` - ignores Python cache files, virtual environments, and local editor files.

## Requirements

No external packages are required. The project uses only the Python standard library.

- Python 3.10 or newer is recommended.
- Tkinter is needed for the desktop UI. It is included with most Windows Python installations.

## Run the UI

```powershell
python "SearchAlgorithms2 - Template .py"
```

The UI opens with the sample puzzle:

```text
1 2 3
4 0 6
7 5 8
```

## Command-Line Usage

Run the built-in demo:

```powershell
python "SearchAlgorithms2 - Template .py" --cli
```

Run a benchmark:

```powershell
python "SearchAlgorithms2 - Template .py" --benchmark
```

Run quick correctness checks:

```powershell
python "SearchAlgorithms2 - Template .py" --self-test
```

Run one algorithm:

```powershell
python "SearchAlgorithms2 - Template .py" --algorithm "A*" --heuristic manhattan --start "1 2 3 4 0 6 7 5 8"
```

## UI Flow

1. Enter a puzzle state in the input box or press `Shuffle`.
2. Choose an algorithm: `UCS`, `A*`, or `Greedy`.
3. Choose a heuristic for A* or Greedy: `misplaced`, `manhattan`, or `linear_conflict`.
4. Press `Solve`.
5. Use `Step` to move one state at a time, or `Animate` to play the full solution.
6. Press `Benchmark` to compare UCS, A*, and Greedy across the available heuristics.

Tiles next to the blank are highlighted. Clicking a highlighted tile moves it into the blank position. The live heuristic values update after every manual move.

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

## Algorithms

### UCS

Uniform Cost Search uses:

```text
f(n) = g(n)
```

Because every move costs `1`, UCS finds the shortest solution but may expand many states.

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

Adds Manhattan distance plus `2` for each pair of tiles that are in the same goal row or column but reversed relative to their goal order.

The expected dominance order is:

```text
linear_conflict >= manhattan >= misplaced
```

## Main Code Parts

- `Node` stores one search-tree state, its parent, the action that produced it, `g(n)`, and `h(n)`.
- `SearchAlgorithms` exposes the required `UCS`, `Astar`, and `Greedy` methods.
- `successors` generates all valid next states by swapping the blank with an adjacent tile.
- `misplaced`, `manhattan`, and `linear_conflict` calculate heuristic values.
- `EightPuzzleApp` builds the UI and connects button actions to the solver.
- `run_demo`, `run_benchmark`, and `run_self_test` provide command-line workflows.

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
