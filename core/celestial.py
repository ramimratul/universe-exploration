# ============================================================#
# core/celestial.py — Celestial body and resource data models
#
# Currently:>>>
#   Resource tracks collection SEPARATELY for player and AI.
#   Both can collect the same resource independently (As this is exploration--- later if we add
# mission then First collects gets it)
# ====================================#

import random
from dataclasses import dataclass, field
from typing import Optional
from config import (
    BODY_EMPTY, BODY_STAR, BODY_PLANET, BODY_EXOPLANET,
    BODY_SATELLITE, BODY_ASTEROID, BODY_COMET,
    RESOURCE_NONE, RESOURCE_COMMON, RESOURCE_RARE,
    RESOURCE_EXOTIC, RESOURCE_DISCOVERY, RESOURCE_VALUES,
    BODY_SPAWN_CHANCE, BODY_TYPE_WEIGHTS,
    RESOURCE_SPAWN_CHANCE, RESOURCE_TYPE_WEIGHTS,
    HAZARD_SPAWN_CHANCE, HAZARD_EXTRA_FUEL, FUEL_MOVE_COST,
)


def weighted_choice(weights: dict) -> str:
    keys  = list(weights.keys())
    probs = list(weights.values())
    return random.choices(keys, weights=probs, k=1)[0]


# Resource
# -----------

@dataclass
class Resource:
    """
    A resource on a celestial body.
    Collection is tracked INDEPENDENTLY for player and AI.
    Both can collect the same resource and neither blocks the other.
    """
    rtype:            str  = RESOURCE_NONE
    value:            int  = 0
    collected_player: bool = False
    collected_ai:     bool = False

    @staticmethod
    def generate() -> "Resource":
        if random.random() > RESOURCE_SPAWN_CHANCE:
            return Resource()
        rtype = weighted_choice(RESOURCE_TYPE_WEIGHTS)
        return Resource(rtype=rtype, value=RESOURCE_VALUES[rtype])

    @property
    def has_resource(self) -> bool:
        """True if the resource exists at all (ignores who collected it)."""
        return self.rtype != RESOURCE_NONE

    def available_for_player(self) -> bool:
        """True if the player hasn't collected this yet."""
        return self.has_resource and not self.collected_player

    def available_for_ai(self) -> bool:
        """True if the AI hasn't collected this yet."""
        return self.has_resource and not self.collected_ai

    def collect_as_player(self) -> int:
        """Player collects — returns points, or 0 if already collected."""
        if self.available_for_player():
            self.collected_player = True
            return self.value
        return 0

    def collect_as_ai(self) -> int:
        """AI collects — returns points, or 0 if already collected."""
        if self.available_for_ai():
            self.collected_ai = True
            return self.value
        return 0



# CelestialBody
# ---------------

@dataclass
class CelestialBody:
    """
    One celestial object in a grid cell.
    """
    btype:           str      = BODY_EMPTY
    resource:        Resource = field(default_factory=Resource)
    is_hazard:       bool     = False
    extra_fuel_cost: int      = 0
    name:            str      = ""

    @staticmethod
    def generate_at(col: int, row: int) -> "CelestialBody":
        if random.random() > BODY_SPAWN_CHANCE:
            return CelestialBody(btype=BODY_EMPTY)

        btype    = weighted_choice(BODY_TYPE_WEIGHTS)
        resource = Resource.generate()

        hazard_chance = HAZARD_SPAWN_CHANCE
        if btype in (BODY_ASTEROID, BODY_COMET):
            hazard_chance *= 2.5

        is_hazard       = random.random() < hazard_chance
        extra_fuel_cost = HAZARD_EXTRA_FUEL if is_hazard else 0

        return CelestialBody(
            btype=btype, resource=resource,
            is_hazard=is_hazard, extra_fuel_cost=extra_fuel_cost,
        )

    @property
    def is_empty(self) -> bool:
        return self.btype == BODY_EMPTY

    @property
    def move_cost(self) -> int:
        return FUEL_MOVE_COST + self.extra_fuel_cost

    @property
    def has_resource(self) -> bool:
        """True if a resource exists here (either or both may have collected it)."""
        return self.resource.has_resource

    def collect_as_player(self) -> int:
        return self.resource.collect_as_player()

    def collect_as_ai(self) -> int:
        return self.resource.collect_as_ai()

    def __repr__(self) -> str:
        hazard = " [HAZARD]" if self.is_hazard else ""
        res    = f" +{self.resource.rtype}" if self.has_resource else ""
        return f"CelestialBody({self.btype}{hazard}{res})"