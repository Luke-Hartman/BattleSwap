from abc import ABC, abstractmethod
import math
import random
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
from functools import total_ordering
import esper
import shapely
from auto_battle import BattleOutcome, simulate_battle_with_dependencies
from battles import get_battle_id
from components.health import Health
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType
from entities.items import ItemType
from components.spell_type import SpellType
from scene_utils import get_legal_placement_area, get_legal_spell_placement_area, axial_to_world, clip_to_polygon
from point_values import unit_values, item_values, spell_values
from game_constants import get_game_constants_hash
import plotly.graph_objects as go
from pathlib import Path
import os

import numpy as np
import multiprocessing

# ALLOWED_UNIT_TYPES = [
#     UnitType.CORE_ARCHER,
#     UnitType.CORE_CAVALRY,
#     UnitType.CORE_DUELIST,
#     UnitType.CORE_SWORDSMAN,
#     UnitType.CORE_WIZARD,
#     UnitType.CRUSADER_BLACK_KNIGHT,
#     UnitType.CRUSADER_CLERIC,
#     UnitType.MISC_COMMANDER,
#     UnitType.CORE_DEFENDER,
#     UnitType.CRUSADER_GOLD_KNIGHT,
#     UnitType.CRUSADER_LONGBOWMAN,
#     UnitType.CRUSADER_PALADIN,
#     UnitType.INFANTRY_PIKEMAN,
#     UnitType.ZOMBIE_TANK,
# ]
ALLOWED_UNIT_TYPES = [
    UnitType.CORE_ARCHER,
    UnitType.CORE_VETERAN,
    UnitType.CORE_CAVALRY,
    UnitType.CORE_DUELIST,
    UnitType.CORE_LONGBOWMAN,
    UnitType.CORE_SWORDSMAN,
    UnitType.CORE_WIZARD,
    UnitType.INFANTRY_BANNER_BEARER,
    # UnitType.MISC_COMMANDER,
    UnitType.CRUSADER_BLACK_KNIGHT,
    UnitType.INFANTRY_CATAPULT,
    UnitType.CRUSADER_CLERIC,
    UnitType.INFANTRY_CROSSBOWMAN,
    UnitType.CORE_DEFENDER,
    UnitType.CRUSADER_GOLD_KNIGHT,
    UnitType.CRUSADER_GUARDIAN_ANGEL,
    UnitType.CRUSADER_PALADIN,
    UnitType.INFANTRY_PIKEMAN,
    UnitType.INFANTRY_SOLDIER,
    UnitType.ORC_BERSERKER,
    UnitType.ORC_GOBLIN,
    UnitType.ORC_WARG_RIDER,
    UnitType.ORC_WARRIOR,
    UnitType.ORC_WARCHIEF,
    UnitType.PIRATE_CAPTAIN,
    UnitType.PIRATE_CREW,
    UnitType.PIRATE_GUNNER,
    UnitType.PIRATE_CANNON,
    UnitType.PIRATE_HARPOONER,
    UnitType.SKELETON_ARCHER_NECROMANCER,
    UnitType.SKELETON_HORSEMAN_NECROMANCER,
    UnitType.SKELETON_MAGE_NECROMANCER,
    UnitType.SKELETON_SWORDSMAN_NECROMANCER,
    UnitType.SKELETON_LICH,
    # UnitType.WEREBEAR,
    UnitType.ZOMBIE_BASIC_ZOMBIE,
    UnitType.ZOMBIE_JUMPER,
    UnitType.ZOMBIE_SPITTER,
    UnitType.ZOMBIE_TANK,
    UnitType.ZOMBIE_FIGHTER,
]

ALLOWED_ITEM_TYPES = list(ItemType)

ALLOWED_SPELL_TYPES = list(SpellType)



@total_ordering
class Fitness:

    def __init__(self, outcome: BattleOutcome, points: float, team1_health: float, team2_health: float):
        self.outcome = outcome
        self.points = points
        self.team1_health = team1_health
        self.team2_health = team2_health

    def __str__(self) -> str:
        return f"Outcome: {self.outcome}, Points: {self.points}, Team 1 Health: {self.team1_health}, Team 2 Health: {self.team2_health}"

    def _as_tuple(self) -> Tuple[bool, float, float]:
        # Maximizing fitness
        if self.outcome == BattleOutcome.TEAM1_VICTORY:
            # If winning, minimize points, tie break with more team 1 health
            return (1, -self.points, self.team1_health)
        else:
            # If losing, minimize team 2 health, tie break with fewer points
            return (0, -self.team2_health, -self.points)

    def __le__(self, other: 'Fitness') -> bool:
        return self._as_tuple() <= other._as_tuple()

    def __eq__(self, other: 'Fitness') -> bool:
        return self._as_tuple() == other._as_tuple()


