from collections import Counter
import multiprocessing
import os
from typing import Dict

from battles import get_battle_id, get_battles
from battle_solver import (
    ALLOWED_UNIT_TYPES, EvolutionStrategy, AddRandomUnit, GradeDistributionPlotter, MoveNextToAlly, PlotGroup, Plotter, Population, RemoveRandomUnit, 
    PerturbPosition, RandomizeUnitPosition, RandomizeUnitType, ReplaceSubarmy, TournamentSelection, UniformSelection, UnitCountsPlotter, UnitValuesPlotter, random_population
)
from unit_values import unit_values

class AllBattlesPlotter:

    def __init__(self, overview_plotter: Plotter, battle_plotters: Dict[str, Plotter]):
        self.overview_plotter = overview_plotter
        self.battle_plotters = battle_plotters

    def update(self, battle_populations: Dict[str, Population]):
        self.overview_plotter.update(
            Population(
                [
                    individual
                    for _, battle_population in battle_populations.items()
                    for individual in battle_population.individuals
                ]
            )
        )
        for battle_id, battle_population in battle_populations.items():
            self.battle_plotters[battle_id].update(battle_population)

    def create_plot(self):
        html = "<h1>Table of Contents</h1><ul>"
        html += f"<li><a href='#overview'>All Battles</a></li>"
        for battle_id, plotter in self.battle_plotters.items():
            html += f"<li><a href='#{battle_id}'>{battle_id}</a></li>"
        html += "</ul>"

        html += f"<h2 id='overview'>All Battles</h2>"
        html += self.overview_plotter.create_plot()
        for battle_id, plotter in self.battle_plotters.items():
            html += f"<h2 id='{battle_id}'>{battle_id}</h2>"
            html += plotter.create_plot()
            html += f"<a href='#overview'>Back to top</a>"
        return html

    def save_html(self, filename: str):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.create_plot())


def run_balance_overview():
    """
    Runs evolutionary generations for every battle in the game and analyzes unit usage patterns.
    Each loop evolves the same populations further, showing how solutions improve over time.
    """
    print(f"Running balance overview with {multiprocessing.cpu_count()} cores")
    print("Starting balance overview analysis...")

    PARENTS_PER_GENERATION = 30
    CHILDREN_PER_GENERATION = 10
    MUTATION_ADAPTATION_RATE = 0.1
    CATEGORY_CAP = 5
    TOURNAMENT_SIZE = None
    MINIMUM_POINTS = 600
    USE_POWERS = True

    # Setup evolution strategy with the same parameters as the main script
    evolution = EvolutionStrategy(
        mutations=[
            RemoveRandomUnit(),
            PerturbPosition(noise_scale=10),
            PerturbPosition(noise_scale=100),
            RandomizeUnitPosition(),
            ReplaceSubarmy(),
            RandomizeUnitType(),
            MoveNextToAlly(noise_scale=20),
        ],
        selector=TournamentSelection(tournament_size=TOURNAMENT_SIZE) if TOURNAMENT_SIZE is not None else UniformSelection(),
        parents_per_generation=PARENTS_PER_GENERATION,
        children_per_generation=CHILDREN_PER_GENERATION,
        mutation_adaptation_rate=MUTATION_ADAPTATION_RATE,
        category_cap=CATEGORY_CAP if CATEGORY_CAP is not None else PARENTS_PER_GENERATION,
        n_mutations=1,
        use_powers=USE_POWERS,
    )
    # Get all non-test battles
    battles = [b for b in get_battles() if not b.is_test and sum(unit_values[unit_type] for unit_type, _ in b.enemies) >= MINIMUM_POINTS]
    print(f"Initializing populations for {len(battles)} non-test battles")
    
    # Initialize populations for all battles
    battle_populations: Dict[str, Population] = {}
    for battle in battles:
        # Set the target cost based on the battle's grades
        target_cost = 900  # Default target cost
        if battle.grades is not None:
            # Use the D cutoff as the target cost
            target_cost = battle.grades.d_cutoff
        
        # Create initial population
        population = random_population(battle_id=battle.id, size=PARENTS_PER_GENERATION, target_cost=target_cost)
        
        # Evaluate the initial population
        population.evaluate()
        
        # Store the population for this battle
        battle_populations[battle.id] = population
        print(f"Initialized population for {battle.id}")
    

    all_battles_plotter = AllBattlesPlotter(
        overview_plotter=PlotGroup(
            plotters=[
                UnitCountsPlotter(),
                UnitValuesPlotter(),
                GradeDistributionPlotter(),
            ],
        ),
        battle_plotters={
            battle.id: PlotGroup(
                plotters=[
                    UnitCountsPlotter(),
                    GradeDistributionPlotter(),
                ],
            )
            for battle in battles
        }
    )
    all_battles_plotter.update(battle_populations)
    
    generation = 0
    
    while True:
        print(f"\n----- GENERATION {generation} -----\n")
        
        # Track unit usage across all battles
        best_solution_unit_counts = Counter()
        all_battles_unit_counts = Counter()
        
        # Track grades for best solutions
        grade_distribution = Counter()
        
        # Process each battle
        for battle_id, population in battle_populations.items():
            battle = get_battle_id(battle_id)
            
            print(f"Processing battle: {battle_id}")
            
            # Get the best individual for this battle
            if population.best_individuals:
                best_individual = population.best_individuals[0]
                
                # Count units in best solution
                for unit_type, _ in best_individual.unit_placements:
                    best_solution_unit_counts[unit_type] += 1
                
                # Grade the solution
                points_used = best_individual.points
                grade = best_individual.fitness.grade
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
        for battle_id, population in battle_populations.items():
            print(f"Evolving population for {battle_id}")
            battle_populations[battle_id] = evolution(population)
        
        generation += 1

        all_battles_plotter.update(battle_populations)
        all_battles_plotter.save_html("plots/balance_overview.html")

if __name__ == "__main__":
    run_balance_overview()
