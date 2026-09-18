# ===================================#
# agents/ai_base.py — Base AI agent
# ==================================#

from config import AI_START_FUEL, START_REVEAL_RADIUS, AI_REVEAL_RADIUS
from core.map import GalaxyMap


class AIAgent:

    def __init__(self, galaxy: GalaxyMap):
        start = galaxy.get_start_pos()
        self.col = start[0]
        self.row = start[1]

        self.fuel = AI_START_FUEL
        self.max_fuel = AI_START_FUEL
        self.score = 0
        self.resources_collected = 0
        self.alive = True

        self.move_interval = 30
        self._tick_counter = 0

        galaxy.reveal_around(self.col, self.row, AI_REVEAL_RADIUS, who='ai')



    def step(self, galaxy: GalaxyMap) -> bool:
        
        if not self.alive:
            return False

        self._tick_counter += 1
        if self._tick_counter < self.move_interval:
            return False

        self._tick_counter = 0
        action = self.choose_action(galaxy)

        if action is None:
            return False

        dcol, drow = action
        self._move(dcol, drow, galaxy)
        return True

    def choose_action(self, galaxy: GalaxyMap):
        """
        Return (dcol, drow) to move, or None to wait.
        Override in subclasses (AStarAgent, MCTSAgent, etc....)

        Default: do nothing (placeholder until subclass is implemented).
        """
        return None


    ## Movement (same as player)

    def _move(self, dcol: int, drow: int, galaxy: GalaxyMap) -> bool:
        new_col = self.col + dcol
        new_row = self.row + drow

        if not galaxy.in_bounds(new_col, new_row):
            return False

        body      = galaxy.get(new_col, new_row)
        fuel_cost = body.move_cost if body else 1

        if self.fuel < fuel_cost:
            self.alive = False
            return False

        self.col = new_col
        self.row = new_row
        self.fuel -= fuel_cost

        galaxy.visited_by_ai.add((self.col, self.row))
        galaxy.dim_revealed(who='ai')
        galaxy.reveal_around(self.col, self.row, AI_REVEAL_RADIUS, who='ai')
        galaxy.dim_revealed(who='player')
        galaxy.reveal_around(self.col, self.row, AI_REVEAL_RADIUS, who='player')

        points = body.collect_as_ai() if body else 0
        if points > 0:
            self.score += points
            self.resources_collected += 1

        if self.fuel <= 0:
            self.fuel = 0
            self.alive = False

        return True


    ## Utility

    @property
    def pos(self):
        return (self.col, self.row)

    def __repr__(self):
        return f"{self.__class__.__name__}(pos={self.pos}, fuel={self.fuel}, score={self.score})"