class Individual:
    def __init__(self, battle_id: str, unit_placements: List[Tuple[UnitType, Tuple[float, float], List[ItemType]]], spell_placements: Optional[List[Tuple[SpellType, Tuple[float, float], int]]] = None):
        self.battle_id = battle_id
        self.unit_placements = sorted(unit_placements)
        self.spell_placements = spell_placements or []
        self._fitness = None
    
    @property
    def points(self) -> float:
        unit_points = sum(unit_values[unit_type] for unit_type, _, _ in self.unit_placements)
        item_points = sum(
            item_values[item_type] 
            for _, _, items in self.unit_placements 
            for item_type in items
        )
        spell_points = sum(spell_values[spell_type] for spell_type, _, _ in self.spell_placements)
        return unit_points + item_points + spell_points
    
    def __str__(self) -> str:
        counts = Counter(unit_type for unit_type, _, _ in self.unit_placements)
        return ", ".join(f"{count} {unit_type}" for unit_type, count in counts.items())
    
    def needs_evaluation(self) -> bool:
        return self._fitness is None

    @property
    def fitness(self) -> Fitness:
        if self._fitness is None:
            raise ValueError("Fitness not evaluated")
        return self._fitness

    def short_str(self) -> str:
        return ", ".join(f"{count} {unit_type}" for unit_type, count in sorted(Counter(unit_type for unit_type, _, _ in self.unit_placements).items()))
    
    def evaluate(
        self,
        max_duration: float,
        use_powers: bool,
    ) -> Fitness:
        battle = get_battle_id(self.battle_id)
        enemy_placements = battle.enemies
        
        # Convert hex coordinates to world coordinates if hex_coords is available
        if battle.hex_coords is not None:
            from hex_grid import axial_to_world
            world_x, world_y = axial_to_world(*battle.hex_coords)
            # Convert enemy placements from relative to world coordinates
            enemy_placements = [
                (unit_type, (position[0] + world_x, position[1] + world_y), items)
                for unit_type, position, items in enemy_placements
            ]
        def _get_team_health(team_type: TeamType) -> float:
            total_health = 0
            for ent, (health, team, unit_state) in esper.get_components(Health, Team, UnitState):
                if team.type == team_type and unit_state.state != State.DEAD:
                    total_health += health.current
            return total_health

        _, fitness_result = simulate_battle_with_dependencies(
            ally_placements=self.unit_placements,
            enemy_placements=enemy_placements,
            max_duration=max_duration,
            hex_coords=battle.hex_coords if battle.hex_coords is not None else (0, 0),
            corruption_powers=battle.corruption_powers if use_powers else [],
            spell_placements=self.spell_placements,
            post_battle_callback=lambda outcome: Fitness(
                outcome=outcome,
                points=self.points,
                team1_health=_get_team_health(TeamType.TEAM1),
                team2_health=_get_team_health(TeamType.TEAM2),
            )
        )
        self._fitness = fitness_result
        return fitness_result

    def __str__(self) -> str:
        return self.short_str()

    def __eq__(self, other: 'Individual') -> bool:
        return self.unit_placements == other.unit_placements and self.spell_placements == other.spell_placements
    
    def __hash__(self) -> int:
        # Convert all lists to tuples for hashing
        unit_placements_tuple = tuple((unit_type, position, tuple(items)) for unit_type, position, items in self.unit_placements)
        spell_placements_tuple = tuple(tuple(spell) for spell in self.spell_placements)
        return hash((unit_placements_tuple, spell_placements_tuple))

def _evaluate(individual: Individual, max_duration: float, use_powers: bool):
    return individual.evaluate(max_duration, use_powers)

# Add this at the module level
_global_process_pool = None

def get_process_pool(num_processes=None):
    """Get or create the global process pool."""
    global _global_process_pool
    if _global_process_pool is None:
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()
        _global_process_pool = multiprocessing.Pool(processes=num_processes)
    return _global_process_pool

def cleanup_process_pool():
    """Clean up the global process pool when the program exits."""
    global _global_process_pool
    if _global_process_pool is not None:
        _global_process_pool.close()
        _global_process_pool.join()
        _global_process_pool = None

class Population:
    def __init__(self, individuals: List[Individual]):
        self.individuals = individuals

    def evaluate(self, max_duration: float = 120.0, use_powers: bool = False):
        game_constants_hash = get_game_constants_hash()
        game_constants_hash_changed = False
        individuals_to_evaluate = []
        for ind in self.individuals:
            if ind.needs_evaluation():
                individuals_to_evaluate.append(ind)
            elif getattr(ind, "_constants_hash", game_constants_hash) != game_constants_hash:
                individuals_to_evaluate.append(ind)
                game_constants_hash_changed = True

        if game_constants_hash_changed:
            print(f"Game constants hash changed to {game_constants_hash}")
            cleanup_process_pool()

        if not individuals_to_evaluate:
            return
        
        if len(individuals_to_evaluate) > 1:
            pool = get_process_pool()
            results = pool.starmap(_evaluate, [(ind, max_duration, use_powers) for ind in individuals_to_evaluate])
            
            # Update the fitness for each individual in the main process
            for ind, fitness in zip(individuals_to_evaluate, results):
                ind._fitness = fitness
                ind._constants_hash = game_constants_hash
        else:
            # For a single individual, avoid the overhead of using the pool
            for ind in individuals_to_evaluate:
                ind._fitness = ind.evaluate(max_duration, use_powers)
                ind._constants_hash = game_constants_hash
    @property
    def best_individuals(self) -> List[Individual]:
        best_score = max(ind.fitness for ind in self.individuals).points
        best_individuals = []
        short_strs = set()
        for individual in self.individuals:
            if individual.fitness.outcome == BattleOutcome.TEAM1_VICTORY and individual.fitness.points == best_score and individual.short_str() not in short_strs:
                best_individuals.append(individual)
                short_strs.add(individual.short_str())
        if not best_individuals:
            return [max(self.individuals, key=lambda x: x.fitness)]
        else:
            return sorted(best_individuals, key=lambda x: x.fitness.team1_health, reverse=True)

    def __str__(self) -> str:
        winning_individuals = [ind for ind in self.individuals if ind.fitness.outcome == BattleOutcome.TEAM1_VICTORY]
        losing_individuals = [ind for ind in self.individuals if ind.fitness.outcome == BattleOutcome.TEAM2_VICTORY]
        timeout_individuals = [ind for ind in self.individuals if ind.fitness.outcome == BattleOutcome.TIMEOUT]
        str = f"Best Individuals:\n"
        for ind in self.best_individuals:
            str += f"\t{ind.short_str()}\n"
            str += f"\t\t{ind.fitness}\n"
            str += f"\t\t{repr(ind.unit_placements)}\n"
        str += f"Number winning: {len(winning_individuals)}\n"
        quantiles = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]
        if len(winning_individuals) > 0:
            winning_points_quantiles = np.quantile([ind.points for ind in winning_individuals], quantiles).astype(int)
            str += f"Winning point quantiles: {winning_points_quantiles}\n"

        str += f"Number losing: {len(losing_individuals)}\n"
        if len(losing_individuals) > 0:
            losing_team2_hp_quantiles = np.quantile([ind.fitness.team2_health for ind in losing_individuals], quantiles).astype(int)
            str += f"Losing team 2 hp quantiles: {losing_team2_hp_quantiles}\n"
        str += f"Number timed out: {len(timeout_individuals)}\n"

        str += f"Number of each unit type in population:\n"
        population_counts = Counter(unit_type for ind in self.individuals for unit_type, _, _ in ind.unit_placements)
        for unit_type, count in sorted(population_counts.items(), key=lambda x: x[1], reverse=True):
            str += f"\t{unit_type:<20}: {count:<5}\n"
        
        str += f"Number of each unit type in best individuals:\n"
        best_population_counts = Counter(unit_type for ind in self.best_individuals for unit_type, _, _ in ind.unit_placements)
        for unit_type, count in sorted(best_population_counts.items(), key=lambda x: x[1], reverse=True):
            str += f"\t{unit_type:<20}: {count:<5}\n"
        return str

