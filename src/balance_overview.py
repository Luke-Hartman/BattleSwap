from collections import Counter
import multiprocessing
import os
from typing import Dict

from battles import get_battle_id, get_battles
from battle_solver import (
    ALLOWED_UNIT_TYPES, EvolutionStrategy, AddRandomUnit, MoveNextToAlly, PlotGroup, Plotter, Population, RemoveRandomUnit, 
    PerturbPosition, RandomizeUnitPosition, RandomizeUnitType, ReplaceSubarmy, TournamentSelection, UniformSelection, UnitCountsPlotter, UnitValuesPlotter, 
    ItemCountsPlotter, ItemValuesPlotter, SpellCountsPlotter, SpellValuesPlotter, 
    RandomizeSpellPosition, PerturbSpellPosition, AddRandomSpell, RemoveRandomSpell, random_population
)
from point_values import unit_values

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
            RandomizeSpellPosition(),
            PerturbSpellPosition(noise_scale=10),
            PerturbSpellPosition(noise_scale=100),
            AddRandomSpell(),
            RemoveRandomSpell(),
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
    battles = [b for b in get_battles() if not b.is_test and sum(unit_values[unit_type] for unit_type, _, _ in b.enemies) >= MINIMUM_POINTS]
    print(f"Initializing populations for {len(battles)} non-test battles")
    
    # Initialize populations for all battles
    battle_populations: Dict[str, Population] = {}
    for battle in battles:
        # Create initial population
        population = random_population(battle_id=battle.id, size=PARENTS_PER_GENERATION)
        
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
                ItemCountsPlotter(),
                ItemValuesPlotter(),
                SpellCountsPlotter(),
                SpellValuesPlotter(),
            ],
        ),
        battle_plotters={
            battle.id: PlotGroup(
                plotters=[
                    UnitCountsPlotter(),
                    ItemCountsPlotter(),
                    SpellCountsPlotter(),
                ],
            )
            for battle in battles
        }
    )
    all_battles_plotter.update(battle_populations)
    
    generation = 0
    
    while True:
        print(f"\n----- GENERATION {generation} -----\n")
        
        # Track unit, item, and spell usage across all battles
        best_solution_unit_counts = Counter()
        best_solution_item_counts = Counter()
        best_solution_spell_counts = Counter()
        all_battles_unit_counts = Counter()
        all_battles_item_counts = Counter()
        all_battles_spell_counts = Counter()
        

        
        # Process each battle
        for battle_id, population in battle_populations.items():
            battle = get_battle_id(battle_id)
            
            print(f"Processing battle: {battle_id}")
            
            # Get the best individual for this battle
            if population.best_individuals:
                best_individual = population.best_individuals[0]
                
                # Count units, items, and spells in best solution
                for unit_type, _, items in best_individual.unit_placements:
                    best_solution_unit_counts[unit_type] += 1
                    for item_type in items:
                        best_solution_item_counts[item_type] += 1
                
                for spell_type, _, _ in best_individual.spell_placements:
                    best_solution_spell_counts[spell_type] += 1
                
                # Get solution points
                points_used = best_individual.points
                
                print(f"  Best solution: {best_individual}")
                print(f"  Points: {points_used}")
            else:
                print("  No solution found")

            # Count all units, items, and spells used in this battle's enemy placements
            for unit_type, _, items in battle.enemies:
                all_battles_unit_counts[unit_type] += 1
                for item_type in items:
                    all_battles_item_counts[item_type] += 1
            
            # Count spells if they exist in the battle
            if battle.spells:
                for spell_type, _, _ in battle.spells:
                    all_battles_spell_counts[spell_type] += 1
        
        # Report findings
        print("\n----- UNIT USAGE ANALYSIS -----")
        print(f"{'Unit Type':<20} {'Best Solutions':<15} {'All Battles':<15}")
        print("-" * 50)
        
        # Sort by most used to least used in best solutions
        for unit_type in sorted(ALLOWED_UNIT_TYPES, key=lambda x: best_solution_unit_counts.get(x, 0), reverse=True):
            all_count = all_battles_unit_counts.get(unit_type, 0)
            print(f"{unit_type.name:<20} {best_solution_unit_counts.get(unit_type, 0):<15} {all_count:<15}")
        
        # Report item usage
        from battle_solver import ALLOWED_ITEM_TYPES
        print("\n----- ITEM USAGE ANALYSIS -----")
        print(f"{'Item Type':<20} {'Best Solutions':<15} {'All Battles':<15}")
        print("-" * 50)
        
        for item_type in sorted(ALLOWED_ITEM_TYPES, key=lambda x: best_solution_item_counts.get(x, 0), reverse=True):
            all_count = all_battles_item_counts.get(item_type, 0)
            print(f"{item_type.name:<20} {best_solution_item_counts.get(item_type, 0):<15} {all_count:<15}")
        
        # Report spell usage
        from battle_solver import ALLOWED_SPELL_TYPES
        print("\n----- SPELL USAGE ANALYSIS -----")
        print(f"{'Spell Type':<20} {'Best Solutions':<15} {'All Battles':<15}")
        print("-" * 50)
        
        for spell_type in sorted(ALLOWED_SPELL_TYPES, key=lambda x: best_solution_spell_counts.get(x, 0), reverse=True):
            all_count = all_battles_spell_counts.get(spell_type, 0)
            print(f"{spell_type.name:<20} {best_solution_spell_counts.get(spell_type, 0):<15} {all_count:<15}")
        


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
