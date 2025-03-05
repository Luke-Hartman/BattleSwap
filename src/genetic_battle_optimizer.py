"""Genetic algorithm module for optimizing battle solutions.

This module uses the DEAP library to find optimal battle solutions with minimal points.
It evaluates solutions based on battle outcomes, remaining health, and point costs.
"""

import os
import random
import time
import math
import multiprocessing
from functools import partial
from typing import Dict, List, Optional, Tuple, Any, Callable

import numpy as np
from deap import algorithms, base, creator, tools

import esper
import pygame
from auto_battle import BattleOutcome, simulate_battle
from battles import Battle, get_battle_id
from components.health import Health
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType
from handlers.combat_handler import CombatHandler
from handlers.state_machine import StateMachine
from unit_values import unit_values
from entities.units import load_sprite_sheets
from visuals import load_visual_sheets
from scene_utils import get_legal_placement_area, clip_to_polygon
import shapely
import sys

def get_team_health(team_type: TeamType) -> int:
    """Get the total remaining health of a team.

    Args:
        team_type: The team type to check.

    Returns:
        The total remaining health of the team.
    """
    total_health = 0
    for ent, (health, team, unit_state) in esper.get_components(Health, Team, UnitState):
        if team.type == team_type and unit_state.state != State.DEAD:
            total_health += health.current
    return total_health


def print_solution_details(solution: List[Tuple[UnitType, Tuple[int, int]]], fitness: Tuple[float, float, float]) -> None:
    """Print detailed information about a solution, including unit type counts and positions.
    
    Args:
        solution: The solution to print details for.
        fitness: The fitness values of the solution.
    """
    from collections import Counter
    
    # Print fitness values
    print(f"Fitness: {fitness}")
    
    # Calculate and print total points
    points_used = sum(unit_values[unit_type] for unit_type, _ in solution)
    print(f"Total points: {points_used}")
    
    # Count unit types and print
    unit_counts = Counter(unit_type for unit_type, _ in solution)
    print("Unit composition:")
    for unit_type, count in unit_counts.items():
        total_cost = count * unit_values[unit_type]
        print(f"  {count}x {unit_type.name} (cost: {total_cost})")

def is_better_fitness_lex(fitness_a: Tuple[float, float, float], fitness_b: Tuple[float, float, float]) -> bool:
    """Compare two fitness values using lexicographic ordering.
    
    Fitness tuples are structured as:
    - For winning solutions: (win_value, -points_used, team1_health)
    - For losing solutions: (loss_value, team2_health, -points_used)
    
    Lexicographic priority:
    1. Winning status (win_value >= 0 is better than loss_value < 0)
    2. If winning: points used (fewer/less negative is better)
    3. If winning: team1 health (more is better)
    4. If losing: enemy health (less is better)
    5. If losing: points used (fewer/less negative is better)
    
    Args:
        fitness_a: First fitness value to compare.
        fitness_b: Second fitness value to compare.
        
    Returns:
        True if fitness_a is better than fitness_b using lexicographic ordering.
    """
    # First check if one is winning and one is losing
    if fitness_a[0] >= 0 and fitness_b[0] < 0:
        return True  # A is winning, B is losing
    if fitness_a[0] < 0 and fitness_b[0] >= 0:
        return False  # A is losing, B is winning
        
    # If both winning or both losing, use different orderings
    if fitness_a[0] >= 0:  # Both winning
        # First objective: winning (higher is better)
        if fitness_a[0] > fitness_b[0]:
            return True
        if fitness_a[0] < fitness_b[0]:
            return False
            
        # If winning status is equal, compare points (less negative is better)
        if fitness_a[1] > fitness_b[1]:
            return True
        if fitness_a[1] < fitness_b[1]:
            return False
            
        # If points are equal, compare health (higher is better)
        return fitness_a[2] > fitness_b[2]
    else:  # Both losing
        # First objective: loss margin (higher/closer to 0 is better)
        if fitness_a[0] > fitness_b[0]:
            return True
        if fitness_a[0] < fitness_b[0]:
            return False
            
        # For losing solutions, next most important is enemy health (lower is better)
        if fitness_a[1] < fitness_b[1]:
            return True
        if fitness_a[1] > fitness_b[1]:
            return False
            
        # If enemy health is equal, compare points (less negative is better)
        return fitness_a[2] > fitness_b[2]