def _get_random_legal_position(team_type: TeamType, hex_coords: Tuple[int, int], battle_id: str) -> Tuple[float, float]:
    """Generate a random position within the legal placement area.
    
    Args:
        team_type: The team type to get legal area for.
        hex_coords: The hex coordinates to use for the legal area.
        battle_id: The battle ID to use for the legal area.
        
    Returns:
        A tuple of (x, y) coordinates within the legal area.
    """
    # Get the legal placement area for the team
    legal_area = get_legal_placement_area(
        battle_id=battle_id,
        hex_coords=hex_coords,
        required_team=team_type,
        include_units=False,
    )
    min_x, min_y, max_x, max_y = legal_area.bounds

    while True:
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        if legal_area.contains(shapely.Point(x, y)):
            return (x, y)

def _get_random_legal_unit_type() -> UnitType:
    return random.choice(
        ALLOWED_UNIT_TYPES
    )

def _get_random_spell_position(battle_id: str, hex_coords: Tuple[int, int]) -> Tuple[float, float]:
    """Get a random legal position for a spell within the battlefield."""
    from scene_utils import get_legal_spell_placement_area
    
    legal_area = get_legal_spell_placement_area(battle_id, hex_coords)
    
    # Get bounding box of legal area
    minx, miny, maxx, maxy = legal_area.bounds
    
    # Try to find a valid position within the legal area
    for _ in range(100):  # Try up to 100 times
        x = random.uniform(minx, maxx)
        y = random.uniform(miny, maxy)
        point = shapely.Point(x, y)
        if legal_area.contains(point):
            return (x, y)
    
    # If we can't find a valid position, return center of battlefield
    hex_center_x, hex_center_y = axial_to_world(*hex_coords)
    return (hex_center_x, hex_center_y)

def _validate_team1_positions(individual: 'Individual') -> bool:
    """Validate that all team 1 units and spells are in legal positions.
    
    Args:
        individual: The individual to validate
        
    Returns:
        True if all positions are legal, False otherwise
    """
    # Get the same battle context as the mutation functions
    battle = get_battle_id(individual.battle_id)
    hex_coords = battle.hex_coords or (0, 0)
    
    # Get legal placement areas for team 1 (without considering existing units as obstacles)
    unit_legal_area = get_legal_placement_area(
        battle_id=individual.battle_id,
        hex_coords=hex_coords,
        required_team=TeamType.TEAM1,
        include_units=False,
        additional_unit_positions=None
    )
    
    spell_legal_area = get_legal_spell_placement_area(
        battle_id=individual.battle_id,
        hex_coords=hex_coords
    )
    
    # Check all unit positions
    for unit_type, position, _ in individual.unit_placements:
        point = shapely.Point(position[0], position[1])
        if not unit_legal_area.covers(point):
            return False
    
    # Check all spell positions for team 1 spells
    for spell_type, position, team_value in individual.spell_placements:
        if team_value == TeamType.TEAM1.value:
            point = shapely.Point(position[0], position[1])
            if not spell_legal_area.covers(point):
                return False
    
    return True

def generate_random_army(target_cost: int, battle_id: str, hex_coords: Tuple[int, int], max_decrease: int = 100) -> Tuple[List[Tuple[UnitType, Tuple[float, float], List[ItemType]]], List[Tuple[SpellType, Tuple[float, float], int]]]:
    current_cost = 0
    unit_placements = []
    spell_placements = []
    
    # First, allocate spells to ensure expensive spells have a chance
    # Randomly choose what percentage of budget to use for spells (10% to 60%)
    spell_percentage = random.uniform(0.1, 0.6)
    spell_budget = min(target_cost * spell_percentage, target_cost - 100)  # Leave at least 100 for units
    
    # Keep adding random spells until we can't afford any more
    while spell_budget > 0:
        # Get all spells we can afford
        affordable_spells = [spell_type for spell_type in ALLOWED_SPELL_TYPES if spell_values[spell_type] <= spell_budget]
        if not affordable_spells:
            break
        
        # Pick a random affordable spell
        spell_type = random.choice(affordable_spells)
        position = _get_random_spell_position(battle_id, hex_coords)
        spell_placements.append((spell_type, position, TeamType.TEAM1.value))
        spell_budget -= spell_values[spell_type]
        current_cost += spell_values[spell_type]
    
    # Then generate units with items using the remaining budget
    remaining_budget = target_cost - current_cost
    while not (remaining_budget - max_decrease <= current_cost <= target_cost):
        if current_cost > target_cost:
            # Remove a unit if we're over budget
            delete_index = random.randint(0, len(unit_placements) - 1)
            unit_type, _, items = unit_placements[delete_index]
            current_cost -= unit_values[unit_type]
            for item_type in items:
                current_cost -= item_values[item_type]
            unit_placements = unit_placements[:delete_index] + unit_placements[delete_index + 1:]
        else:
            unit_type = _get_random_legal_unit_type()
            position = _get_random_legal_position(TeamType.TEAM1, hex_coords, battle_id)
            
            # Randomly add 0-2 items to the unit
            items = []
            if random.random() < 0.3:  # 30% chance of having items
                num_items = random.randint(1, 2)
                for _ in range(num_items):
                    item_type = random.choice(ALLOWED_ITEM_TYPES)
                    items.append(item_type)
                    current_cost += item_values[item_type]
            
            unit_placements.append((unit_type, position, items))
            current_cost += unit_values[unit_type]
    
    return unit_placements, spell_placements

