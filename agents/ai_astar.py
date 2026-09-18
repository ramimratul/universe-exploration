# ==========================================#
# agents/ai_astar.py — A* powered AI agent

#
# >>>> Fuel-aware targeting
#     When fuel < LOW_FUEL_THRESHOLD only consider nearby resources.
#     Prevents overcommitting on a far target and getting stranded.
#
#>>>> AI needs to be more smarter..............
# ===============================================#

from typing import Optional, List, Tuple
from config import AI_START_FUEL, START_REVEAL_RADIUS, FOG_HIDDEN
from core.map import GalaxyMap
from agents.ai_base import AIAgent
from agents.astar import astar, path_cost

Pos = Tuple[int, int]

LOW_FUEL_THRESHOLD = 35

## How much better a new target must be to interrupt current path (60% better)
REPLAN_THRESHOLD = 1.6


class AStarAgent(AIAgent):

    def __init__(self, galaxy: GalaxyMap):
        super().__init__(galaxy)

        self.path:          List[Pos]     = []
        self.target:        Optional[Pos] = None
        self._target_ratio: float         = -1.0  # ratio of current target

        self.move_interval = 35 # ai movement speed
        self.decision_text: str = "Initialising..."

    ## Core decision loop
    # ----------------------

    def choose_action(self, galaxy: GalaxyMap) -> Optional[Tuple[int, int]]:

        if self.path and self.target is not None:
            body = galaxy.get(self.target[0], self.target[1])

            if body and body.resource.available_for_ai():
                better = self._find_dramatically_better(galaxy)
                if better is None:
                    tval = body.resource.value
                    self.decision_text = (
                        f"A* NAVIGATING → ({self.target[0]},{self.target[1]}) "
                        f"| +{tval} | steps left: {len(self.path)}"
                    )
                    return self._follow_path()
                else:
                    self.path   = []
                    self.target = None
                    self._target_ratio = -1.0

            else:
                ## Target gone —>> replan
                self.path   = []
                self.target = None
                self._target_ratio = -1.0

        target, ratio = self._pick_best_target(galaxy)

        if target is not None:
            path = astar(galaxy, self.pos, target, fuel_limit=self.fuel)
            if path and len(path) > 1:
                self.target = target
                self.path = path[1:]
                self._target_ratio = ratio
                body = galaxy.get(target[0], target[1])
                tval = body.resource.value if body and body.has_resource else 0
                cost = path_cost(path, galaxy)
                self.decision_text = (
                    f"A* PLANNED → ({target[0]},{target[1]}) "
                    f"| +{tval} | cost: {cost} fuel | ratio: {ratio:.1f}"
                )
                return self._follow_path()

        self.decision_text = "EXPLORING → advancing into unknown space"
        return self._explore(galaxy)


    def _find_dramatically_better(self, galaxy: GalaxyMap) -> Optional[Pos]:
        """
        Scan visible resources. If any scores REPLAN_THRESHOLD times
        better than current target ratio, return it. Otherwise None.
        """
        if self._target_ratio <= 0:
            return None

        candidates = galaxy.revealed_resources_for_ai()
        best_pre   = -1.0
        best_pos   = None

        for (pos, value) in candidates:
            if pos == self.target:
                continue
            manhattan = abs(pos[0] - self.col) + abs(pos[1] - self.row)
            if manhattan > self.fuel:
                continue
            pre = (value ** 1.5) / max(1, manhattan)
            if pre > best_pre:
                best_pre = pre
                best_pos = pos

        if best_pos is None:
            return None

        if best_pre < self._target_ratio * REPLAN_THRESHOLD:
            return None

        path = astar(galaxy, self.pos, best_pos, fuel_limit=self.fuel)
        if path is None:
            return None
        cost = path_cost(path, galaxy)
        if cost <= 0 or cost > self.fuel:
            return None

        body  = galaxy.get(best_pos[0], best_pos[1])
        value = body.resource.value if body and body.has_resource else 0
        real_ratio = (value ** 1.5) / cost

        if real_ratio >= self._target_ratio * REPLAN_THRESHOLD:
            return best_pos
        return None


    def _pick_best_target(self, galaxy: GalaxyMap) -> Tuple[Optional[Pos], float]:
        """
        Score every visible uncollected resource by value^1.5 / fuel_cost.

        value^1.5 strongly favours high-value resources even at
               medium distance — AI chases quality over proximity.

        When fuel is low, cap the max manhattan distance so the
               AI only considers nearby reachable targets and doesn't
               overcommit on something far away.
        """
        candidates = galaxy.revealed_resources_for_ai()
        if not candidates:
            return None, -1.0

        low_fuel    = self.fuel < LOW_FUEL_THRESHOLD
        max_allowed = max(3, self.fuel // 2) if low_fuel else self.fuel

        best_pos   = None
        best_ratio = -1.0

        for (pos, value) in candidates:
            manhattan = abs(pos[0] - self.col) + abs(pos[1] - self.row)

            if manhattan > max_allowed:
                continue

            ## Run A* for exact fuel cost
            path = astar(galaxy, self.pos, pos, fuel_limit=self.fuel)
            if path is None:
                continue
            cost = path_cost(path, galaxy)
            if cost <= 0 or cost > self.fuel:
                continue

            ######
            ratio = (value ** 1.5) / cost

            if ratio > best_ratio:
                best_ratio = ratio
                best_pos   = pos

        return best_pos, best_ratio

    def _explore(self, galaxy: GalaxyMap) -> Optional[Tuple[int, int]]:
        ## Before exploring unknown, do one final sweep for any missed
        # resources in already-visited cells — catches anything the AI
        # passed early that it didn't collect yet
        fallback = self._sweep_any_resource(galaxy)
        if fallback is not None:
            path = astar(galaxy, self.pos, fallback, fuel_limit=self.fuel)
            if path and len(path) > 1:
                body = galaxy.get(fallback[0], fallback[1])
                tval = body.resource.value if body and body.has_resource else 0
                self.target = fallback
                self.path = path[1:]
                self._target_ratio = (tval ** 1.5) / max(1, path_cost(path, galaxy))
                self.decision_text = (
                    f"A* BACKFILL → ({fallback[0]},{fallback[1]}) "
                    f"| +{tval} | missed resource"
                )
                return self._follow_path()

        target = self._best_hidden_target(galaxy)

        if target:
            path = astar(galaxy, self.pos, target, fuel_limit=self.fuel)
            if path and len(path) > 1:
                self.path   = path[1:]
                self.target = target
                self.decision_text = (
                    f"EXPLORING → heading to ({target[0]},{target[1]}) "
                    f"| {len(path)-1} steps ahead"
                )
                return self._follow_path()

        for dcol, drow in [(1, 0), (0, 1), (0, -1), (-1, 0)]:
            nc, nr = self.col + dcol, self.row + drow
            if galaxy.in_bounds(nc, nr) and galaxy.get_fog(nc, nr, who='ai') == FOG_HIDDEN:
                return (dcol, drow)

        ## Last resort — move in any valid direction to drain remaining fuel
        for dcol, drow in [(1, 0), (0, 1), (0, -1), (-1, 0)]:
            nc, nr = self.col + dcol, self.row + drow
            if galaxy.in_bounds(nc, nr) and self.fuel >= galaxy.move_cost(nc, nr):
                return (dcol, drow)

        return None

    def _sweep_any_resource(self, galaxy: GalaxyMap) -> Optional[Pos]:
        """
        Final fallback before exploring — find ANY uncollected resource
        in visited space that A* can still reach within current fuel.
        Sorted by value^1.5/manhattan so highest value choosen.
        """
        candidates = []
        for (pos, value) in galaxy.revealed_resources_for_ai():
            manhattan = abs(pos[0] - self.col) + abs(pos[1] - self.row)
            if manhattan > self.fuel:
                continue
            candidates.append(((value ** 1.5) / max(1, manhattan), pos, value))

        candidates.sort(reverse=True)

        for (_, pos, value) in candidates[:8]:
            path = astar(galaxy, self.pos, pos, fuel_limit=self.fuel)
            if path and len(path) > 1:
                cost = path_cost(path, galaxy)
                if 0 < cost <= self.fuel:
                    return pos
        return None

    def _best_hidden_target(self, galaxy: GalaxyMap) -> Optional[Pos]:
        """
        Score hidden cells by a weighted combination of:
          - Distance (closer = better base)
        This pushes the AI forward into unknown territory rather than
        zigzagging up/down for marginally closer cells.
        """
        best_pos   = None
        best_score = float('-inf')

        for row in range(galaxy.rows):
            for col in range(galaxy.cols):
                if galaxy.get_fog(col, row, who='ai') != FOG_HIDDEN:
                    continue

                dist = abs(col - self.col) + abs(row - self.row)
                if dist > self.fuel:
                    continue

                rightward_bonus = (col - self.col) * 0.25
                score           = -dist + rightward_bonus

                if score > best_score:
                    best_score = score
                    best_pos   = (col, row)

        return best_pos

    def _follow_path(self) -> Optional[Tuple[int, int]]:
        if not self.path:
            self.target = None
            self._target_ratio = -1.0
            return None

        next_pos = self.path.pop(0)
        dcol = next_pos[0] - self.col
        drow = next_pos[1] - self.row

        if abs(dcol) > 1 or abs(drow) > 1:
            self.path = []
            self.target = None
            self._target_ratio = -1.0
            return None

        return (dcol, drow)