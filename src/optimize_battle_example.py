#!/usr/bin/env python3
"""Example script demonstrating how to use the genetic battle optimizer.

This script shows how to use the genetic battle optimizer to find optimal solutions
for a specific battle.
"""

from collections import Counter
from typing import List, Optional, Tuple
import random
import multiprocessing

from components.unit_type import UnitType
from genetic_battle_optimizer import optimize_battle, is_better_fitness_lex
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
    print(f"  Quality: {first_objective}, {second_objective}, {third_objective}")
    print(f"  Total points: {total_points}")
    print("  Unit composition:")
    for unit_type, count in unit_counts.items():
        total_cost = count * unit_values[unit_type]
        print(f"    {count}x {unit_type.name} (cost: {total_cost})")


def main() -> None:
    """Run the battle optimization example with island model."""
    # Configuration
    battle_id = "A Balanced Army"  # Replace with your battle ID
    
    # Optimization parameters
    optimization_timeout = 600.0  # 10 minutes total
    
    # Island model parameters
    num_islands = 4
    island_population = 50  # Population per island
    island_generations = 15  # Generations per island epoch
    migration_interval = 5  # Migrate every N generations
    num_epochs = 3  # Number of epochs (migration events)
    
    # Genetic algorithm parameters
    battle_timeout = 120.0  # 2 minutes
    mutation_rate = 0.4  # Higher mutation for better exploration
    crossover_rate = 0.7  # Higher crossover rate
    
    # Multiprocessing setup - use one less than the available cores for each island
    # so the system remains responsive
    total_cores = multiprocessing.cpu_count()
    cores_per_island = max(1, (total_cores - 1) // num_islands)
    print(f"Total CPU cores: {total_cores}")
    print(f"Using {cores_per_island} cores per island")
    
    # Only use core units for this example
    available_unit_types: List[UnitType] = []
    for unit_type in unit_values.keys():
        if unit_type.name.lower().startswith("core_"):
            available_unit_types.append(unit_type)
    
    # Run optimization with island model
    print("\nStarting island model optimization...")
    print(f"Number of islands: {num_islands}")
    print(f"Population per island: {island_population}")
    print(f"Generations per epoch: {island_generations}")
    print(f"Number of epochs: {num_epochs}")
    
    # Initialize islands with their own populations
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
            optimization_timeout=optimization_timeout / (num_islands * num_epochs),  # Divide timeout
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            progress_callback=lambda gen, sol, fit: print_progress(gen, sol, fit, f"Island {i+1}"),
            early_stopping=False,  # Disable early stopping for islands
            early_stopping_generations=5,
            n_jobs=cores_per_island,  # Use the calculated cores per island
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
                        early_stopping_generations=5,
                        seed_solutions=[migrated_solutions[i], island_best_solutions[i]],  # Add both migrated and local best
                        n_jobs=cores_per_island,  # Use the calculated cores per island
                    )
                    
                    new_islands.append((solution, fitness))
                    
                    # Update best solution for this island using lexicographic comparison
                    if solution and fitness:
                        if i < len(island_best_solutions):
                            # Use the utility function for lexicographic comparison
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
    best_fitness = (-float('inf'), -float('inf'), -float('inf'))
    
    for solution, fitness in islands:
        if solution and fitness:
            # Use the utility function for lexicographic comparison
            if best_solution is None or is_better_fitness_lex(fitness, best_fitness):
                best_solution = solution
                best_fitness = fitness
    
    # Print final results
    if best_solution is not None and best_fitness is not None:
        first_objective, second_objective, third_objective = best_fitness
        print("\nBest solution across all islands:")
        print(f"First objective: {first_objective}")
        print(f"Second objective: {second_objective}")
        print(f"Third objective: {third_objective}")
        
        # Count unit types in final solution
        unit_counts = Counter(unit_type for unit_type, _ in best_solution)
        total_points = sum(count * unit_values[unit_type] for unit_type, count in unit_counts.items())
        print(f"\nTotal points used: {total_points}")
        print("\nUnit composition:")
        for unit_type, count in unit_counts.items():
            total_cost = count * unit_values[unit_type]
            print(f"  {count}x {unit_type.name} (cost: {total_cost})")
        
        # Print unit positions
        print("\nUnit positions:")
        for unit_type, position in best_solution:
            print(f"  {unit_type.name} at position {position}")
        
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