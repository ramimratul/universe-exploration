# =================================#
# agents/player.py — Human player
#
#Currently:>
# Handles keyboard input, movement, fuel management,
# resource collection, and the scanner mechanic.
# ================================================#

import pygame
from config import (
    PLAYER_START_FUEL, FUEL_SCAN_COST, SCAN_RADIUS, START_REVEAL_RADIUS,
)
from core.map import GalaxyMap


class Player:

    def __init__(self, galaxy: GalaxyMap):
        start = galaxy.get_start_pos()
        self.col = start[0]
        self.row = start[1]

        self.fuel = PLAYER_START_FUEL
        self.max_fuel = PLAYER_START_FUEL
        self.score = 0
        self.resources_collected = 0

        self.alive   = True
        self.scanner = None

        # Reveal the starting area immediately
        galaxy.reveal_around(self.col, self.row, START_REVEAL_RADIUS, who='player')


    ## Input handling
    # -----------------

    def handle_input(self, event: pygame.event.Event, galaxy: GalaxyMap,
                     renderer=None) -> bool:
        
        if not self.alive:
            return False

        if event.type != pygame.KEYDOWN:
            return False

        dcol, drow = 0, 0

        if event.key == pygame.K_UP:
            drow = -1
        elif event.key == pygame.K_DOWN:
            drow = 1
        elif event.key == pygame.K_LEFT:
            dcol = -1
        elif event.key == pygame.K_RIGHT:
            dcol = 1
        elif event.key == pygame.K_SPACE:
            self._scan(galaxy, renderer)
            return True
        else:
            return False

        if dcol != 0 or drow != 0:
            self._try_move(dcol, drow, galaxy)
            return True

        return False


    ## Movement
    # ----------

    def _try_move(self, dcol: int, drow: int, galaxy: GalaxyMap) -> None: 
        new_col = self.col + dcol
        new_row = self.row + drow

        if not galaxy.in_bounds(new_col, new_row):
            return

        body = galaxy.get(new_col, new_row)
        fuel_cost = body.move_cost if body else 1

        if self.fuel < fuel_cost:
            return   ## not enough fuel

        self.col = new_col
        self.row = new_row
        self.fuel -= fuel_cost

        ## Mark cell as visited
        galaxy.visited_by_player.add((self.col, self.row))

        galaxy.dim_revealed(who='player')
        galaxy.reveal_around(self.col, self.row, START_REVEAL_RADIUS, who='player')


        points = body.collect_as_player() if body else 0
        if points > 0:
            self.score += points
            self.resources_collected += 1

        ## Check fuel
        if self.fuel <= 0:
            self.fuel  = 0
            self.alive = False

    ## Scanner

    def _scan(self, galaxy: GalaxyMap, renderer=None) -> None:
        """
        Activate the scanner: Reveal larger radius, costs more fuel.
        Also triggers the visual pulse animation in the renderer.
        """
        if self.fuel < FUEL_SCAN_COST:
            return   ## can't afford scan

        self.fuel -= FUEL_SCAN_COST
        galaxy.reveal_around(self.col, self.row, SCAN_RADIUS, who='player')

        if renderer is not None:
            renderer.trigger_scan_pulse(self.col, self.row, SCAN_RADIUS)

        if self.fuel <= 0:
            self.fuel  = 0
            self.alive = False

    ## Utility

    @property
    def pos(self):
        return (self.col, self.row)

    def __repr__(self):
        return f"Player(pos={self.pos}, fuel={self.fuel}, score={self.score})"