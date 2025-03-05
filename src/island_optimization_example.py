#!/usr/bin/env python3
"""Example script demonstrating island model genetic algorithm for battle optimization.

This script shows how to use island model optimization to find better solutions
by running multiple genetic algorithms in parallel with occasional migration.
"""

import random
import multiprocessing
from collections import Counter
from typing import List, Tuple, Optional

from components.unit_type import UnitType
from battle_optimizer import optimize_battle, is_better_fitness_lex, print_solution_details
from unit_values import unit_values


def print_progress(
    generation: int,
    solution: List[Tuple[UnitType, Tuple[int, int]]],
    fitness: Tuple[float, float, float],
    island_label: str = "",
) -> None:
    """Print progress information after each generation.
    
    Args:
        generation: The current generation number.
        solution: The best solution found so far.
        fitness: The fitness values (win_value, points_used, health_value) of the best solution.
        island_label: Optional label for the island.
    """
    prefix = f"{island_label} - " if island_label else ""
    first_objective, second_objective, third_objective = fitness
    
    # Count unit types
    unit_counts = Counter(unit_type for unit_type, _ in solution)
    total_points = sum(count * unit_values[unit_type] for unit_type, count in unit_counts.items())
    
    print(f"\n{prefix}Generation {generation}:")
    print(f"  Quality: {first_objective:.2f}, {second_objective:.2f}, {third_objective:.2f}")
    print(f"  Total points: {total_points}")
    print("  Unit composition:")
    for unit_type, count in unit_counts.items():
        total_cost = count * unit_values[unit_type]
        print(f"    {count}x {unit_type.name} (cost: {total_cost})")


