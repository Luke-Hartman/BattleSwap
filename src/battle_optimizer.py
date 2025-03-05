"""Battle optimization using genetic algorithms.

This module provides functionality for optimizing battle team compositions and positions
using a genetic algorithm. It builds on the generic genetic algorithm framework.
"""

import os
import random
import time
import multiprocessing
from typing import Dict, List, Optional, Tuple, Any, Callable

import numpy as np
import pygame
import esper
import shapely

from genetic_algorithm import GeneticAlgorithm, setup_deap_types, adaptive_mutation_rate
from auto_battle import BattleOutcome, simulate_battle
from battles import Battle, get_battle_id
from components.health import Health
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType
from unit_values import unit_values
from handlers.combat_handler import CombatHandler
from handlers.state_machine import StateMachine
from entities.units import load_sprite_sheets
from visuals import load_visual_sheets
from scene_utils import get_legal_placement_area, clip_to_polygon


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


def print_solution_details(
    solution: List[Tuple[UnitType, Tuple[int, int]]], 
    fitness: Tuple[float, float, float]
) -> None:
    """Print detailed information about a solution.
    
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


def is_better_fitness_lex(
    fitness_a: Tuple[float, float, float], 
    fitness_b: Tuple[float, float, float]
) -> bool:
    """Compare two fitness values using lexicographic ordering.
    
    Fitness tuples are structured as:
    - For winning solutions: (win_value, -points_used, team1_health)
    - For losing solutions: (loss_value, team2_health, -points_used)
    
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


