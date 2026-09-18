# ============================================#
# agents/astar.py — A* pathfinding algorithm
#
# >>A* finds the CHEAPEST fuel-cost path between two grid cells.
# >>Here it is pure logic — no Pygame, no game state, just graph search.
#
# How A* works:
#   - It explores cells outward from the start
#   - For each cell it tracks: cost so far + estimated cost to goal
#   - It always expands the cell with the LOWEST total estimate first
#   - This guarantees the optimal (cheapest) path when it reaches the goal
#
# The "heuristic" is Manhattan distance — a fast estimate of remaining cost.
# Because our actual costs are always >= 1, this heuristic never overestimates,
# which means A* is guaranteed to find the optimal path (it's "admissible").
# ================================================================================#

import heapq
from typing import List, Optional, Tuple, Dict
from core.map import GalaxyMap

## A position in the grid
Pos = Tuple[int, int]   ## (col, row)


def heuristic(a: Pos, b: Pos) -> int:
    """
    Manhattan distance between two grid positions.
    This estimates the minimum number of steps from a to b,
    which is always <= the actual fuel cost (admissible heuristic).
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(galaxy: GalaxyMap, start: Pos, goal: Pos,
          fuel_limit: Optional[int] = None) -> Optional[List[Pos]]:

    if start == goal:
        return [start]

    ## Priority queue entries: (f_score, g_score, position)
    ### f_score = g_score + heuristic  (total estimated cost)
    ### g_score = actual fuel cost from start to this cell
    open_heap: List[Tuple[int, int, Pos]] = []
    heapq.heappush(open_heap, (0 + heuristic(start, goal), 0, start))

    ## Best known fuel cost to reach each cell
    g_score: Dict[Pos, int] = {start: 0}

    ## Where we came from - used to reconstruct the path at the end
    came_from: Dict[Pos, Pos] = {}

    while open_heap:
        f, g, current = heapq.heappop(open_heap)

        if current == goal:
            return _reconstruct(came_from, start, goal)

        ## Skip if we already found a better path to this cell
        if g > g_score.get(current, float('inf')):
            continue

        ## Expand neighbours
        col, row = current
        for neighbor in galaxy.neighbors(col, row):
            step_cost = galaxy.move_cost(neighbor[0], neighbor[1])
            new_g     = g + step_cost

            if fuel_limit is not None and new_g > fuel_limit:
                continue

            ## Only update if this is a better path to neighbor
            if new_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor]   = new_g
                came_from[neighbor] = current
                f_score = new_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, new_g, neighbor))

    ## No path found within constraints
    return None


def path_cost(path: List[Pos], galaxy: GalaxyMap) -> int:
    """
    Calculate the total fuel cost of a given path.
    Cost = sum of move_cost for every cell ENTERED (excludes start).
    """
    if not path or len(path) < 2:
        return 0
    total = 0
    for pos in path[1:]:
        total += galaxy.move_cost(pos[0], pos[1])
    return total


def _reconstruct(came_from: Dict[Pos, Pos], start: Pos, goal: Pos) -> List[Pos]:
    """
    Walk backwards through came_from to rebuild the full path
    from start to goal, then reverse it.
    """
    path    = [goal]
    current = goal
    while current != start:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path