class Mutation(ABC):

    @abstractmethod
    def __call__(self, individual: Individual) -> Individual:
        pass

class AddRandomUnit(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        new_unit = _get_random_legal_unit_type()
        new_position = _get_random_legal_position(TeamType.TEAM1, hex_coords, individual.battle_id)
        index = random.randint(0, len(individual.unit_placements))
        
        # Randomly add items to the new unit
        items = []
        if random.random() < 0.3:  # 30% chance of having items
            num_items = random.randint(1, 2)
            for _ in range(num_items):
                item_type = random.choice(ALLOWED_ITEM_TYPES)
                items.append(item_type)
        
        new_unit_placements = individual.unit_placements[:index] + [(new_unit, new_position, items)] + individual.unit_placements[index:]
        return Individual(individual.battle_id, new_unit_placements, individual.spell_placements)

class RemoveRandomUnit(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        index = random.randint(0, len(individual.unit_placements) - 1)
        new_unit_placements = individual.unit_placements[:index] + individual.unit_placements[index + 1:]
        if len(new_unit_placements) == 0:
            battle = get_battle_id(individual.battle_id)
            hex_coords = battle.hex_coords or (0, 0)
            return Individual(individual.battle_id, [(_get_random_legal_unit_type(), _get_random_legal_position(TeamType.TEAM1, hex_coords, individual.battle_id), [])], individual.spell_placements)
        return Individual(individual.battle_id, new_unit_placements, individual.spell_placements)

class RandomizeUnitPosition(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        new_position = _get_random_legal_position(TeamType.TEAM1, hex_coords, individual.battle_id)
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        new_unit_placements = individual.unit_placements[:index] + [(unit_to_mutate[0], new_position, unit_to_mutate[2])] + individual.unit_placements[index + 1:]
        return Individual(individual.battle_id, new_unit_placements, individual.spell_placements)

class RandomizeUnitType(Mutation):

    def __init__(self, max_decrease: int = 100):
        self.max_decrease = max_decrease

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        original_unit_type, position, original_items = unit_to_mutate
        
        # Calculate total cost of original unit + items
        original_cost = unit_values[original_unit_type] + sum(item_values[item_type] for item_type in original_items)
        
        # Find legal unit options within the cost constraint
        legal_options = [
            unit_type
            for unit_type in ALLOWED_UNIT_TYPES
            if unit_type != original_unit_type and unit_values[unit_type] <= original_cost
        ]
        if not legal_options:
            return individual
        
        new_unit = random.choice(legal_options)
        remaining_budget = original_cost - unit_values[new_unit]
        
        # Generate random items up to the remaining budget
        new_items = []
        if remaining_budget > 0:
            # Randomly choose how many items to add (0-3 items)
            max_items = min(3, remaining_budget // min(item_values.values()) if item_values else 0)
            num_items = random.randint(0, max_items)
            
            for _ in range(num_items):
                # Get affordable items
                affordable_items = [
                    item_type for item_type in ALLOWED_ITEM_TYPES
                    if item_values[item_type] <= remaining_budget
                ]
                if not affordable_items:
                    break
                
                item_type = random.choice(affordable_items)
                new_items.append(item_type)
                remaining_budget -= item_values[item_type]
        
        new_unit_placements = individual.unit_placements[:index] + [(new_unit, position, new_items)] + individual.unit_placements[index + 1:]
        return Individual(individual.battle_id, new_unit_placements, individual.spell_placements)

class ApplyRandomMutations(Mutation):

    def __init__(self, mutations: Dict[Mutation, float]):
        self.mutations = mutations

    def __call__(self, individual: Individual) -> Individual:
        for mutation, weight in self.mutations.items():
            if random.random() < weight:
                individual = mutation(individual)
        return individual


class PerturbPosition(Mutation):

    def __init__(self, noise_scale: float):
        self.noise_scale = noise_scale
    
    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        
        # Calculate perturbed position
        perturbed_x = unit_to_mutate[1][0] + random.gauss(0, self.noise_scale)
        perturbed_y = unit_to_mutate[1][1] + random.gauss(0, self.noise_scale)
        
        # Get legal placement area and clip the position
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        legal_area = get_legal_placement_area(
            battle_id=individual.battle_id,
            hex_coords=hex_coords,
            required_team=TeamType.TEAM1,
            include_units=False,
        )
        new_position = clip_to_polygon(legal_area, perturbed_x, perturbed_y)
        
        new_unit_placements = individual.unit_placements[:index] + [(unit_to_mutate[0], new_position, unit_to_mutate[2])] + individual.unit_placements[index + 1:]
        return Individual(individual.battle_id, new_unit_placements, individual.spell_placements)


class RandomizeSpellPosition(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        if not individual.spell_placements:
            return individual
        
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        new_position = _get_random_spell_position(individual.battle_id, hex_coords)
        index = random.randint(0, len(individual.spell_placements) - 1)
        spell_to_mutate = individual.spell_placements[index]
        new_spell_placements = individual.spell_placements[:index] + [(spell_to_mutate[0], new_position, spell_to_mutate[2])] + individual.spell_placements[index + 1:]
        return Individual(individual.battle_id, individual.unit_placements, new_spell_placements)


class PerturbSpellPosition(Mutation):

    def __init__(self, noise_scale: float):
        self.noise_scale = noise_scale
    
    def __call__(self, individual: Individual) -> Individual:
        if not individual.spell_placements:
            return individual
        
        index = random.randint(0, len(individual.spell_placements) - 1)
        spell_to_mutate = individual.spell_placements[index]
        
        # Calculate perturbed position
        perturbed_x = spell_to_mutate[1][0] + random.gauss(0, self.noise_scale)
        perturbed_y = spell_to_mutate[1][1] + random.gauss(0, self.noise_scale)
        
        # Get legal spell placement area and clip the position
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        legal_area = get_legal_spell_placement_area(individual.battle_id, hex_coords)
        new_position = clip_to_polygon(legal_area, perturbed_x, perturbed_y)
        
        new_spell_placements = individual.spell_placements[:index] + [(spell_to_mutate[0], new_position, spell_to_mutate[2])] + individual.spell_placements[index + 1:]
        return Individual(individual.battle_id, individual.unit_placements, new_spell_placements)


class AddRandomSpell(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        new_spell_type = random.choice(ALLOWED_SPELL_TYPES)
        new_position = _get_random_spell_position(individual.battle_id, hex_coords)
        
        new_spell_placements = individual.spell_placements + [(new_spell_type, new_position, TeamType.TEAM1.value)]
        return Individual(individual.battle_id, individual.unit_placements, new_spell_placements)


class RemoveRandomSpell(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        if not individual.spell_placements:
            return individual
        
        index = random.randint(0, len(individual.spell_placements) - 1)
        new_spell_placements = individual.spell_placements[:index] + individual.spell_placements[index + 1:]
        return Individual(individual.battle_id, individual.unit_placements, new_spell_placements)


class RemoveRandomItem(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        # Find all units that have items
        units_with_items = [
            (i, unit_type, position, items) 
            for i, (unit_type, position, items) in enumerate(individual.unit_placements)
            if items
        ]
        
        if not units_with_items:
            return individual
        
        # Select a random unit with items
        unit_index, unit_type, position, items = random.choice(units_with_items)
        
        # Remove the first instance of a random item from this unit
        item_to_remove = random.choice(items)
        new_items = list(items)  # Create a copy
        new_items.remove(item_to_remove)  # Remove only the first instance
        
        # Create new unit placements with the updated items
        new_unit_placements = list(individual.unit_placements)
        new_unit_placements[unit_index] = (unit_type, position, new_items)
        
        return Individual(individual.battle_id, new_unit_placements, individual.spell_placements)


class ReplaceSubarmy(Mutation):

    def __init__(self, max_decrease: int = 100):
        self.max_decrease = max_decrease

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        original_score = individual.points
        kept_unit_placements = list(individual.unit_placements)
        random.shuffle(kept_unit_placements)
        index = random.randint(0, len(kept_unit_placements) - 1)
        kept_unit_placements = kept_unit_placements[:index]

        if individual.spell_placements:
            kept_spell_placements = list(individual.spell_placements)
            random.shuffle(kept_spell_placements)
            index = random.randint(0, len(kept_spell_placements) - 1)
            kept_spell_placements = kept_spell_placements[:index]
        else:
            kept_spell_placements = []
        
        # Calculate cost of kept units including items
        kept_unit_cost = sum(
            unit_values[unit_type] + sum(item_values[item_type] for item_type in items)
            for unit_type, _, items in kept_unit_placements
        )

        kept_spell_cost = sum(spell_values[spell_type] for spell_type, _, _ in kept_spell_placements)
        
        # Replacement budget = original total - kept unit cost
        # This allows the new subarmy to include both units and spells
        replacement_budget = original_score - kept_unit_cost - kept_spell_cost

        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)  # Default to (0,0) if no hex coords
        new_subarmy_unit_placements, new_subarmy_spell_placements = generate_random_army(replacement_budget, individual.battle_id, hex_coords, self.max_decrease)
        
        # Return with kept units + new subarmy units, and new subarmy spells
        # The new subarmy spells replace the original spells
        return Individual(individual.battle_id, kept_unit_placements + new_subarmy_unit_placements, kept_spell_placements + new_subarmy_spell_placements)


class MoveNextToAlly(Mutation):

    def __init__(self, noise_scale: float):
        self.noise_scale = noise_scale

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        random_ally_index = random.randint(0, len(individual.unit_placements) - 1)
        random_other_ally_index = random.randint(0, len(individual.unit_placements) - 1)
        # Can be the same ally
        random_ally = individual.unit_placements[random_ally_index]
        random_other_ally = individual.unit_placements[random_other_ally_index]
        # Move random_ally next to random_other_ally
        new_position = random_other_ally[1]
        def distance(position1: Tuple[float, float], position2: Tuple[float, float]) -> float:
            return math.sqrt((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2)
        while distance(new_position, random_other_ally[1]) < 10:
            new_position = (
                random.gauss(random_other_ally[1][0], self.noise_scale),
                random.gauss(random_other_ally[1][1], self.noise_scale)
            )
        # Clip to legal placement area for Team 1 to avoid illegal positions
        battle = get_battle_id(individual.battle_id)
        hex_coords = battle.hex_coords or (0, 0)
        legal_area = get_legal_placement_area(
            battle_id=individual.battle_id,
            hex_coords=hex_coords,
            required_team=TeamType.TEAM1,
            include_units=False,
        )
        clipped_position = clip_to_polygon(legal_area, new_position[0], new_position[1])
        return Individual(
            individual.battle_id,
            individual.unit_placements[:random_ally_index] + [(random_ally[0], clipped_position, random_ally[2])] + individual.unit_placements[random_ally_index + 1:],
            individual.spell_placements
        )


class All(Mutation):

    def __init__(self, mutations: List[Mutation]):
        self.mutations = mutations

    def __call__(self, individual: Individual) -> Individual:
        for mutation in self.mutations:
            individual = mutation(individual)
        return individual


class Crossover(ABC):

    @abstractmethod
    def __call__(self, individual1: Individual, individual2: Individual) -> Tuple[Individual, Individual]:
        pass

class SinglePointCrossover(Crossover):

    def __call__(self, individual1: Individual, individual2: Individual) -> Tuple[Individual, Individual]:
        while True:
            left_split_index = random.randint(0, len(individual1.unit_placements))
            right_split_index = random.randint(0, len(individual2.unit_placements))
            left_unit_placements = individual1.unit_placements[:left_split_index] + individual2.unit_placements[right_split_index:]
            right_unit_placements = individual2.unit_placements[:right_split_index] + individual1.unit_placements[left_split_index:]
            if not left_unit_placements or not right_unit_placements:
                continue
            return Individual(individual1.battle_id, left_unit_placements, individual1.spell_placements), Individual(individual2.battle_id, right_unit_placements, individual2.spell_placements)


class RandomMixCrossover(Crossover):

    def __call__(self, individual1: Individual, individual2: Individual) -> Tuple[Individual, Individual]:
        while True:
            new_unit_placements1 = []
            new_unit_placements2 = []
            for unit_type, position, items in individual1.unit_placements:
                if random.random() < 0.5:
                    new_unit_placements1.append((unit_type, position, items))  
                else:
                    new_unit_placements2.append((unit_type, position, items))
            for unit_type, position, items in individual2.unit_placements:
                if random.random() < 0.5:
                    new_unit_placements1.append((unit_type, position, items))
                else:
                    new_unit_placements2.append((unit_type, position, items))
            if not new_unit_placements1 or not new_unit_placements2:
                continue
            return Individual(individual1.battle_id, new_unit_placements1, individual1.spell_placements), Individual(individual2.battle_id, new_unit_placements2, individual2.spell_placements)


class ChooseRandomCrossover(Crossover):

    def __init__(self, crossovers: Dict[Crossover, float]):
        self.crossovers = crossovers

    def __call__(self, individual1: Individual, individual2: Individual) -> Individual:
        crossover = random.choices(list(self.crossovers.keys()), weights=list(self.crossovers.values()))[0]
        return crossover(individual1, individual2)


class SelectIndividual(ABC):

    @abstractmethod
    def __call__(self, population: Population) -> Individual:
        pass


class TournamentSelection(SelectIndividual):

    def __init__(self, tournament_size: int):
        self.tournament_size = tournament_size

    def __call__(self, population: Population) -> Individual:
        tournament_individuals = random.sample(population.individuals, self.tournament_size)
        return max(tournament_individuals, key=lambda x: x.fitness)


class UniformSelection(SelectIndividual):

    def __call__(self, population: Population) -> Individual:
        return random.choice(population.individuals)


class Evolution(ABC):

    @abstractmethod
    def __call__(self, population: Population) -> Population:
        pass


class EvolutionWithElitism(Evolution):

    def __init__(
        self,
        elitism_size: int,
        individual_selector: SelectIndividual,
        crossover: Crossover,
        mutation: Mutation,
        crossover_rate: float,
        mutation_rate: float,
    ):
        self.elitism_size = elitism_size
        self.individual_selector = individual_selector
        self.crossover = crossover
        self.mutation = mutation
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate

    def __call__(self, population: Population) -> Population:
        sorted_individuals = sorted(population.individuals, key=lambda x: x.fitness, reverse=True)
        new_generation = set(sorted_individuals[:self.elitism_size])
        while len(new_generation) < len(population.individuals):
            parent1 = self.individual_selector(population)
            parent2 = self.individual_selector(population)
            if random.random() < self.crossover_rate:
                child1, child2 = self.crossover(parent1, parent2)
            else:
                child1 = parent1
                child2 = parent2
            if random.random() < self.mutation_rate:
                child1 = self.mutation(child1)
            if random.random() < self.mutation_rate:
                child2 = self.mutation(child2)
            new_generation.add(child1)
            new_generation.add(child2)
        return Population(list(new_generation)[:len(population.individuals)])


class EvolutionStrategy(Evolution):

    def __init__(
        self,
        mutations: List[Mutation],
        selector: SelectIndividual,
        parents_per_generation: int,
        children_per_generation: int,
        mutation_adaptation_rate: float = 0.1,
        category_cap: int = 3,
        n_mutations: int = 1,
        use_powers: bool = False,
    ):
        self.mutations = mutations
        self.selector = selector
        self.parents_per_generation = parents_per_generation
        self.children_per_generation = children_per_generation
        self.mutation_rates = {
            mutation: 1/len(mutations)
            for mutation in mutations
        }
        self.mutation_adaptation_rate = mutation_adaptation_rate
        self.category_cap = category_cap
        self.n_mutations = n_mutations
        self.use_powers = use_powers

    def __call__(self, population: Population) -> Population:
        parents = population.individuals

        # Generate children
        next_generation = set(parents)
        mutation_pairs = []
        while len(next_generation) < self.children_per_generation + self.parents_per_generation:
            parent = self.selector(population)
            mutations = random.choices(list(self.mutation_rates.keys()), weights=list(self.mutation_rates.values()), k=self.n_mutations)
            child = parent
            for mutation in mutations:
                child = mutation(child)
                # Validate that all team 1 units/spells are in legal positions after mutation
                if not _validate_team1_positions(child):
                    print(f"Validation failed after mutation: {mutation.__class__.__name__}")
                    assert False, f"Mutation {mutation.__class__.__name__} resulted in illegal positions for team 1"
            if child not in next_generation:
                mutation_pairs.extend((mutation, parent, child) for mutation in mutations)
                next_generation.add(child)

        # Evaluate parents + children
        parents_and_children = Population(list(next_generation))
        parents_and_children.evaluate(use_powers=self.use_powers)

        # Select the next generation
        individuals = []
        category_counts = defaultdict(int)
        for individual in sorted(parents_and_children.individuals, key=lambda x: x.fitness, reverse=True):
            category = tuple(sorted(Counter(
                unit_type for unit_type, _, _ in individual.unit_placements
            ).items()))
            if category_counts[category] < self.category_cap:
                individuals.append(individual)
                category_counts[category] += 1
            if len(individuals) >= self.parents_per_generation:
                break

        next_population = Population(individuals)

        # Update mutation rates
        mutation_successes = defaultdict(int)
        mutation_counts = defaultdict(int)
        
        for mutation, parent, child in mutation_pairs:
            mutation_counts[mutation] += 1
            if child.fitness > parent.fitness:
                mutation_successes[mutation] += 1
        
        for mutation in self.mutations:
            successes = mutation_successes[mutation]
            failures = mutation_counts[mutation] - successes
            total = successes + failures
            self.mutation_rates[mutation] = (
                self.mutation_rates[mutation] * (1 + self.mutation_adaptation_rate * ((successes - failures) / (total + 1)))
            )

        return next_population


class Plotter(ABC):

    @abstractmethod
    def update(self, population: Population):
        pass

    @abstractmethod
    def create_plot(self) -> str:
        pass

    def save_plot(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.create_plot())


class UnitCountsPlotter(Plotter):

    def __init__(self):
        self.unit_counts_history = defaultdict(list)
    
    def update(self, population: Population):
        population_counts = Counter(
            unit_type 
            for ind in population.individuals 
            for unit_type, _, _ in ind.unit_placements
        )
        for unit_type in ALLOWED_UNIT_TYPES:
            self.unit_counts_history[unit_type].append(population_counts.get(unit_type, 0))
        
    def create_plot(self) -> str:
        """Create and save the unit counts plot."""
        fig = go.Figure()
        
        for unit_type in ALLOWED_UNIT_TYPES:
            counts = self.unit_counts_history[unit_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=unit_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        fig.update_layout(
            title="Unit Type Population Over Generations",
            xaxis_title="Generation",
            yaxis_title="Unit Count",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)  # Add right margin for legend
        )
        return fig.to_html()


class UnitValuesPlotter(Plotter):

    def __init__(self):
        self.unit_values_history = defaultdict(list)

    def update(self, population: Population):
        total_unit_values = defaultdict(int)
        for ind in population.individuals:
            for unit_type, _, _ in ind.unit_placements:
                total_unit_values[unit_type] += unit_values[unit_type]
        for unit_type in ALLOWED_UNIT_TYPES:
            self.unit_values_history[unit_type].append(total_unit_values[unit_type])

    def create_plot(self) -> str:
        fig = go.Figure()
        for unit_type in ALLOWED_UNIT_TYPES:
            counts = self.unit_values_history[unit_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=unit_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        return fig.to_html()


class ItemCountsPlotter(Plotter):

    def __init__(self):
        self.item_counts_history = defaultdict(list)
    
    def update(self, population: Population):
        population_counts = Counter()
        for ind in population.individuals:
            for _, _, items in ind.unit_placements:
                for item_type in items:
                    population_counts[item_type] += 1
        
        for item_type in ALLOWED_ITEM_TYPES:
            self.item_counts_history[item_type].append(population_counts.get(item_type, 0))
        
    def create_plot(self) -> str:
        """Create and save the item counts plot."""
        fig = go.Figure()
        
        for item_type in ALLOWED_ITEM_TYPES:
            counts = self.item_counts_history[item_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=item_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        fig.update_layout(
            title="Item Type Population Over Generations",
            xaxis_title="Generation",
            yaxis_title="Item Count",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)  # Add right margin for legend
        )
        return fig.to_html()


class ItemValuesPlotter(Plotter):

    def __init__(self):
        self.item_values_history = defaultdict(list)

    def update(self, population: Population):
        total_item_values = defaultdict(int)
        for ind in population.individuals:
            for _, _, items in ind.unit_placements:
                for item_type in items:
                    total_item_values[item_type] += item_values[item_type]
        for item_type in ALLOWED_ITEM_TYPES:
            self.item_values_history[item_type].append(total_item_values[item_type])

    def create_plot(self) -> str:
        fig = go.Figure()
        for item_type in ALLOWED_ITEM_TYPES:
            counts = self.item_values_history[item_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=item_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        fig.update_layout(
            title="Item Type Values Over Generations",
            xaxis_title="Generation",
            yaxis_title="Total Item Value",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)
        )
        return fig.to_html()


class SpellCountsPlotter(Plotter):

    def __init__(self):
        self.spell_counts_history = defaultdict(list)
    
    def update(self, population: Population):
        population_counts = Counter()
        for ind in population.individuals:
            for spell_type, _, _ in ind.spell_placements:
                population_counts[spell_type] += 1
        
        for spell_type in ALLOWED_SPELL_TYPES:
            self.spell_counts_history[spell_type].append(population_counts.get(spell_type, 0))
        
    def create_plot(self) -> str:
        """Create and save the spell counts plot."""
        fig = go.Figure()
        
        for spell_type in ALLOWED_SPELL_TYPES:
            counts = self.spell_counts_history[spell_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=spell_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        fig.update_layout(
            title="Spell Type Population Over Generations",
            xaxis_title="Generation",
            yaxis_title="Spell Count",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)  # Add right margin for legend
        )
        return fig.to_html()


class SpellValuesPlotter(Plotter):

    def __init__(self):
        self.spell_values_history = defaultdict(list)

    def update(self, population: Population):
        total_spell_values = defaultdict(int)
        for ind in population.individuals:
            for spell_type, _, _ in ind.spell_placements:
                total_spell_values[spell_type] += spell_values[spell_type]
        for spell_type in ALLOWED_SPELL_TYPES:
            self.spell_values_history[spell_type].append(total_spell_values[spell_type])

    def create_plot(self) -> str:
        fig = go.Figure()
        for spell_type in ALLOWED_SPELL_TYPES:
            counts = self.spell_values_history[spell_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=spell_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        fig.update_layout(
            title="Spell Type Values Over Generations",
            xaxis_title="Generation",
            yaxis_title="Total Spell Value",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)
        )
        return fig.to_html()


class AllCountsPlotter(Plotter):
    """Combined plotter for units, items, and spells counts."""

    def __init__(self):
        self.unit_counts_history = defaultdict(list)
        self.item_counts_history = defaultdict(list)
        self.spell_counts_history = defaultdict(list)
    
    def update(self, population: Population):
        # Count units
        unit_counts = Counter(
            unit_type 
            for ind in population.individuals 
            for unit_type, _, _ in ind.unit_placements
        )
        for unit_type in ALLOWED_UNIT_TYPES:
            self.unit_counts_history[unit_type].append(unit_counts.get(unit_type, 0))
        
        # Count items
        item_counts = Counter()
        for ind in population.individuals:
            for _, _, items in ind.unit_placements:
                for item_type in items:
                    item_counts[item_type] += 1
        for item_type in ALLOWED_ITEM_TYPES:
            self.item_counts_history[item_type].append(item_counts.get(item_type, 0))
        
        # Count spells
        spell_counts = Counter()
        for ind in population.individuals:
            for spell_type, _, _ in ind.spell_placements:
                spell_counts[spell_type] += 1
        for spell_type in ALLOWED_SPELL_TYPES:
            self.spell_counts_history[spell_type].append(spell_counts.get(spell_type, 0))
    
    def create_plot(self) -> str:
        """Create combined counts plot for units, items, and spells."""
        fig = go.Figure()
        
        # Add units
        for unit_type in ALLOWED_UNIT_TYPES:
            counts = self.unit_counts_history[unit_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=f"Unit: {unit_type.name}",
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        # Add items
        for item_type in ALLOWED_ITEM_TYPES:
            counts = self.item_counts_history[item_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=f"Item: {item_type.name}",
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        # Add spells
        for spell_type in ALLOWED_SPELL_TYPES:
            counts = self.spell_counts_history[spell_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=f"Spell: {spell_type.name}",
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        fig.update_layout(
            title="Units/Items/Spells Population Over Generations",
            xaxis_title="Generation",
            yaxis_title="Count",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=200)  # Add right margin for legend
        )
        return fig.to_html()


class AllValuesPlotter(Plotter):
    """Combined plotter for units, items, and spells values."""

    def __init__(self):
        self.unit_values_history = defaultdict(list)
        self.item_values_history = defaultdict(list)
        self.spell_values_history = defaultdict(list)

    def update(self, population: Population):
        # Calculate unit values
        total_unit_values = defaultdict(int)
        for ind in population.individuals:
            for unit_type, _, _ in ind.unit_placements:
                total_unit_values[unit_type] += unit_values[unit_type]
        for unit_type in ALLOWED_UNIT_TYPES:
            self.unit_values_history[unit_type].append(total_unit_values[unit_type])
        
        # Calculate item values
        total_item_values = defaultdict(int)
        for ind in population.individuals:
            for _, _, items in ind.unit_placements:
                for item_type in items:
                    total_item_values[item_type] += item_values[item_type]
        for item_type in ALLOWED_ITEM_TYPES:
            self.item_values_history[item_type].append(total_item_values[item_type])
        
        # Calculate spell values
        total_spell_values = defaultdict(int)
        for ind in population.individuals:
            for spell_type, _, _ in ind.spell_placements:
                total_spell_values[spell_type] += spell_values[spell_type]
        for spell_type in ALLOWED_SPELL_TYPES:
            self.spell_values_history[spell_type].append(total_spell_values[spell_type])

    def create_plot(self) -> str:
        """Create combined values plot for units, items, and spells."""
        fig = go.Figure()
        
        # Add units
        for unit_type in ALLOWED_UNIT_TYPES:
            values = self.unit_values_history[unit_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(values))),
                y=values,
                name=f"Unit: {unit_type.name}",
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        # Add items
        for item_type in ALLOWED_ITEM_TYPES:
            values = self.item_values_history[item_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(values))),
                y=values,
                name=f"Item: {item_type.name}",
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        # Add spells
        for spell_type in ALLOWED_SPELL_TYPES:
            values = self.spell_values_history[spell_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(values))),
                y=values,
                name=f"Spell: {spell_type.name}",
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        fig.update_layout(
            title="Units/Items/Spells Values Over Generations",
            xaxis_title="Generation",
            yaxis_title="Total Value",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=200)
        )
        return fig.to_html()


class PlotGroup(Plotter):

    def __init__(
        self,
        plotters: List[Plotter],
    ):
        self.plotters = plotters

    def update(self, population: Population):
        for plotter in self.plotters:
            plotter.update(population)

    def create_plot(self) -> str:
        html = ""
        for plotter in self.plotters:
            html += plotter.create_plot()
        return html

def random_population(
    battle_id: str,
    size: int,
) -> Population:
    min_target_cost = 300
    max_target_cost = 3000
    battle = get_battle_id(battle_id)
    hex_coords = battle.hex_coords or (0, 0)  # Default to (0,0) if no hex coords
    return Population([
        Individual(battle_id, *generate_random_army(random.randint(min_target_cost, max_target_cost), battle_id, hex_coords))
        for _ in range(size)
    ])

def main():

    BATTLE_ID = "Soldiers"
    PARENTS_PER_GENERATION = 50
    CHILDREN_PER_GENERATION = 10
    CATEGORY_CAP = 1
    TOURNAMENT_SIZE = None
    USE_POWERS = False

    population = random_population(battle_id=BATTLE_ID, size=PARENTS_PER_GENERATION)
    population.evaluate()
    evolution = EvolutionStrategy(
        mutations=[
            RemoveRandomUnit(),
            PerturbPosition(noise_scale=10),
            PerturbPosition(noise_scale=100),
            RandomizeUnitPosition(),
            ReplaceSubarmy(),
            RandomizeUnitType(),
            MoveNextToAlly(noise_scale=20),
            RemoveRandomItem(),
        ],
        selector=TournamentSelection(tournament_size=TOURNAMENT_SIZE) if TOURNAMENT_SIZE is not None else UniformSelection(),
        parents_per_generation=PARENTS_PER_GENERATION,
        children_per_generation=CHILDREN_PER_GENERATION,
        mutation_adaptation_rate=0.1,
        n_mutations=1,
        use_powers=USE_POWERS,
        category_cap=CATEGORY_CAP if CATEGORY_CAP is not None else PARENTS_PER_GENERATION,
    )
    
    # Initialize the population plotter
    plotter = PlotGroup(
        plotters=[
            AllCountsPlotter(),
            AllValuesPlotter(),
        ],
    )
    
    # Plot initial population
    plotter.update(population)
    
    generation = 1  # Start at 1 since we've plotted generation 0
    try:
        while True:
            print(f"Generation {generation}")
            
            # Evolve the population
            population = evolution(population)
            
            # Print status
            print(population)
            # print(evolution.mutation_rates)
            
            # Update the plot with the evolved population
            plotter.update(population)
            plotter.save_plot(f"plots/battle.html")
            
            generation += 1
    finally:
        # Make sure to clean up the process pool when done
        cleanup_process_pool()

if __name__ == "__main__":
    main()
    # import cProfile
    # import pstats

    # # Run the profiler
    # profiler = cProfile.Profile()
    # profiler.enable()
    # main()
    # profiler.disable()

    # # Print the stats
    # stats = pstats.Stats(profiler)
    # stats.sort_stats('cumulative')
    # stats.print_stats()