class GeneticBattleOptimizer:
    """Genetic algorithm optimizer for battle solutions.

    This class uses DEAP to evolve optimal battle solutions that use minimal points
    while still winning the battle.
    """

    def __init__(
        self,
        battle_id: str,
        available_unit_types: Optional[List[UnitType]] = None,
        population_size: int = 50,
        generations: int = 20,
        battle_timeout: float = 120.0,
        mutation_rate: float = 0.2,
        crossover_rate: float = 0.5,
        tournament_size: int = 3,
        grid_size: Tuple[int, int] = (10, 10),
        simulation_world_name: str = "genetic_simulation",
        n_jobs: int = -1,  # Number of processes to use (-1 = all available cores)
    ):
        """Initialize the genetic battle optimizer.

        Args:
            battle_id: The ID of the battle to optimize.
            available_unit_types: List of unit types available for the solution.
                If None, all unit types will be used.
            population_size: Size of the population.
            generations: Number of generations to evolve.
            battle_timeout: Maximum duration for battle simulation in seconds.
            mutation_rate: Probability of mutating an individual.
            crossover_rate: Probability of crossing over two individuals.
            tournament_size: Size of the tournament for selection.
            grid_size: Size of the battle grid (width, height).
            simulation_world_name: Name of the simulation world to use.
            n_jobs: Number of parallel processes to use for evaluation.
                If -1, use all available cores.
        """
        os.environ['SDL_VIDEODRIVER'] = 'dummy'

        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Battle Swap")
        load_sprite_sheets()
        load_visual_sheets()
        self.combat_handler = CombatHandler()
        self.state_machine = StateMachine()
        self.battle = get_battle_id(battle_id)
        self.battle_timeout = battle_timeout
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        self.grid_size = grid_size
        self.simulation_world_name = simulation_world_name
        
        # Set up multiprocessing
        if n_jobs == -1:
            self.n_jobs = multiprocessing.cpu_count()
        else:
            self.n_jobs = n_jobs
        
        # If no unit types are provided, use all available unit types
        if available_unit_types is None:
            self.available_unit_types = list(unit_values.keys())
        else:
            self.available_unit_types = available_unit_types
        
        # Set up the DEAP framework
        self._setup_deap()
    
    def _get_random_legal_position(self, team_type: TeamType) -> Tuple[float, float]:
        """Generate a random position within the legal placement area.
        
        Uses rejection sampling to ensure uniform distribution within the legal area.
        
        Args:
            team_type: The team type to get legal area for.
            
        Returns:
            A tuple of (x, y) coordinates within the legal area.
        """
        # Get the legal placement area for the team
        legal_area = get_legal_placement_area(
            battle_id=self.battle.id,
            hex_coords=(0, 0),  # We use (0,0) since positions are relative
            required_team=team_type,
            include_units=False,  # Don't include unit spacing since we're just ensuring basic bounds
        )
        
        # Get the bounding box of the legal area
        minx, miny, maxx, maxy = legal_area.bounds
        
        # Use rejection sampling to get a point within the legal area
        while True:
            x = random.uniform(minx, maxx)
            y = random.uniform(miny, maxy)
            if legal_area.contains(shapely.Point(x, y)):
                return (x, y)

    def _setup_deap(self) -> None:
        """Set up the DEAP framework for genetic algorithm."""
        # Clean up DEAP creator to avoid errors when reusing
        if hasattr(creator, "FitnessLex"):
            del creator.FitnessLex
        if hasattr(creator, "Individual"):
            del creator.Individual
        
        # Create a fitness class with lexicographic ordering
        # This replaces the weighted multi-objective approach
        creator.create("FitnessLex", base.Fitness)
        
        # Override the comparison methods to implement lexicographic ordering
        def gt(self, other):
            # First check if one is winning and one is losing
            if self.values[0] >= 0 and other.values[0] < 0:
                return True  # Self is winning, other is losing
            if self.values[0] < 0 and other.values[0] >= 0:
                return False  # Self is losing, other is winning
            
            # If both winning or both losing, use different orderings
            if self.values[0] >= 0:  # Both winning
                # First objective: winning (higher is better)
                if self.values[0] > other.values[0]:
                    return True
                if self.values[0] < other.values[0]:
                    return False
                
                # For winning solutions, next most important is points (less negative is better)
                if self.values[1] > other.values[1]:
                    return True
                if self.values[1] < other.values[1]:
                    return False
                
                # If points are equal, compare health (higher is better)
                return self.values[2] > other.values[2]
            else:  # Both losing
                # First objective: loss margin (higher/closer to 0 is better)
                if self.values[0] > other.values[0]:
                    return True
                if self.values[0] < other.values[0]:
                    return False
                
                # For losing solutions, next most important is enemy health (lower is better)
                if self.values[1] < other.values[1]:
                    return True
                if self.values[1] > other.values[1]:
                    return False
                
                # If enemy health is equal, compare points (less negative is better)
                return self.values[2] > other.values[2]
        
        def lt(self, other):
            # First check if one is winning and one is losing
            if self.values[0] >= 0 and other.values[0] < 0:
                return False  # Self is winning, other is losing
            if self.values[0] < 0 and other.values[0] >= 0:
                return True  # Self is losing, other is winning
            
            # If both winning or both losing, use different orderings
            if self.values[0] >= 0:  # Both winning
                # First objective: winning (higher is better)
                if self.values[0] < other.values[0]:
                    return True
                if self.values[0] > other.values[0]:
                    return False
                
                # For winning solutions, next most important is points (less negative is better)
                if self.values[1] < other.values[1]:
                    return True
                if self.values[1] > other.values[1]:
                    return False
                
                # If points are equal, compare health (higher is better)
                return self.values[2] < other.values[2]
            else:  # Both losing
                # First objective: loss margin (higher/closer to 0 is better)
                if self.values[0] < other.values[0]:
                    return True
                if self.values[0] > other.values[0]:
                    return False
                
                # For losing solutions, next most important is enemy health (lower is better)
                if self.values[1] > other.values[1]:
                    return True
                if self.values[1] < other.values[1]:
                    return False
                
                # If enemy health is equal, compare points (less negative is better)
                return self.values[2] < other.values[2]
        
        # Add the comparison methods to the FitnessLex class
        creator.FitnessLex.__gt__ = gt
        creator.FitnessLex.__lt__ = lt
        
        # Set weights for compatibility with existing code
        # (1.0, 1.0, 1.0) means higher is better for all objectives
        creator.FitnessLex.weights = (1.0, 1.0, 1.0)
        
        # Create individual class with the lexicographic fitness
        creator.create("Individual", list, fitness=creator.FitnessLex)
        
        # Initialize toolbox
        self.toolbox = base.Toolbox()
        
        # Register unit type generator
        self.toolbox.register(
            "unit_type", 
            random.choice, 
            self.available_unit_types
        )
        
        # Register position generator using rejection sampling
        self.toolbox.register(
            "position",
            self._get_random_legal_position,
            TeamType.TEAM1  # Always Team1 for ally positions
        )
        
        # Register unit generator (unit_type, position)
        self.toolbox.register(
            "unit", 
            lambda: (self.toolbox.unit_type(), self.toolbox.position())
        )
        
        # Register individual generator - variable size teams
        # Start with smaller teams to encourage efficiency
        self.toolbox.register(
            "individual", 
            tools.initRepeat, 
            creator.Individual,
            self.toolbox.unit,
            # Use a smaller starting range to encourage efficiency
            n=random.randint(3, 10)
        )
        
        # Register population generator
        self.toolbox.register(
            "population", 
            tools.initRepeat, 
            list, 
            self.toolbox.individual, 
            n=self.population_size
        )
        
        # Register evaluation function
        self.toolbox.register("evaluate", self._evaluate_solution)
        
        # Register genetic operators
        self.toolbox.register("mate", self._crossover)
        self.toolbox.register("mutate", self._mutate)
        
        # Custom tournament selection that respects lexicographic ordering
        def selLexicographicTournament(individuals, k, tournsize):
            """Tournament selection based on lexicographic ordering.
            
            Args:
                individuals: A list of individuals to select from.
                k: The number of individuals to select.
                tournsize: The size of the tournament.
                
            Returns:
                A list of selected individuals.
            """
            chosen = []
            for i in range(k):
                # Select tournsize individuals at random
                aspirants = random.sample(individuals, tournsize)
                
                # Find the best in the tournament using lexicographic ordering
                best = aspirants[0]
                for ind in aspirants[1:]:
                    if is_better_fitness_lex(ind.fitness.values, best.fitness.values):
                        best = ind
                        
                chosen.append(best)
                
            return chosen
        
        # Register the custom selection function
        self.toolbox.register(
            "select", 
            selLexicographicTournament, 
            tournsize=self.tournament_size
        )

    def _evaluate_solution(self, individual: List[Tuple[UnitType, Tuple[int, int]]]) -> Tuple[float, float, float]:
        """Evaluate a battle solution focused on winning with minimal points.

        Args:
            individual: A list of (unit_type, position) tuples representing a solution.

        Returns:
            A tuple of (win_priority, point_efficiency, health_value) where:
            - win_priority: Very large positive value for wins, negative for losses
            - point_efficiency: -points_used (for winning solutions)
            - health_value: Remaining health (for winning solutions) or damage dealt (for losing ones)
        """
        # If the individual is empty, return a very poor fitness
        if not individual:
            return -1000.0, -10000.0, 0.0
            
        # Calculate total points used
        points_used = sum(unit_values[unit_type] for unit_type, _ in individual)
        
        # Simulate the battle
        outcome = simulate_battle(
            ally_placements=individual,
            enemy_placements=self.battle.enemies,
            max_duration=self.battle_timeout,
            delete_world=False,  # Don't delete the world yet, we need to get health values
            world_name=self.simulation_world_name,
        )
        
        # Get the remaining health for both teams
        # We need to switch to the simulation world to get the health values
        previous_world = esper.current_world
        esper.switch_world(self.simulation_world_name)
        team1_health = get_team_health(TeamType.TEAM1)
        team2_health = get_team_health(TeamType.TEAM2)
        esper.switch_world(previous_world)
        
        # Now we can safely delete the simulation world
        esper.delete_world(self.simulation_world_name)
        
        # With lexicographic ordering:
        if outcome == BattleOutcome.TEAM1_VICTORY:
            # Winning solutions:
            # 1. All winning solutions have the same first objective value (1000)
            # 2. The second objective is -points_used (higher/less negative is better)
            # 3. The third objective is remaining health (higher is better)
            win_value = 1000.0
            return win_value, -float(points_used), float(team1_health)
        else:  # TEAM2_VICTORY or TIMEOUT
            # Losing solutions:
            # 1. All losing solutions have loss_value (closer to 0 is better)
            # 2. Second objective is team2_health (lower is better)
            # 3. Third objective is -points_used (less negative is better)
            
            # Estimate how close we were to winning - use enemy health
            enemy_damage_factor = max(0, 1 - (team2_health / (100 * len(self.battle.enemies))))
            # Value ranges from -1000 to -1 based on damage dealt
            loss_value = -1000.0 + (enemy_damage_factor * 999.0)
            
            # For losing solutions, return (loss_value, team2_health, -points_used)
            return loss_value, float(team2_health), -float(points_used)
    
    def _crossover(
        self, 
        ind1: List[Tuple[UnitType, Tuple[int, int]]], 
        ind2: List[Tuple[UnitType, Tuple[int, int]]]
    ) -> Tuple[List[Tuple[UnitType, Tuple[int, int]]], List[Tuple[UnitType, Tuple[int, int]]]]:
        """Enhanced crossover operator for battle solutions that better preserves unit groupings.

        Args:
            ind1: First individual.
            ind2: Second individual.

        Returns:
            A tuple of two new individuals created by crossover.
        """
        # If either individual is empty, return copies
        if not ind1 or not ind2:
            return creator.Individual(ind1), creator.Individual(ind2)
        
        # Calculate unit density centers for each individual
        def get_center(units: List[Tuple[UnitType, Tuple[int, int]]]) -> Tuple[float, float]:
            if not units:
                return (0.0, 0.0)
            x_sum = sum(pos[0] for _, pos in units)
            y_sum = sum(pos[1] for _, pos in units)
            return (x_sum / len(units), y_sum / len(units))
        
        center1 = get_center(ind1)
        center2 = get_center(ind2)
        
        # Create new individuals
        new_ind1 = creator.Individual([])
        new_ind2 = creator.Individual([])
        
        # Determine crossover strategy based on team compositions
        if random.random() < 0.5:
            # Strategic crossover - try to preserve unit clusters
            
            # Sort units by distance from center
            ind1_sorted = sorted(ind1, key=lambda unit: ((unit[1][0] - center1[0])**2 + (unit[1][1] - center1[1])**2))
            ind2_sorted = sorted(ind2, key=lambda unit: ((unit[1][0] - center2[0])**2 + (unit[1][1] - center2[1])**2))
            
            # Choose crossover points based on distance from center
            # This tends to keep nearby units together in the same child
            cx_point1 = random.randint(0, len(ind1_sorted))
            cx_point2 = random.randint(0, len(ind2_sorted))
            
            # Create children using crossover points
            new_ind1 = creator.Individual(ind1_sorted[:cx_point1] + ind2_sorted[cx_point2:])
            new_ind2 = creator.Individual(ind2_sorted[:cx_point2] + ind1_sorted[cx_point1:])
        else:
            # Unit-type based crossover - try to preserve unit type balance
            
            # Group units by type
            types1 = {}
            types2 = {}
            
            for unit in ind1:
                unit_type = unit[0]
                if unit_type not in types1:
                    types1[unit_type] = []
                types1[unit_type].append(unit)
                
            for unit in ind2:
                unit_type = unit[0]
                if unit_type not in types2:
                    types2[unit_type] = []
                types2[unit_type].append(unit)
            
            # Get all unique unit types
            all_types = set(list(types1.keys()) + list(types2.keys()))
            
            # For each unit type, randomly decide which parent to take units from
            for unit_type in all_types:
                from_parent1 = random.random() < 0.5
                
                # Get units of this type from the selected parent
                if from_parent1 and unit_type in types1:
                    new_ind1.extend(types1[unit_type])
                    if unit_type in types2:
                        new_ind2.extend(types2[unit_type])
                else:
                    if unit_type in types1:
                        new_ind2.extend(types1[unit_type])
                    if unit_type in types2:
                        new_ind1.extend(types2[unit_type])
        
        # Ensure each child has at least one unit
        if not new_ind1 and ind1:
            new_ind1.append(random.choice(ind1))
        elif not new_ind1 and ind2:
            new_ind1.append(random.choice(ind2))
            
        if not new_ind2 and ind2:
            new_ind2.append(random.choice(ind2))
        elif not new_ind2 and ind1:
            new_ind2.append(random.choice(ind1))
        
        return new_ind1, new_ind2
    
    def _mutate(
        self, 
        individual: List[Tuple[UnitType, Tuple[int, int]]]
    ) -> Tuple[List[Tuple[UnitType, Tuple[int, int]]]]:
        """Enhanced mutation operator for battle solutions.

        This mutation can:
        1. Add a new unit
        2. Remove a unit
        3. Change a unit type
        4. Change a unit position
        5. Shift unit formations
        6. Clone successful unit types

        Args:
            individual: The individual to mutate.

        Returns:
            A tuple containing the mutated individual.
        """
        if not individual:
            # If empty, add a unit
            individual.append((self.toolbox.unit_type(), self.toolbox.position()))
            return individual,
        
        # Choose mutation type with weighted probabilities
        mutation_types = ["add", "remove", "change_type", "change_position", "shift_formation", "clone_unit"]
        mutation_weights = [0.2, 0.1, 0.2, 0.3, 0.1, 0.1]  # Higher weight for position changes
        
        mutation_type = random.choices(mutation_types, weights=mutation_weights, k=1)[0]
        
        if mutation_type == "add":
            # Add a new unit - try to place it near existing units
            if individual:
                # Get a random existing unit's position
                _, existing_pos = random.choice(individual)
                
                # Place new unit near the existing one with some variation
                spread = 2.0  # Adjust this value to control how far new units are placed
                new_x = existing_pos[0] + random.uniform(-spread, spread)
                new_y = existing_pos[1] + random.uniform(-spread, spread)
                
                # Ensure the position is legal
                attempted = 0
                while attempted < 5:  # Try a few times to find a legal position
                    attempted += 1
                    point = shapely.Point(new_x, new_y)
                    legal_area = get_legal_placement_area(
                        battle_id=self.battle.id,
                        hex_coords=(0, 0),
                        required_team=TeamType.TEAM1,
                        include_units=False,
                    )
                    if legal_area.contains(point):
                        individual.append((self.toolbox.unit_type(), (new_x, new_y)))
                        break
                    else:
                        # Try a different position
                        new_x = existing_pos[0] + random.uniform(-spread, spread)
                        new_y = existing_pos[1] + random.uniform(-spread, spread)
                
                # If we couldn't find a legal position, fall back to the default approach
                if attempted >= 5:
                    individual.append((self.toolbox.unit_type(), self.toolbox.position()))
            else:
                # No existing units, so just add randomly
                individual.append((self.toolbox.unit_type(), self.toolbox.position()))
        
        elif mutation_type == "remove" and len(individual) > 1:
            # Remove a random unit - bias towards removing expensive units to encourage efficiency
            unit_costs = [(i, unit_values[unit_type]) for i, (unit_type, _) in enumerate(individual)]
            # Normalize costs to use as weights - higher cost = higher chance of removal
            total_cost = sum(cost for _, cost in unit_costs)
            weights = [cost/total_cost for _, cost in unit_costs] if total_cost > 0 else None
            
            # Choose unit to remove with weights (or randomly if weights can't be calculated)
            idx = random.choices([i for i, _ in unit_costs], weights=weights, k=1)[0] if weights else random.randint(0, len(individual) - 1)
            individual.pop(idx)
        
        elif mutation_type == "change_type":
            # Change a unit type - bias towards cheaper unit types
            idx = random.randint(0, len(individual) - 1)
            unit_type, position = individual[idx]
            
            # Get costs of all available unit types
            available_costs = [(ut, unit_values[ut]) for ut in self.available_unit_types]
            
            # Normalize costs inversely (lower cost = higher probability)
            total_cost = sum(cost for _, cost in available_costs)
            inv_costs = [(ut, total_cost - cost) for ut, cost in available_costs]
            total_inv = sum(inv_cost for _, inv_cost in inv_costs)
            
            # Choose new unit type with probability inversely proportional to cost
            weights = [inv_cost/total_inv for _, inv_cost in inv_costs] if total_inv > 0 else None
            new_unit_type = random.choices([ut for ut, _ in inv_costs], weights=weights, k=1)[0] if weights else random.choice(self.available_unit_types)
            
            individual[idx] = (new_unit_type, position)
        
        elif mutation_type == "change_position":
            # Change a unit position - use different strategies based on team performance
            idx = random.randint(0, len(individual) - 1)
            unit_type, old_position = individual[idx]
            
            # Choose between random position and fine-tuning
            if random.random() < 0.3:  # 30% chance of completely new position
                new_position = self.toolbox.position()
            else:  # 70% chance of small adjustment
                # Make a small adjustment to existing position
                adjustment = random.uniform(0.5, 2.0)  # Smaller adjustments
                direction = random.uniform(0, 2 * 3.14159)  # Random direction
                
                new_x = old_position[0] + adjustment * math.cos(direction)
                new_y = old_position[1] + adjustment * math.sin(direction)
                
                # Ensure the position is legal
                attempted = 0
                while attempted < 5:  # Try a few times to find a legal position
                    attempted += 1
                    point = shapely.Point(new_x, new_y)
                    legal_area = get_legal_placement_area(
                        battle_id=self.battle.id,
                        hex_coords=(0, 0),
                        required_team=TeamType.TEAM1,
                        include_units=False,
                    )
                    if legal_area.contains(point):
                        new_position = (new_x, new_y)
                        break
                    else:
                        # Try a different adjustment
                        direction = random.uniform(0, 2 * 3.14159)
                        new_x = old_position[0] + adjustment * math.cos(direction)
                        new_y = old_position[1] + adjustment * math.sin(direction)
                
                # If we couldn't find a legal position, fall back to the default approach
                if attempted >= 5:
                    new_position = self.toolbox.position()
            
            individual[idx] = (unit_type, new_position)
        
        elif mutation_type == "shift_formation" and len(individual) > 1:
            # Shift the entire formation in a direction
            shift_x = random.uniform(-2.0, 2.0)
            shift_y = random.uniform(-2.0, 2.0)
            
            # Create a new list for the shifted individuals
            shifted_individuals = []
            
            for unit_type, (x, y) in individual:
                new_x = x + shift_x
                new_y = y + shift_y
                
                # Check if the new position is legal
                point = shapely.Point(new_x, new_y)
                legal_area = get_legal_placement_area(
                    battle_id=self.battle.id,
                    hex_coords=(0, 0),
                    required_team=TeamType.TEAM1,
                    include_units=False,
                )
                
                if legal_area.contains(point):
                    shifted_individuals.append((unit_type, (new_x, new_y)))
                else:
                    # If not legal, keep the original position
                    shifted_individuals.append((unit_type, (x, y)))
            
            # Only apply the shift if at least one unit could be moved
            if any(old[1] != new[1] for old, new in zip(individual, shifted_individuals)):
                individual[:] = shifted_individuals
        
        elif mutation_type == "clone_unit" and individual:
            # Clone a random unit and place it nearby
            unit_type, (x, y) = random.choice(individual)
            
            # Place the clone near the original with some variation
            spread = 1.5
            new_x = x + random.uniform(-spread, spread)
            new_y = y + random.uniform(-spread, spread)
            
            # Ensure the position is legal
            attempted = 0
            while attempted < 5:
                attempted += 1
                point = shapely.Point(new_x, new_y)
                legal_area = get_legal_placement_area(
                    battle_id=self.battle.id,
                    hex_coords=(0, 0),
                    required_team=TeamType.TEAM1,
                    include_units=False,
                )
                if legal_area.contains(point):
                    individual.append((unit_type, (new_x, new_y)))
                    break
                else:
                    new_x = x + random.uniform(-spread, spread)
                    new_y = y + random.uniform(-spread, spread)
            
            # If we couldn't find a legal position, fall back to the default approach
            if attempted >= 5:
                individual.append((unit_type, self.toolbox.position()))
        
        return individual,
    
    def _adaptive_mutation_rate(self, current_gen: int) -> float:
        """Calculate adaptive mutation rate based on generation number.
        
        Higher mutation rate early for exploration, lower later for exploitation.
        
        Args:
            current_gen: Current generation number.
            
        Returns:
            Adjusted mutation rate for the current generation.
        """
        # Start with higher mutation rate, gradually decrease
        return max(0.05, self.mutation_rate * (1 - (current_gen / self.generations) * 0.7))
    
    def _parallel_evaluate(self, individuals: list) -> list:
        """Evaluate multiple individuals in parallel, one at a time per process.
        
        Each process evaluates a single individual at a time and gets a new one as soon as
        it finishes, providing better load balancing than batch processing.
        
        Args:
            individuals: List of individuals to evaluate.
            
        Returns:
            List of fitness values for each individual.
        """
        if self.n_jobs == 1:
            # Single process evaluation
            return [self._evaluate_solution(ind) for ind in individuals]
        else:
            # Parallel evaluation using multiprocessing
            try:
                with multiprocessing.Pool(processes=self.n_jobs) as pool:
                    # Create a partial function with the battle parameters
                    eval_func = partial(
                        evaluate_solution_worker, 
                        battle_enemies=self.battle.enemies,
                        battle_timeout=self.battle_timeout,
                        simulation_world_name=f"{self.simulation_world_name}",
                        battle_id=self.battle.id
                    )
                    # Use imap_unordered to process individuals one at a time
                    # as processes become available
                    return list(pool.imap_unordered(eval_func, individuals))
            except KeyboardInterrupt:
                print("\nKeyboard interrupt detected. Cleaning up processes...")
                # The context manager will handle pool cleanup
                raise

    def optimize(self) -> Tuple[List[Tuple[UnitType, Tuple[int, int]]], Tuple[float, float, float]]:
        """Run the genetic algorithm to find an optimal battle solution.

        Returns:
            A tuple containing:
                - The best solution as a list of (unit_type, position) tuples
                - The fitness of the best solution (win_value, points_used, health_value)
        """
        # Create initial population
        pop = self.toolbox.population()
        
        # Track the best individual across all generations
        hof = tools.HallOfFame(1)
        
        # Track statistics
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean, axis=0)
        stats.register("min", np.min, axis=0)
        stats.register("max", np.max, axis=0)
        
        # Initialize logbook for stats
        logbook = tools.Logbook()
        logbook.header = ['gen', 'nevals'] + stats.fields
        
        # Evaluate the individuals with invalid fitness using parallel evaluation
        invalid_ind = [ind for ind in pop if not ind.fitness.valid]
        
        if invalid_ind:
            fitnesses = self._parallel_evaluate(invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
        
        # Update hall of fame and record stats
        hof.update(pop)
        record = stats.compile(pop)
        logbook.record(gen=0, nevals=len(invalid_ind), **record)
        
        # Begin the generational process
        for gen in range(1, self.generations + 1):
            # Calculate adaptive mutation rate for this generation
            current_mutation_rate = self._adaptive_mutation_rate(gen - 1)
            
            # Select the next generation individuals
            offspring = self.toolbox.select(pop, int(self.population_size * 0.3))  # mu parents
            offspring = list(map(self.toolbox.clone, offspring))
            
            # Generate lambda offspring via crossover and mutation
            offspring_size = self.population_size - len(offspring)
            
            # Fill offspring using crossover and mutation
            while len(offspring) < self.population_size:
                # Select 2 parents
                parent1 = tools.selRandom(pop, 1)[0]
                parent2 = tools.selRandom(pop, 1)[0]
                
                # Apply crossover
                if random.random() < self.crossover_rate:
                    child1, child2 = self.toolbox.mate(
                        self.toolbox.clone(parent1), 
                        self.toolbox.clone(parent2)
                    )
                    # Apply mutation with adaptive rate
                    if random.random() < current_mutation_rate:
                        child1, = self.toolbox.mutate(child1)
                    if random.random() < current_mutation_rate:
                        child2, = self.toolbox.mutate(child2)
                    # Delete fitness values
                    del child1.fitness.values, child2.fitness.values
                    # Add to offspring
                    offspring.append(child1)
                    if len(offspring) < self.population_size:
                        offspring.append(child2)
                else:
                    # Just add mutated parents
                    child1 = self.toolbox.clone(parent1)
                    child2 = self.toolbox.clone(parent2)
                    if random.random() < current_mutation_rate:
                        child1, = self.toolbox.mutate(child1)
                    if random.random() < current_mutation_rate:
                        child2, = self.toolbox.mutate(child2)
                    del child1.fitness.values, child2.fitness.values
                    offspring.append(child1)
                    if len(offspring) < self.population_size:
                        offspring.append(child2)
            
            # Evaluate the individuals with invalid fitness using parallel evaluation
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            
            if invalid_ind:
                fitnesses = self._parallel_evaluate(invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit
                
            # Select the next generation population (μ+λ selection)
            pop = tools.selBest(pop + offspring, self.population_size)
            
            # Update the hall of fame with the new population
            hof.update(pop)
            
            # Record statistics for this generation
            record = stats.compile(pop)
            logbook.record(gen=gen, nevals=len(invalid_ind), **record)
            
            # Print progress periodically
            if gen % 5 == 0 or gen == self.generations:
                print(f"Gen {gen}: Best fitness = {hof[0].fitness.values}")
                if gen % 5 == 0:  # Every 5 generations, print detailed information
                    print_solution_details(hof[0], hof[0].fitness.values)
                    print("")  # Add a blank line for readability
        
        # Return the best solution and its fitness
        best_solution = hof[0]
        return best_solution, best_solution.fitness.values

# Function for parallel evaluation that can be pickled
def evaluate_solution_worker(
    individual: List[Tuple[UnitType, Tuple[int, int]]],
    battle_enemies: List[Tuple[UnitType, Tuple[int, int]]],
    battle_timeout: float,
    simulation_world_name: str,
    battle_id: str,
) -> Tuple[float, float, float]:
    """Evaluate a battle solution in a separate process.
    
    This standalone function allows for parallel evaluation using multiprocessing.
    
    Args:
        individual: A list of (unit_type, position) tuples representing a solution.
        battle_enemies: The list of enemy units and their positions.
        battle_timeout: Maximum duration for battle simulation in seconds.
        simulation_world_name: Base name of the simulation world to use.
        battle_id: The ID of the battle to optimize.
        
    Returns:
        For winning solutions: (win_value, -points_used, team1_health)
        For losing solutions: (loss_value, team2_health, -points_used)
        The ordering is critical for lexicographic comparison.
    """
    # Ensure each process has a unique world name
    process_id = os.getpid()
    world_name = f"{simulation_world_name}_{process_id}"
    
    # Initialize pygame if needed (each process needs its own initialization)
    if not pygame.get_init():
        # Suppress pygame output messages
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        # Redirect stdout temporarily to suppress pygame initialization messages
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        try:
            pygame.init()
            screen = pygame.display.set_mode((800, 600))
            load_sprite_sheets()
            load_visual_sheets()
        finally:
            # Restore stdout
            sys.stdout.close()
            sys.stdout = original_stdout
    
    # If the individual is empty, return a very poor fitness
    if not individual:
        return -1000.0, 10000.0, -10000.0  # Loss, high enemy health, high cost
            
    # Calculate total points used
    points_used = sum(unit_values[unit_type] for unit_type, _ in individual)
    
    # Simulate the battle
    outcome = simulate_battle(
        ally_placements=individual,
        enemy_placements=battle_enemies,
        max_duration=battle_timeout,
        delete_world=False,  # Don't delete the world yet, we need to get health values
        world_name=world_name,
    )
    
    # Get the remaining health for both teams
    # We need to switch to the simulation world to get the health values
    previous_world = esper.current_world
    esper.switch_world(world_name)
    team1_health = get_team_health(TeamType.TEAM1)
    team2_health = get_team_health(TeamType.TEAM2)
    esper.switch_world(previous_world)
    
    # Now we can safely delete the simulation world
    esper.delete_world(world_name)
    
    # With lexicographic ordering:
    if outcome == BattleOutcome.TEAM1_VICTORY:
        # Winning solutions:
        # 1. All winning solutions have the same first objective value (1000)
        # 2. The second objective is -points_used (higher/less negative is better)
        # 3. The third objective is remaining health (higher is better)
        win_value = 1000.0
        return win_value, -float(points_used), float(team1_health)
    else:  # TEAM2_VICTORY or TIMEOUT
        # Losing solutions:
        # 1. All losing solutions have loss_value (closer to 0 is better)
        # 2. Second objective is team2_health (lower is better)
        # 3. Third objective is -points_used (less negative is better)
        
        # Estimate how close we were to winning - use enemy health
        enemy_damage_factor = max(0, 1 - (team2_health / (100 * len(battle_enemies))))
        # Value ranges from -1000 to -1 based on damage dealt
        loss_value = -1000.0 + (enemy_damage_factor * 999.0)
        
        # For losing solutions, return (loss_value, team2_health, -points_used)
        return loss_value, float(team2_health), -float(points_used)

def optimize_battle(
    battle_id: str,
    available_unit_types: Optional[List[UnitType]] = None,
    population_size: int = 50,
    generations: int = 20,
    battle_timeout: float = 120.0,
    optimization_timeout: float = 300.0,
    mutation_rate: float = 0.2,
    crossover_rate: float = 0.5,
    simulation_world_name: str = "genetic_simulation",
    progress_callback: Optional[
        Callable[
            [int, List[Tuple[UnitType, Tuple[int, int]]], Tuple[float, float, float]], 
            None
        ]
    ] = None,
    early_stopping: bool = True,
    early_stopping_generations: int = 5,
    seed_solutions: Optional[List[List[Tuple[UnitType, Tuple[int, int]]]]] = None,
    n_jobs: int = -1
) -> Tuple[
    Optional[List[Tuple[UnitType, Tuple[int, int]]]], 
    Optional[Tuple[float, float, float]]
]:
    """Optimize a battle solution using genetic algorithm.

    Args:
        battle_id: The ID of the battle to optimize.
        available_unit_types: List of unit types available for the solution.
            If None, all unit types will be used.
        population_size: Size of the population.
        generations: Number of generations to evolve.
        battle_timeout: Maximum duration for battle simulation in seconds.
        optimization_timeout: Maximum time to run the optimization in seconds.
        mutation_rate: Probability of mutating an individual.
        crossover_rate: Probability of crossing over two individuals.
        simulation_world_name: Name of the simulation world to use.
        progress_callback: Optional callback function that takes (generation_number, best_solution, best_fitness)
            as arguments. Called after each generation to report progress.
        early_stopping: Whether to stop early if no improvement is seen for early_stopping_generations.
        early_stopping_generations: Number of generations without improvement to trigger early stopping.
        seed_solutions: Optional list of solutions to include in the initial population.
        n_jobs: Number of parallel processes to use for evaluation.
            If -1, use all available cores.

    Returns:
        A tuple containing:
            - The best solution as a list of (unit_type, position) tuples, or None if timeout
            - The fitness of the best solution (win_value, points_used, health_value), or None if timeout
    """
    try:
        optimizer = GeneticBattleOptimizer(
            battle_id=battle_id,
            available_unit_types=available_unit_types,
            population_size=population_size,
            generations=generations,
            battle_timeout=battle_timeout,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            simulation_world_name=simulation_world_name,
            n_jobs=n_jobs,
        )
        
        # Custom optimization loop with early stopping
        if early_stopping or seed_solutions:
            # Track start time for timeout
            start_time = time.time()
            
            # Create initial population
            pop = optimizer.toolbox.population()
            
            # Add seed solutions to population if provided
            if seed_solutions:
                # Convert seed solutions to DEAP individuals
                for solution in seed_solutions:
                    if solution:
                        # Create a deep copy of the solution
                        ind = creator.Individual(solution[:])
                        # Replace individuals in the population with seed solutions
                        if len(pop) > 0:
                            # Replace a random individual
                            pop[random.randint(0, len(pop) - 1)] = ind
                        else:
                            # If population is empty, add the seed solution
                            pop.append(ind)
            
            # Track the best individual across all generations
            hof = tools.HallOfFame(1)
            
            # Track statistics
            stats = tools.Statistics(lambda ind: ind.fitness.values)
            stats.register("avg", np.mean, axis=0)
            stats.register("min", np.min, axis=0)
            stats.register("max", np.max, axis=0)
            
            # Initialize logbook for stats
            logbook = tools.Logbook()
            logbook.header = ['gen', 'nevals'] + stats.fields
            
            # Variables for early stopping
            best_fitness = (-float('inf'), -float('inf'), -float('inf'))
            generations_without_improvement = 0
            
            # Evaluate the individuals with invalid fitness using parallel evaluation
            invalid_ind = [ind for ind in pop if not ind.fitness.valid]
            
            if invalid_ind:
                fitnesses = optimizer._parallel_evaluate(invalid_ind)
                for ind, fit in zip(invalid_ind, fitnesses):
                    ind.fitness.values = fit
            
            # Update hall of fame and record stats
            hof.update(pop)
            if hof:
                best_fitness = hof[0].fitness.values
                if progress_callback:
                    progress_callback(0, hof[0], best_fitness)
            
            record = stats.compile(pop)
            logbook.record(gen=0, nevals=len(invalid_ind), **record)
            
            # Begin the generational process
            for gen in range(1, generations + 1):
                # Check timeout
                if time.time() - start_time > optimization_timeout:
                    print("Optimization timeout reached")
                    break
                    
                # Calculate adaptive mutation rate for this generation
                current_mutation_rate = optimizer._adaptive_mutation_rate(gen - 1)
                
                # Create offspring using the same approach as in optimize()
                offspring = optimizer.toolbox.select(pop, int(population_size * 0.3))
                offspring = list(map(optimizer.toolbox.clone, offspring))
                
                # Fill offspring using crossover and mutation
                while len(offspring) < population_size:
                    parent1 = tools.selRandom(pop, 1)[0]
                    parent2 = tools.selRandom(pop, 1)[0]
                    
                    if random.random() < crossover_rate:
                        child1, child2 = optimizer.toolbox.mate(
                            optimizer.toolbox.clone(parent1), 
                            optimizer.toolbox.clone(parent2)
                        )
                        if random.random() < current_mutation_rate:
                            child1, = optimizer.toolbox.mutate(child1)
                        if random.random() < current_mutation_rate:
                            child2, = optimizer.toolbox.mutate(child2)
                        del child1.fitness.values, child2.fitness.values
                        offspring.append(child1)
                        if len(offspring) < population_size:
                            offspring.append(child2)
                    else:
                        child1 = optimizer.toolbox.clone(parent1)
                        child2 = optimizer.toolbox.clone(parent2)
                        if random.random() < current_mutation_rate:
                            child1, = optimizer.toolbox.mutate(child1)
                        if random.random() < current_mutation_rate:
                            child2, = optimizer.toolbox.mutate(child2)
                        del child1.fitness.values, child2.fitness.values
                        offspring.append(child1)
                        if len(offspring) < population_size:
                            offspring.append(child2)
                
                # Evaluate the individuals with invalid fitness using parallel evaluation
                invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
                
                if invalid_ind:
                    fitnesses = optimizer._parallel_evaluate(invalid_ind)
                    for ind, fit in zip(invalid_ind, fitnesses):
                        ind.fitness.values = fit
                    
                # Select the next generation population (μ+λ selection)
                pop = tools.selBest(pop + offspring, population_size)
                
                # Update the hall of fame with the new population
                previous_best = best_fitness if hof else (-float('inf'), -float('inf'), -float('inf'))
                hof.update(pop)
                
                # Check for improvement using lexicographic comparison
                if hof and is_better_fitness_lex(hof[0].fitness.values, previous_best):
                    best_fitness = hof[0].fitness.values
                    generations_without_improvement = 0
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(gen, hof[0], best_fitness)
                else:
                    generations_without_improvement += 1
                
                # Record statistics
                record = stats.compile(pop)
                logbook.record(gen=gen, nevals=len(invalid_ind), **record)
                
                # Print progress periodically
                if gen % 5 == 0 or gen == generations:
                    print(f"Gen {gen}: Best fitness = {best_fitness}")
                    if gen % 5 == 0 and hof:  # Every 5 generations, print detailed information
                        print_solution_details(hof[0], best_fitness)
                        print("")  # Add a blank line for readability
                
                # Check early stopping conditions:
                # 1. If we have a winning solution (fitness[0] > 0) and have not improved for several generations
                # 2. Or if we have a really good winning solution (fitness[0] > 900)
                if early_stopping and ((best_fitness[0] > 0 and generations_without_improvement >= early_stopping_generations) or best_fitness[0] > 900):
                    print(f"Early stopping at generation {gen}, no improvement for {generations_without_improvement} generations")
                    if hof:
                        print("Final solution details:")
                        print_solution_details(hof[0], best_fitness)
                    break
            
            # Return the best solution found
            if hof:
                return hof[0], hof[0].fitness.values
            return None, None
        else:
            # Use the normal optimize method without early stopping
            return optimizer.optimize()
            
    except KeyboardInterrupt:
        print("\nOptimization interrupted by user. Cleaning up...")
        # Any remaining cleanup can be done here
        return None, None

# Test function to verify lexicographic ordering
def test_lexicographic_ordering() -> None:
    """Test function to verify lexicographic ordering works correctly.
    
    This can be run to ensure the fitness comparison behaves as expected.
    """
    # Clean up any existing DEAP classes
    if hasattr(creator, "TestFitness"):
        del creator.TestFitness
    if hasattr(creator, "TestIndividual"):
        del creator.TestIndividual
        
    # Create a test fitness class with lexicographic ordering
    creator.create("TestFitness", base.Fitness)
    
    # Define comparison methods
    def gt(self, other):
        # First check if one is winning and one is losing
        if self.values[0] >= 0 and other.values[0] < 0:
            return True  # Self is winning, other is losing
        if self.values[0] < 0 and other.values[0] >= 0:
            return False  # Self is losing, other is winning
            
        # If both winning or both losing, use different orderings
        if self.values[0] >= 0:  # Both winning
            # First objective: winning (higher is better)
            if self.values[0] > other.values[0]:
                return True
            if self.values[0] < other.values[0]:
                return False
                
            # If winning status is equal, compare points (less negative is better)
            if self.values[1] > other.values[1]:
                return True
            if self.values[1] < other.values[1]:
                return False
                
            # If points are equal, compare health (higher is better)
            return self.values[2] > other.values[2]
        else:  # Both losing
            # First objective: loss margin (higher/closer to 0 is better)
            if self.values[0] > other.values[0]:
                return True
            if self.values[0] < other.values[0]:
                return False
                
            # If loss margin is equal, compare enemy damage (higher is better)
            if self.values[2] > other.values[2]:
                return True
            if self.values[2] < other.values[2]:
                return False
                
            # If damage is equal, compare points (less negative is better)
            return self.values[1] > other.values[1]
    
    def lt(self, other):
        # First check if one is winning and one is losing
        if self.values[0] >= 0 and other.values[0] < 0:
            return False  # Self is winning, other is losing
        if self.values[0] < 0 and other.values[0] >= 0:
            return True  # Self is losing, other is winning
            
        # If both winning or both losing, use different orderings
        if self.values[0] >= 0:  # Both winning
            # First objective: winning (higher is better)
            if self.values[0] < other.values[0]:
                return True
            if self.values[0] > other.values[0]:
                return False
                
            # If winning status is equal, compare points (less negative is better)
            if self.values[1] < other.values[1]:
                return True
            if self.values[1] > other.values[1]:
                return False
                
            # If points are equal, compare health (higher is better)
            return self.values[2] < other.values[2]
        else:  # Both losing
            # First objective: loss margin (higher/closer to 0 is better)
            if self.values[0] < other.values[0]:
                return True
            if self.values[0] > other.values[0]:
                return False
                
            # For losing solutions, next most important is enemy health (lower is better)
            if self.values[1] > other.values[1]:
                return True
            if self.values[1] < other.values[1]:
                return False
                
            # If enemy health is equal, compare points (less negative is better)
            return self.values[2] < other.values[2]
    
    # Add the comparison methods to the FitnessLex class
    creator.TestFitness.__gt__ = gt
    creator.TestFitness.__lt__ = lt
    
    # Set weights for compatibility
    creator.TestFitness.weights = (1.0, 1.0, 1.0)
    
    # Create individual class
    creator.create("TestIndividual", list, fitness=creator.TestFitness)
    
    # Create some individuals with different fitness values
    print("Testing lexicographic ordering of fitness values:")
    
    # Winning solutions with different points and health
    win1 = creator.TestIndividual()
    win1.fitness.values = (1000.0, -800.0, 100.0)  # Win, 800 points, 100 health
    
    win2 = creator.TestIndividual()
    win2.fitness.values = (1000.0, -600.0, 50.0)   # Win, 600 points, 50 health
    
    win3 = creator.TestIndividual()
    win3.fitness.values = (1000.0, -600.0, 150.0)  # Win, 600 points, 150 health
    
    # Losing solutions with different damage and points
    loss1 = creator.TestIndividual()
    loss1.fitness.values = (-500.0, -400.0, 200.0)  # Moderate loss, high damage, high points
    
    loss2 = creator.TestIndividual()
    loss2.fitness.values = (-500.0, -200.0, 100.0)  # Same loss margin, low damage, low points
    
    loss3 = creator.TestIndividual()
    loss3.fitness.values = (-100.0, -800.0, 300.0)  # Close to winning, highest damage, highest points
    
    # Create a population
    population = [win1, win2, win3, loss1, loss2, loss3]
    
    # Sort by fitness
    sorted_pop = sorted(population, key=lambda ind: ind.fitness, reverse=True)
    
    # Print results
    print("\nSorted population (best to worst):")
    for i, ind in enumerate(sorted_pop):
        print(f"{i+1}. Fitness: {ind.fitness.values}")
        print(f"   Winning: {'Yes' if ind.fitness.values[0] > 0 else 'No'}")
        print(f"   Points: {-ind.fitness.values[1]}")
        print(f"   Health/Damage: {ind.fitness.values[2]}")
    
    # Verify ordering
    success = True
    expected_order = [win2, win3, win1, loss3, loss1, loss2]  # Expected ordering
    
    for i, (actual, expected) in enumerate(zip(sorted_pop, expected_order)):
        if actual.fitness.values != expected.fitness.values:
            print(f"\nError at position {i+1}:")
            print(f"Expected: {expected.fitness.values}")
            print(f"Got: {actual.fitness.values}")
            success = False
    
    if success:
        print("\nLexicographic ordering is working correctly!")
        print("For winning solutions:")
        print("  - 600-point solution ranks higher than 800-point solution when both win")
        print("  - Health is only used as a tiebreaker for solutions with identical win status and points")
        print("\nFor losing solutions:")
        print("  - Solutions closer to winning (-100) rank higher than those further from winning (-500)")
        print("  - When loss margin is equal, more damage (300) ranks higher than less damage (200)")
        print("  - Points are only considered as a final tiebreaker for losing solutions")
    else:
        print("\nLexicographic ordering test failed!")
    
    # Clean up
    del creator.TestFitness
    del creator.TestIndividual

if __name__ == "__main__":
    # Run the test if this module is executed directly
    test_lexicographic_ordering()
