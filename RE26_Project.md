# RE26 / RA26 8-Puzzle Solver Project

## Project Title

8-Puzzle Solver using Uniform Cost Search, A* Search, and Greedy Best-First Search.

## Project Overview

This project solves the 8-puzzle problem. The puzzle is a 3x3 board containing tiles from `1` to `8` and one blank tile represented by `0`.

The program starts from an initial puzzle state and searches for a sequence of moves that reaches the goal state:

```text
1 2 3
4 5 6
7 8 0
```

The project includes:

- Uniform Cost Search.
- A* Search.
- Greedy Best-First Search.
- Bonus Breadth-First Search.
- Bonus Depth-First Search.
- Three heuristic functions.
- Required `fullPath` output.
- Bonus `path` output.
- Browser user interface.
- Benchmark comparison table.
- Solvability validation.

## Project Files

The project is split into two Python files:

```text
SearchAlgorithms2 - Template .py
UI.py
```

The old `search_algorithms.py` file was removed. `SearchAlgorithms2 - Template .py` is now the search algorithm file and contains the required `SearchAlgorithms` class and the three required methods:

```python
UCS()
Astar()
Greedy()
```

Each method returns exactly three values:

```python
path, fullPath, totalCost
```

## Five Project Parts Without UI

The project can be explained in five solver-only parts:

1. State handling: the puzzle is represented as a flat list of 9 numbers, and the code validates that every value from `0` to `8` is used once.
2. Solvability and moves: `SearchAlgorithms` checks inversion parity and creates valid next states by moving the blank tile up, down, left, or right.
3. Heuristics: `SearchAlgorithms` provides Misplaced Tiles, Manhattan Distance, and Linear Conflict.
4. Search algorithms: `SearchAlgorithms` includes UCS, A*, Greedy, BFS, and DFS, and each method contains its own full search loop.
5. Output and testing: each algorithm returns `path`, `fullPath`, and `totalCost`; `SearchAlgorithms` also includes self-test and benchmark commands.

## Five Person Work Split

| Person | Part | What they explain |
|---|---|---|
| Person 1 | State handling | Board format, input rules, and the blank tile `0`. |
| Person 2 | Solvability and moves | Inversion parity and legal blank-tile movement inside `SearchAlgorithms`. |
| Person 3 | Heuristics | Misplaced Tiles, Manhattan Distance, and Linear Conflict inside `SearchAlgorithms`. |
| Person 4 | Search algorithms | UCS, A*, Greedy, BFS, and DFS inside `SearchAlgorithms`. |
| Person 5 | Results and testing | `path`, `fullPath`, `totalCost`, self-test, and benchmark. |

## State Representation

The puzzle state is represented as a flat list of 9 numbers.

Example:

```python
[1, 2, 3, 4, 0, 6, 7, 5, 8]
```

This represents:

```text
1 2 3
4 0 6
7 5 8
```

The blank tile is represented by:

```python
0
```

## Input Rules

The input must contain the numbers from `0` to `8` exactly once.

Accepted formats:

```text
1 2 3 4 0 6 7 5 8
```

```text
123406758
```

```text
1,2,3,4,0,6,7,5,8
```

## Solvability Check

Before solving, the program checks if the puzzle can reach the goal state.

For a 3x3 puzzle, the puzzle is solvable only if the inversion count has the same parity as the goal state.

Example unsolvable input:

```text
1 2 3 4 0 6 7 8 5
```

This cannot reach the goal state, so the UI shows:

```text
This puzzle cannot reach the goal state.
```

## Algorithms

### Uniform Cost Search

Uniform Cost Search uses only the path cost:

```text
f(n) = g(n)
```

Since every move has cost `1`, UCS finds an optimal solution. UCS does not use heuristics.

In the UI, when UCS is selected, the heuristic dropdown is disabled and shows:

```text
Not used
```

### A* Search

A* Search uses:

```text
f(n) = g(n) + h(n)
```

It uses both the path cost and a heuristic estimate. With an admissible heuristic, A* finds an optimal solution.

### Greedy Best-First Search

Greedy Search uses:

```text
f(n) = h(n)
```

It chooses the state that looks closest to the goal according to the heuristic. It can be fast, but it does not always guarantee the shortest path.

## Heuristics

The project implements all required and bonus heuristics.

### h1: Misplaced Tiles

