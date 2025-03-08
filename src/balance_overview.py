from collections import Counter
import multiprocessing

from battles import get_battles
from battle_solver import (
    ALLOWED_UNIT_TYPES, EvolutionStrategy, AddRandomUnit, RemoveRandomUnit, 
    PerturbPosition, RandomizeUnitPosition, RandomizeUnitType, All, ReplaceSubarmy, random_population
)
from unit_values import unit_values

def grade_solution(points_used: int, battle_grades) -> str:
    """Grade a solution based on points used."""
    if battle_grades is None:
        return "N/A"
    
    if points_used < battle_grades.a_cutoff:
        return "S"  # Better than A
    elif points_used <= battle_grades.a_cutoff:
        return "A"
    elif points_used <= battle_grades.b_cutoff:
        return "B"
    elif points_used <= battle_grades.c_cutoff:
        return "C"
    elif points_used <= battle_grades.d_cutoff:
        return "D"
    else:
        return "F"

def run_balance_overview():
    """
    Runs evolutionary generations for every battle in the game and analyzes unit usage patterns.
    Each loop evolves the same populations further, showing how solutions improve over time.
    """
    print(f"Running balance overview with {multiprocessing.cpu_count()} cores")
    print("Starting balance overview analysis...")

    PARENTS_PER_GENERATION = 40
    CHILDREN_PER_GENERATION = 100
    MUTATION_ADAPTATION_RATE = 0.2
    CATEGORY_CAP = 3
    
    # Setup evolution strategy with the same parameters as the main script
    evolution = EvolutionStrategy(
        mutations=[
            RemoveRandomUnit(),
            PerturbPosition(noise_scale=10),
            PerturbPosition(noise_scale=100),
            RandomizeUnitPosition(),
            ReplaceSubarmy(),
            RandomizeUnitType(),
        ],
        parents_per_generation=PARENTS_PER_GENERATION,
        children_per_generation=CHILDREN_PER_GENERATION,
        mutation_adaptation_rate=MUTATION_ADAPTATION_RATE,
        category_cap=CATEGORY_CAP,
    )
    
    # Get all non-test battles
    battles = [b for b in get_battles() if not b.is_test]
    print(f"Initializing populations for {len(battles)} non-test battles")
    
    # Initialize populations for all battles
    battle_populations = {}
    for battle in battles:
        # Set the target cost based on the battle's grades
        target_cost = 900  # Default target cost
        if battle.grades is not None:
            # Use the D cutoff as the target cost
            target_cost = battle.grades.d_cutoff
        
        # Create initial population
        population = random_population(size=PARENTS_PER_GENERATION, target_cost=target_cost)
        
        # Evaluate the initial population
        population.evaluate(battle.enemies)
        
        # Store the population for this battle
        battle_populations[battle.id] = {
            'population': population,
            'enemy_placements': battle.enemies,
            'battle': battle
        }
        print(f"Initialized population for {battle.id}")
    
    generation = 0
    
    while True:
        print(f"\n----- GENERATION {generation} -----\n")
        
        # Track unit usage across all battles
        best_solution_unit_counts = Counter()
        all_battles_unit_counts = Counter()
        
        # Track grades for best solutions
        grade_distribution = Counter()
        
        # Process each battle
        for battle_id, battle_data in battle_populations.items():
            population = battle_data['population']
            battle = battle_data['battle']
            
            print(f"Processing battle: {battle_id}")
            
            # Get the best individual for this battle
            if population.best_individuals:
                best_individual = population.best_individuals[0]
                
                # Count units in best solution
                for unit_type, _ in best_individual.unit_placements:
                    best_solution_unit_counts[unit_type] += 1
                
                # Grade the solution
                points_used = best_individual.points
                grade = grade_solution(points_used, battle.grades)
                grade_distribution[grade] += 1
                
                print(f"  Best solution: {best_individual}")
                if battle.grades is not None:
                    print(f"  Points: {points_used}, Grade: {grade}")
            else:
                print("  No solution found")

            # Count all units used in this battle's enemy placements
            for unit_type, _ in battle.enemies:
                all_battles_unit_counts[unit_type] += 1
        
        # Report findings
        print("\n----- UNIT USAGE ANALYSIS -----")
        print(f"{'Unit Type':<20} {'Best Solutions':<15} {'All Battles':<15}")
        print("-" * 50)
        
        # Sort by most used to least used in best solutions
        for unit_type in sorted(ALLOWED_UNIT_TYPES, key=lambda x: best_solution_unit_counts.get(x, 0), reverse=True):
            all_count = all_battles_unit_counts.get(unit_type, 0)
            print(f"{unit_type.name:<20} {best_solution_unit_counts.get(unit_type, 0):<15} {all_count:<15}")
        
        # Report grade distribution
        print("\n----- GRADE DISTRIBUTION -----")
        print(f"S (better than A): {grade_distribution.get('S', 0)}")
        print(f"A: {grade_distribution.get('A', 0)}")
        print(f"B: {grade_distribution.get('B', 0)}")
        print(f"C: {grade_distribution.get('C', 0)}")
        print(f"D: {grade_distribution.get('D', 0)}")
        print(f"F: {grade_distribution.get('F', 0)}")
        print(f"N/A: {grade_distribution.get('N/A', 0)}")
        
        # Evolve each population for the next generation
        print(f"\nEvolving populations for generation {generation + 1}...")
        for battle_id, battle_data in battle_populations.items():
            print(f"Evolving population for {battle_id}")
            population = battle_data['population']
            enemy_placements = battle_data['enemy_placements']
            
            # Evolve the population
            battle_data['population'] = evolution(population, enemy_placements)
        
        generation += 1

if __name__ == "__main__":
    run_balance_overview()
    