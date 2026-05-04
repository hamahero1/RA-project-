"""Compatibility launcher for the RA26 8-puzzle project.

Algorithms live in search_algorithms.py.
The graphical interface lives in UI.py.
Running this file still opens the UI for older instructions.
"""

from search_algorithms import *  # re-export required template names


if __name__ == "__main__":
    from UI import main

    main()