Counts how many tiles are not in their correct goal position, ignoring the blank tile.

### h2: Manhattan Distance

Calculates the total distance of every tile from its goal position.

For each tile:

```text
distance = row difference + column difference
```

### h3: Linear Conflict

Uses Manhattan Distance plus an extra cost for tiles that are in the same row or column but block each other from reaching their goal position.

Expected strength:

```text
Linear Conflict >= Manhattan Distance >= Misplaced Tiles
```

## Return Values

Each search function returns:

```python
path, fullPath, totalCost
```

### path

`path` is the actual movement list.

Example:

```python
["DOWN", "RIGHT"]
```

This is a bonus part in the assignment, and it is implemented.

### fullPath

`fullPath` is the list of all board states from the start state to the goal state.

Example:

```python
[
    [1, 2, 3, 4, 0, 6, 7, 5, 8],
    [1, 2, 3, 4, 5, 6, 7, 0, 8],
    [1, 2, 3, 4, 5, 6, 7, 8, 0]
]
```

This is required in the assignment, and it is implemented.

### totalCost

`totalCost` is the number of moves needed to reach the goal.

Example:

```python
2
```

If no solution exists, the cost is:

```python
-1
```

## Difference Between path and fullPath

| Output | Meaning | Example |
|---|---|---|
| `path` | The movement directions | `["DOWN", "RIGHT"]` |
| `fullPath` | The board after every move | Start board, next board, goal board |

In the UI:

- The `Step` button follows the `path`.
- The board display shows the `fullPath` visually.

## User Interface

The project includes a browser UI inside the same Python file.

Run:

```powershell
python UI.py
```

The program opens a local browser UI at:

```text
http://127.0.0.1:8000
```

## UI Features

- Enter a puzzle state.
- Load the puzzle.
- Shuffle a solvable puzzle.
- Reset to the last loaded or shuffled puzzle.
- Select UCS, A*, Greedy, BFS, or DFS.
- Select a heuristic for A* and Greedy.
- Disable heuristic selection automatically for UCS.
- Solve the puzzle.
- Step through the solution one move at a time.
- Animate the solution.
- Benchmark algorithms.
- Clear old results after shuffle or reset.

## Benchmark Table

The UI benchmark table contains:

| Column | Meaning |
|---|---|
| Algorithm | UCS, A*, or Greedy |
| Cost | Solution cost |
| Experience | Number of expanded states |
| Settings | Heuristic used |

## Example Solution

Start:

```text
1 2 3
4 0 6
7 5 8
```

Goal:

```text
1 2 3
4 5 6
7 8 0
```

Actual path:

```python
["DOWN", "RIGHT"]
```

Full path:

```python
[
    [1, 2, 3, 4, 0, 6, 7, 5, 8],
    [1, 2, 3, 4, 5, 6, 7, 0, 8],
    [1, 2, 3, 4, 5, 6, 7, 8, 0]
]
```

Total cost:

```python
2
```

## How to Run in Visual Studio

1. Open Visual Studio.
2. Clone the GitHub repository.
3. Open the project folder.
4. Select the Python file:

```text
UI.py
SearchAlgorithms2 - Template .py
```

5. Set it as the startup file.
6. Run without debugging.

## Command-Line Tests

Run the self-test:

```powershell
python "SearchAlgorithms2 - Template .py" --self-test
```

Run benchmark:

```powershell
python "SearchAlgorithms2 - Template .py" --benchmark
```

Run one algorithm:

```powershell
python "SearchAlgorithms2 - Template .py" --algorithm "A*" --heuristic manhattan --start "123406758"
```

## Bonus Checklist

| Item | Status |
|---|---|
| Actual path `path` | Implemented |
| All three heuristics | Implemented |
| BFS | Implemented |
| DFS | Implemented |
| Browser UI | Implemented |
| Benchmark table | Implemented |
| Step-by-step solution playback | Implemented |

## Final Requirement Checklist

| Requirement | Status |
|---|---|
| UI in its own file | Done |
| Search algorithms in their own file | Done |
| UCS implemented | Done |
| A* implemented | Done |
| Greedy implemented | Done |
| `fullPath` returned | Done |
| `path` returned | Done |
| `totalCost` returned | Done |
| Solvability check | Done |
| README/project documentation | Done |
| GitHub upload | Done |