def run_island_model_optimization(
    battle_id: str,
    available_unit_types: List[UnitType],
    num_islands: int = 4,
    island_population: int = 50,
    island_generations: int = 15,
    num_epochs: int = 3,
    battle_timeout: float = 120.0,
    optimization_timeout: float = 600.0,
    mutation_rate: float = 0.4,
    crossover_rate: float = 0.7,
) -> Tuple[Optional[List[Tuple[UnitType, Tuple[int, int]]]], Optional[Tuple[float, float, float]]]:
    """Run optimization with an island model.
    
    Args:
        battle_id: The ID of the battle to optimize.
        available_unit_types: List of available unit types.
        num_islands: Number of islands (separate populations).
        island_population: Population size per island.
        island_generations: Number of generations per epoch.
        num_epochs: Number of migration events.
        battle_timeout: Maximum duration for battle simulation.
        optimization_timeout: Maximum duration for the entire optimization.
        mutation_rate: Base mutation rate.
        crossover_rate: Base crossover rate.
        
    Returns:
        A tuple of (best solution, fitness) or (None, None) if no solution was found.
    """
    # Calculate cores per island
    total_cores = multiprocessing.cpu_count()
    cores_per_island = max(1, (total_cores - 1) // num_islands)
    print(f"Total CPU cores: {total_cores}")
    print(f"Using {cores_per_island} cores per island")
    
    # Initialize islands
    print("\nStarting island model optimization...")
    print(f"Number of islands: {num_islands}")
    print(f"Population per island: {island_population}")
    print(f"Generations per epoch: {island_generations}")
    print(f"Number of epochs: {num_epochs}")
    
    # Initialize islands
    islands = []
    island_best_solutions = []
    island_best_fitnesses = []
    
    # Initial optimization for each island
    for i in range(num_islands):
        print(f"\n=== Island {i+1} Initial Optimization ===")
        solution, fitness = optimize_battle(
            battle_id=battle_id,
            available_unit_types=available_unit_types,
            population_size=island_population,
            generations=island_generations,
            battle_timeout=battle_timeout,
            optimization_timeout=optimization_timeout / (num_islands * num_epochs),
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            progress_callback=lambda gen, sol, fit: print_progress(gen, sol, fit, f"Island {i+1}"),
            early_stopping=False,  # Disable early stopping within epochs
            n_jobs=cores_per_island,
        )
        
        islands.append((solution, fitness))
        if solution and fitness:
            island_best_solutions.append(solution)
            island_best_fitnesses.append(fitness)
    
    # Migration and further optimization
    for epoch in range(1, num_epochs):
        print(f"\n=== Migration Epoch {epoch} ===")
        
        # Perform migration (exchange best solutions between islands)
        if len(island_best_solutions) >= 2:  # Need at least 2 islands with solutions
            migrated_solutions = []
            
            # For each island, get the best solution from another random island
            for i in range(num_islands):
                if i < len(island_best_solutions):
                    # Select a random different island to get solution from
                    other_islands = [j for j in range(len(island_best_solutions)) if j != i]
                    if other_islands:
                        source_island = random.choice(other_islands)
                        migrated_solutions.append(island_best_solutions[source_island])
                    else:
                        # Fallback if no other islands have solutions
                        migrated_solutions.append(None)
                else:
                    migrated_solutions.append(None)
        
            # Continue optimization for each island with migration
            new_islands = []
            for i in range(num_islands):
                if i < len(island_best_solutions) and migrated_solutions[i]:
                    print(f"\n=== Island {i+1} Optimization with Migration ===")
                    
                    # Create a new population with the migrated solution
                    seed = []
                    if migrated_solutions[i]:
                        seed.append(migrated_solutions[i])
                    if i < len(island_best_solutions):
                        seed.append(island_best_solutions[i])
                    
                    solution, fitness = optimize_battle(
                        battle_id=battle_id,
                        available_unit_types=available_unit_types,
                        population_size=island_population,
                        generations=island_generations,
                        battle_timeout=battle_timeout,
                        optimization_timeout=optimization_timeout / (num_islands * num_epochs),
                        mutation_rate=mutation_rate,
                        crossover_rate=crossover_rate,
                        progress_callback=lambda gen, sol, fit: print_progress(gen, sol, fit, f"Island {i+1}"),
                        early_stopping=False,
                        seed_solutions=seed,
                        n_jobs=cores_per_island,
                    )
                    
                    new_islands.append((solution, fitness))
                    
                    # Update best solution for this island using lexicographic comparison
                    if solution and fitness:
                        if i < len(island_best_solutions):
                            if is_better_fitness_lex(fitness, island_best_fitnesses[i]):
                                island_best_solutions[i] = solution
                                island_best_fitnesses[i] = fitness
                        else:
                            island_best_solutions.append(solution)
                            island_best_fitnesses.append(fitness)
                else:
                    # If this island doesn't have a solution yet, just optimize normally
                    if i < len(islands):
                        new_islands.append(islands[i])
            
            islands = new_islands
    
    # Find the best solution across all islands
    best_solution = None
    best_fitness = None
    
    for solution, fitness in islands:
        if solution and fitness:
            if best_solution is None or is_better_fitness_lex(fitness, best_fitness):
                best_solution = solution
                best_fitness = fitness
    
    return best_solution, best_fitness


def main() -> None:
    """Run the island model optimization example."""
    # Configuration
    battle_id = "A Balanced Army"  # Replace with your battle ID
    
    # Only use core units for this example
    available_unit_types: List[UnitType] = []
    for unit_type in unit_values.keys():
        if unit_type.name.lower().startswith("core_"):
            available_unit_types.append(unit_type)
    
    # Run island model optimization
    best_solution, best_fitness = run_island_model_optimization(
        battle_id=battle_id,
        available_unit_types=available_unit_types,
        num_islands=4,
        island_population=50,
        island_generations=15,
        num_epochs=3,
        battle_timeout=120.0,
        optimization_timeout=600.0,
        mutation_rate=0.4,
        crossover_rate=0.7,
    )
    
    # Print final results
    if best_solution and best_fitness:
        print("\n=== Best Solution Across All Islands ===")
        print_solution_details(best_solution, best_fitness)
        
        # Print the solution in a format that can be easily copied
        print("\nSolution in code format:")
        print("[")
        for unit_type, position in best_solution:
            print(f"    (UnitType.{unit_type.name}, {position}),")
        print("]")
    else:
        print("\nNo solution found within the time limit")


if __name__ == "__main__":
    main() 