class BattleOptimizer:
    """Genetic algorithm optimizer for battle solutions.
    
    Uses the generic genetic algorithm framework to optimize battle team compositions
    and positions.
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
        n_jobs: int = -1,
    ):
        """Initialize the battle optimizer.
        
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
        # Initialize Pygame with dummy video driver for headless operation
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Battle Swap")
        
        # Load game assets
        load_sprite_sheets()
        load_visual_sheets()
        
        # Set up game handlers
        self.combat_handler = CombatHandler()
        self.state_machine = StateMachine()
        
        # Set battle configuration
        self.battle = get_battle_id(battle_id)
        self.battle_timeout = battle_timeout
        self.grid_size = grid_size
        self.simulation_world_name = simulation_world_name
        
        # Set genetic algorithm parameters
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.tournament_size = tournament_size
        
        # Set up available unit types
        if available_unit_types is None:
            self.available_unit_types = list(unit_values.keys())
        else:
            self.available_unit_types = available_unit_types
            
        # Set up genetic algorithm
        self.ga = GeneticAlgorithm(
            population_size=population_size,
            generations=generations,
            crossover_rate=crossover_rate,
            mutation_rate=mutation_rate,
            tournament_size=tournament_size,
            n_jobs=n_jobs,
        )
        
        # Initialize DEAP types for lexicographic fitness
        # (win_status, -points_used, team1_health)
        setup_deap_types(fitness_weights=(1.0, 1.0, 1.0))
        
        # Set up the genetic algorithm
        self._setup_genetic_algorithm()
        
    def _get_random_legal_position(self, team_type: TeamType) -> Tuple[float, float]:
        """Generate a random position within the legal placement area.
        
        Args:
            team_type: The team type to get a legal position for.
            
        Returns:
            A tuple of (x, y) coordinates within the legal area.
        """
        # Get the legal placement area for the team
        legal_area = get_legal_placement_area(
            battle_id=self.battle.id,
            hex_coords=(0, 0),  # Use (0,0) since positions are relative
            required_team=team_type,
            include_units=False,
        )
        
        # Get the bounding box of the legal area
        minx, miny, maxx, maxy = legal_area.bounds
        
        # Use rejection sampling to get a point within the legal area
        while True:
            x = random.uniform(minx, maxx)
            y = random.uniform(miny, maxy)
            if legal_area.contains(shapely.Point(x, y)):
                return (x, y)
                
    def _create_individual(self) -> List[Tuple[UnitType, Tuple[int, int]]]:
        """Create a random individual (team composition and positions).
        
        Returns:
            A list of (unit_type, position) tuples.
        """
        # Start with smaller teams to encourage efficiency
        team_size = random.randint(3, 10)
        
        # Create a list of random units with legal positions
        return [
            (random.choice(self.available_unit_types), self._get_random_legal_position(TeamType.TEAM1))
            for _ in range(team_size)
        ]
                
    def _evaluate_solution(
        self, 
        individual: List[Tuple[UnitType, Tuple[int, int]]]
    ) -> Tuple[float, float, float]:
        """Evaluate a solution by simulating a battle.
        
        Args:
            individual: The individual to evaluate (team composition and positions).
            
        Returns:
            A tuple of (win_status, points_used, health_value).
        """
        # Skip empty solutions
        if not individual:
            return (-100.0, 1000.0, -1000.0)  # Strongly penalize empty solutions
            
        # Calculate total points used
        points_used = sum(unit_values[unit_type] for unit_type, _ in individual)
        
        # Get enemy setup from the battle
        battle_enemies = self.battle.units
        
        # Simulate the battle
        battle_result = simulate_battle(
            battle_id=self.battle.id,
            allies=individual,
            enemies=battle_enemies,
            timeout=self.battle_timeout,
            world_name=self.simulation_world_name,
        )
        
        # Calculate fitness based on battle outcome
        if battle_result == BattleOutcome.WIN:
            # For winning solutions: (win_value, -points_used, team1_health)
            team1_health = get_team_health(TeamType.TEAM1)
            
            # Winning fitness: positive score, fewer points is better, more health is better
            return (1.0, -points_used, team1_health)
        else:
            # For losing solutions: (loss_value, team2_health, -points_used)
            team2_health = get_team_health(TeamType.TEAM2)
            
            # Losing fitness: negative score, fewer enemy health is better, fewer points is better
            return (-1.0, team2_health, -points_used)
            
    def _crossover(
        self, 
        ind1: List[Tuple[UnitType, Tuple[int, int]]], 
        ind2: List[Tuple[UnitType, Tuple[int, int]]]
    ) -> Tuple[List[Tuple[UnitType, Tuple[int, int]]], List[Tuple[UnitType, Tuple[int, int]]]]:
        """Perform crossover between two individuals.
        
        This crossover preserves unit types and recombines them between parents.
        
        Args:
            ind1: First parent individual.
            ind2: Second parent individual.
            
        Returns:
            A tuple of two new individuals.
        """
        # Create new empty individuals
        new_ind1 = []
        new_ind2 = []
        
        # Handle empty individuals
        if not ind1 or not ind2:
            if ind1:
                return ind1[:], ind1[:]
            if ind2:
                return ind2[:], ind2[:]
            return [], []
            
        # Choose crossover method
        crossover_method = random.randint(1, 3)
        
        if crossover_method == 1:
            # Method 1: Spatial crossover based on center of mass
            # Calculate center of mass for each parent
            def get_center(units: List[Tuple[UnitType, Tuple[int, int]]]) -> Tuple[float, float]:
                """Calculate the center of mass of a team."""
                if not units:
                    return (0, 0)
                x_sum = sum(pos[0] for _, pos in units)
                y_sum = sum(pos[1] for _, pos in units)
                return (x_sum / len(units), y_sum / len(units))
                
            center1 = get_center(ind1)
            center2 = get_center(ind2)
            
            # Create dividing line between centers
            if center1[0] == center2[0]:
                # Vertical line if x-coordinates are the same
                for unit in ind1:
                    if unit[1][0] < center1[0]:
                        new_ind1.append(unit)
                    else:
                        new_ind2.append(unit)
                        
                for unit in ind2:
                    if unit[1][0] < center2[0]:
                        new_ind2.append(unit)
                    else:
                        new_ind1.append(unit)
            else:
                # Calculate line equation: y = mx + b
                slope = (center2[1] - center1[1]) / (center2[0] - center1[0])
                intercept = center1[1] - slope * center1[0]
                
                # Assign units based on their position relative to the line
                for unit in ind1:
                    x, y = unit[1]
                    if y < slope * x + intercept:
                        new_ind1.append(unit)
                    else:
                        new_ind2.append(unit)
                        
                for unit in ind2:
                    x, y = unit[1]
                    if y < slope * x + intercept:
                        new_ind2.append(unit)
                    else:
                        new_ind1.append(unit)
                        
        elif crossover_method == 2:
            # Method 2: Type-based crossover
            # Group units by type for each parent
            types1: Dict[UnitType, List[Tuple[UnitType, Tuple[int, int]]]] = {}
            types2: Dict[UnitType, List[Tuple[UnitType, Tuple[int, int]]]] = {}
            
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
                    
        else:
            # Method 3: Simple one-point crossover
            crossover_point1 = random.randint(0, len(ind1))
            crossover_point2 = random.randint(0, len(ind2))
            
            new_ind1 = ind1[:crossover_point1] + ind2[crossover_point2:]
            new_ind2 = ind2[:crossover_point2] + ind1[crossover_point1:]
            
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
        """Perform mutation on an individual.
        
        This mutation can add, remove, or modify units in the team.
        
        Args:
            individual: The individual to mutate.
            
        Returns:
            A tuple containing the mutated individual.
        """
        # Create a copy of the individual
        mutant = individual[:]
        
        # Skip empty individuals
        if not mutant:
            # Add a random unit
            mutant.append((
                random.choice(self.available_unit_types),
                self._get_random_legal_position(TeamType.TEAM1)
            ))
            return (mutant,)
            
        # Choose a mutation type
        mutation_type = random.randint(1, 5)
        
        if mutation_type == 1 and len(mutant) > 1:
            # Remove a random unit (if there's more than one)
            index = random.randint(0, len(mutant) - 1)
            del mutant[index]
            
        elif mutation_type == 2:
            # Add a random unit (if not too many already)
            if len(mutant) < 15:  # Limit team size
                mutant.append((
                    random.choice(self.available_unit_types),
                    self._get_random_legal_position(TeamType.TEAM1)
                ))
                
        elif mutation_type == 3:
            # Change a unit's type
            index = random.randint(0, len(mutant) - 1)
            unit_type, position = mutant[index]
            new_type = random.choice(self.available_unit_types)
            mutant[index] = (new_type, position)
            
        elif mutation_type == 4:
            # Change a unit's position
            index = random.randint(0, len(mutant) - 1)
            unit_type, _ = mutant[index]
            mutant[index] = (
                unit_type,
                self._get_random_legal_position(TeamType.TEAM1)
            )
            
        else:
            # Swap two units' positions
            if len(mutant) >= 2:
                i1, i2 = random.sample(range(len(mutant)), 2)
                ut1, pos1 = mutant[i1]
                ut2, pos2 = mutant[i2]
                mutant[i1] = (ut1, pos2)
                mutant[i2] = (ut2, pos1)
                
        return (mutant,)
        
    def _setup_genetic_algorithm(self) -> None:
        """Set up the genetic algorithm with the appropriate operators."""
        # Register individual creation
        self.ga.register_population(self._create_individual)
        
        # Register evaluation function
        self.ga.register_evaluation(self._evaluate_solution, parallel=False)
        
        # Register genetic operators
        self.ga.register_operations(self._crossover, self._mutate)
        
    def optimize(
        self,
        seed_solutions: Optional[List[List[Tuple[UnitType, Tuple[int, int]]]]] = None,
        early_stopping: bool = True,
        early_stopping_generations: int = 5,
        progress_callback: Optional[Callable[[int, List[Tuple[UnitType, Tuple[int, int]]], Tuple[float, float, float]], None]] = None,
    ) -> Tuple[List[Tuple[UnitType, Tuple[int, int]]], Tuple[float, float, float]]:
        """Run the optimization to find the best team composition.
        
        Args:
            seed_solutions: Optional list of solutions to seed the initial population.
            early_stopping: Whether to stop early if no improvement is found.
            early_stopping_generations: Number of generations with no improvement before stopping.
            progress_callback: Function to call after each generation with progress information.
            
        Returns:
            A tuple of (best solution, fitness values).
        """
        # Run the genetic algorithm
        solution, fitness = self.ga.run(
            seed_population=seed_solutions,
            early_stopping=early_stopping,
            early_stopping_generations=early_stopping_generations,
            progress_callback=progress_callback,
        )
        
        return solution, fitness


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
    progress_callback: Optional[Callable[[int, List[Tuple[UnitType, Tuple[int, int]]], Tuple[float, float, float]], None]] = None,
    early_stopping: bool = True,
    early_stopping_generations: int = 5,
    seed_solutions: Optional[List[List[Tuple[UnitType, Tuple[int, int]]]]] = None,
    n_jobs: int = -1
) -> Tuple[Optional[List[Tuple[UnitType, Tuple[int, int]]]], Optional[Tuple[float, float, float]]]:
    """Optimize a battle team composition with timeout protection.
    
    Args:
        battle_id: ID of the battle to optimize.
        available_unit_types: List of available unit types.
        population_size: Size of the population.
        generations: Number of generations to evolve.
        battle_timeout: Maximum duration for battle simulation.
        optimization_timeout: Maximum duration for the entire optimization.
        mutation_rate: Probability of mutation.
        crossover_rate: Probability of crossover.
        simulation_world_name: Name for the simulation world.
        progress_callback: Function to call with progress information.
        early_stopping: Whether to stop early if no improvement is found.
        early_stopping_generations: Number of generations with no improvement before stopping.
        seed_solutions: Optional list of solutions to seed the population.
        n_jobs: Number of parallel processes for evaluation.
        
    Returns:
        A tuple of (best solution, fitness values) or (None, None) if timeout or error.
    """
    # Record start time
    start_time = time.time()
    
    try:
        # Initialize optimizer
        optimizer = BattleOptimizer(
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
        
        # Add timeout check to progress callback
        def progress_with_timeout(gen: int, solution: List[Tuple[UnitType, Tuple[int, int]]], fitness: Tuple[float, float, float]) -> None:
            # Check for timeout
            if time.time() - start_time > optimization_timeout:
                print("Optimization timeout reached!")
                raise TimeoutError("Optimization timeout")
                
            # Call original callback if provided
            if progress_callback:
                progress_callback(gen, solution, fitness)
                
        # Run optimization
        return optimizer.optimize(
            seed_solutions=seed_solutions,
            early_stopping=early_stopping,
            early_stopping_generations=early_stopping_generations,
            progress_callback=progress_with_timeout,
        )
    except TimeoutError:
        print("Optimization was stopped due to timeout.")
        return None, None
    except Exception as e:
        print(f"Error during optimization: {e}")
        return None, None 