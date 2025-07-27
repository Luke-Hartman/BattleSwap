"""Pre-filtered unit sets for efficient targeting."""

from enum import Enum, auto
from typing import Dict, Set
import esper

from components.position import Position
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.airborne import Airborne


class UnitSetType(Enum):
    """Enum for different pre-filtered unit sets."""
    
    # Living units by team
    TEAM1_LIVING = auto()
    TEAM2_LIVING = auto()
    
    # Living grounded units by team
    TEAM1_LIVING_GROUNDED = auto()
    TEAM2_LIVING_GROUNDED = auto()
    
    # All living units (any team)
    ALL_LIVING = auto()
    
    # All living grounded units (any team)
    ALL_LIVING_GROUNDED = auto()
    
    # All units with positions (baseline)
    ALL_POSITIONED = auto()


class UnitSetManager:
    """Manages pre-filtered unit sets for efficient targeting."""
    
    def __init__(self):
        self._unit_sets: Dict[UnitSetType, Set[int]] = {}
        self._sets_needed: Set[UnitSetType] = set()
        self._computed_this_frame = False
    
    def request_unit_set(self, set_type: UnitSetType) -> None:
        """Request that a unit set be computed this frame."""
        self._sets_needed.add(set_type)
    
    def get_unit_set(self, set_type: UnitSetType) -> Set[int]:
        """Get a pre-filtered unit set. Must call compute_sets() first."""
        if not self._computed_this_frame:
            raise RuntimeError("Must call compute_sets() before getting unit sets")
        
        if set_type not in self._unit_sets:
            return set()
        
        return self._unit_sets[set_type]
    
    def compute_sets(self) -> None:
        """Compute all requested unit sets for this frame."""
        self._unit_sets.clear()
        
        if not self._sets_needed:
            self._computed_this_frame = True
            return
        
        # Start with all positioned entities as base set
        all_positioned = set()
        for entity, (_,) in esper.get_components(Position):
            all_positioned.add(entity)
        
        # If we need the base set, store it
        if UnitSetType.ALL_POSITIONED in self._sets_needed:
            self._unit_sets[UnitSetType.ALL_POSITIONED] = all_positioned.copy()
        
        # Filter to living units
        living_units = set()
        team1_living = set()
        team2_living = set()
        
        for entity in all_positioned:
            unit_state = esper.try_component(entity, UnitState)
            if unit_state is None or unit_state.state == State.DEAD:
                continue
            
            living_units.add(entity)
            
            # Categorize by team
            team = esper.try_component(entity, Team)
            if team is not None:
                if team.type == TeamType.TEAM1:
                    team1_living.add(entity)
                elif team.type == TeamType.TEAM2:
                    team2_living.add(entity)
        
        # Store living sets if needed
        if UnitSetType.ALL_LIVING in self._sets_needed:
            self._unit_sets[UnitSetType.ALL_LIVING] = living_units.copy()
        if UnitSetType.TEAM1_LIVING in self._sets_needed:
            self._unit_sets[UnitSetType.TEAM1_LIVING] = team1_living.copy()
        if UnitSetType.TEAM2_LIVING in self._sets_needed:
            self._unit_sets[UnitSetType.TEAM2_LIVING] = team2_living.copy()
        
        # Filter to grounded units if needed
        grounded_sets_needed = {
            UnitSetType.ALL_LIVING_GROUNDED,
            UnitSetType.TEAM1_LIVING_GROUNDED,
            UnitSetType.TEAM2_LIVING_GROUNDED
        }
        
        if grounded_sets_needed & self._sets_needed:
            living_grounded = set()
            team1_living_grounded = set()
            team2_living_grounded = set()
            
            for entity in living_units:
                # Check if grounded (not airborne)
                if esper.has_component(entity, Airborne):
                    continue
                
                living_grounded.add(entity)
                
                # Categorize by team
                team = esper.try_component(entity, Team)
                if team is not None:
                    if team.type == TeamType.TEAM1:
                        team1_living_grounded.add(entity)
                    elif team.type == TeamType.TEAM2:
                        team2_living_grounded.add(entity)
            
            # Store grounded sets if needed
            if UnitSetType.ALL_LIVING_GROUNDED in self._sets_needed:
                self._unit_sets[UnitSetType.ALL_LIVING_GROUNDED] = living_grounded.copy()
            if UnitSetType.TEAM1_LIVING_GROUNDED in self._sets_needed:
                self._unit_sets[UnitSetType.TEAM1_LIVING_GROUNDED] = team1_living_grounded.copy()
            if UnitSetType.TEAM2_LIVING_GROUNDED in self._sets_needed:
                self._unit_sets[UnitSetType.TEAM2_LIVING_GROUNDED] = team2_living_grounded.copy()
        
        self._computed_this_frame = True
    
    def reset_frame(self) -> None:
        """Reset for the next frame."""
        self._sets_needed.clear()
        self._computed_this_frame = False


# Global instance for the unit set manager
unit_set_manager = UnitSetManager()