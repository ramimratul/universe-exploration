# ============================================================================= #
# core/map.py — Galaxy map with SPLIT fog(Need to improve the known vs unknown... Currently
# always left side is known and from middle to right unknwon--- this should be random)
#
# For now:--- >>> player and AI each have their OWN fog grid.
#   - player_fog : only revealed by player movement/scan
#   - ai_fog     : only revealed by AI movement
# ============================================================================= #

import random
import math
from typing import List, Tuple, Optional

from config import (
    GRID_COLS, GRID_ROWS,
    FOG_HIDDEN, FOG_PARTIAL, FOG_REVEALED,
    KNOWN_COLS_FRACTION,
    START_REVEAL_RADIUS,
)

from core.celestial import CelestialBody

Pos = Tuple[int, int]


class GalaxyMap:

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

        self.cols = GRID_COLS
        self.rows = GRID_ROWS
        self.known_cols = max(1, int(self.cols * KNOWN_COLS_FRACTION))

        self.grid: List[List[CelestialBody]] = self._generate_grid()

        ### Two independent fog grids
        self.player_fog: List[List[int]] = self._init_fog()
        self.ai_fog:     List[List[int]] = self._init_fog()

        self.visited_by_player: set = set()
        self.visited_by_ai:     set = set()

    
    ## Generation
    #-------------#

    def _generate_grid(self) -> List[List[CelestialBody]]:
        grid = []
        for row in range(self.rows):
            grid_row = []
            for col in range(self.cols):
                body = CelestialBody.generate_at(col, row)
                           
                grid_row.append(body)
            grid.append(grid_row)
        start_col, start_row = self.get_start_pos()
        grid[start_row][start_col] = CelestialBody()
        return grid

    def _init_fog(self) -> List[List[int]]:
        """Known space starts as FOG_PARTIAL, unknown as FOG_HIDDEN."""
        fog = []
        for row in range(self.rows):
            fog_row = []
            for col in range(self.cols):
                fog_row.append(FOG_PARTIAL if col < self.known_cols else FOG_HIDDEN)
            fog.append(fog_row)
        return fog

    
    
    def get(self, col: int, row: int) -> Optional[CelestialBody]:
        if self.in_bounds(col, row):
            return self.grid[row][col]
        return None

    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows


    # Fog access — always specify who (player or ai)
    # -----------------------------------------------

    def get_fog(self, col: int, row: int, who: str = "player") -> int:
        """
        Return fog state for (col, row) for the given agent.
        who = "player" or "ai"
        """
        fog = self.player_fog if who == "player" else self.ai_fog
        if self.in_bounds(col, row):
            return fog[row][col]
        return FOG_HIDDEN

    def set_fog(self, col: int, row: int, state: int, who: str = "player") -> None:
        fog = self.player_fog if who == "player" else self.ai_fog
        if self.in_bounds(col, row):
            fog[row][col] = state

    
    # Fog Reveal>>>> separate per agent
    # ----------------------------------

    def reveal_around(self, col: int, row: int, radius: int, who: str = "player") -> List[Pos]:
        """
        Reveal cells within radius for the given agent only.
        either "player" or "ai"
        """
        fog = self.player_fog if who == "player" else self.ai_fog
        newly_revealed = []
        for dc in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                if math.sqrt(dc * dc + dr * dr) <= radius:
                    nc, nr = col + dc, row + dr
                    if self.in_bounds(nc, nr):
                        if fog[nr][nc] != FOG_REVEALED:
                            newly_revealed.append((nc, nr))
                        fog[nr][nc] = FOG_REVEALED
        return newly_revealed

    def dim_revealed(self, who: str = "player") -> None:
        fog = self.player_fog if who == "player" else self.ai_fog
        for row in range(self.rows):
            for col in range(self.cols):
                if fog[row][col] == FOG_REVEALED:
                    fog[row][col] = FOG_PARTIAL



    def neighbors(self, col: int, row: int) -> List[Pos]:
        candidates = [
            (col + 1, row), (col - 1, row),
            (col, row + 1), (col, row - 1),
        ]
        return [(c, r) for c, r in candidates if self.in_bounds(c, r)]

    def move_cost(self, col: int, row: int) -> int:
        body = self.get(col, row)
        return body.move_cost if body else 999

    # ----------#
    # Utility
    # ----------#

    def get_start_pos(self) -> Pos:
        return (1, self.rows // 2)

    def all_resources(self) -> List[Tuple[Pos, int]]:
        results = []
        for row in range(self.rows):
            for col in range(self.cols):
                body = self.grid[row][col]
                if body.has_resource:
                    results.append(((col, row), body.resource.value))
        return results

    def revealed_resources_for_player(self) -> List[Tuple[Pos, int]]:
        results = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.player_fog[row][col] != FOG_HIDDEN:
                    body = self.grid[row][col]
                    if body.resource.available_for_player():
                        results.append(((col, row), body.resource.value))
        return results

    def revealed_resources_for_ai(self) -> List[Tuple[Pos, int]]:
        results = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.ai_fog[row][col] != FOG_HIDDEN:
                    body = self.grid[row][col]
                    if body.resource.available_for_ai():
                        results.append(((col, row), body.resource.value))
        return results

    def revealed_resources(self) -> List[Tuple[Pos, int]]:
        results = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.player_fog[row][col] != FOG_HIDDEN:
                    body = self.grid[row][col]
                    if body.has_resource:
                        results.append(((col, row), body.resource.value))
        return results

    def count_collected(self) -> int:
        count = 0
        for row in range(self.rows):
            for col in range(self.cols):
                r = self.grid[row][col].resource
                if r.collected_player: count += 1
                if r.collected_ai:     count += 1
        return count

    def reset_ai_reveal_for_player(self) -> None:
        """
        When AI turn ends:
        1. Reset both fog grids to original known-space-only state
        2. Reset collected_ai flags on all resources so player
           sees every resource as fresh and uncollected
        """
        self.player_fog = self._init_fog()
        self.ai_fog     = self._init_fog()
        self.visited_by_ai.clear()

        # Reset AI collection flags — player sees all resources fresh
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid[row][col].resource.collected_ai = False

    def __repr__(self) -> str:
        return f"GalaxyMap({self.cols}x{self.rows}, known_cols={self.known_cols})"