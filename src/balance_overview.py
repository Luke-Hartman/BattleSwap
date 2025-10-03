from collections import Counter
import multiprocessing
import os
from typing import Dict, List, Tuple

from battles import get_battle_id, get_battles
from battle_solver import (
    ALLOWED_UNIT_TYPES, EvolutionStrategy, AddRandomUnit, MoveNextToAlly, PlotGroup, Plotter, Population, RemoveRandomUnit, 
    PerturbPosition, RandomizeUnitPosition, RandomizeUnitType, ReplaceSubarmy, TournamentSelection, UniformSelection,
    AllCountsPlotter, AllValuesPlotter,
    RandomizeSpellPosition, PerturbSpellPosition, AddRandomSpell, RemoveRandomSpell, RemoveRandomItem, random_population, Individual
)
from point_values import unit_values
from components.unit_type import UnitType
from entities.items import ItemType
from components.spell_type import SpellType


def create_detailed_solution_description(individual: Individual) -> str:
    """
    Create a detailed description of a solution showing units with their items and spells used.
    Aggregates multiple units of the same type with the same items.
    """
    # Group units by type and items
    unit_groups: Dict[Tuple[UnitType, Tuple[ItemType, ...]], int] = {}
    
    for unit_type, _, items in individual.unit_placements:
        # Sort items for consistent grouping
        items_tuple = tuple(sorted(items))
        key = (unit_type, items_tuple)
        unit_groups[key] = unit_groups.get(key, 0) + 1
    
    # Create unit descriptions
    unit_descriptions = []
    for (unit_type, items_tuple), count in sorted(unit_groups.items(), key=lambda x: (x[0][0].name, x[1])):
        if items_tuple:
            items_str = " with " + ", ".join(item.value.replace("_", " ").title() for item in items_tuple)
        else:
            items_str = ""
        
        if count > 1:
            unit_descriptions.append(f"{count} {unit_type.value.replace('_', ' ').title()}{items_str}")
        else:
            unit_descriptions.append(f"{unit_type.value.replace('_', ' ').title()}{items_str}")
    
    # Create spell descriptions
    spell_descriptions = []
    if individual.spell_placements:
        spell_counts = Counter(spell_type for spell_type, _, _ in individual.spell_placements)
        for spell_type, count in sorted(spell_counts.items(), key=lambda x: x[0].name):
            if count > 1:
                spell_descriptions.append(f"{count} {spell_type.value.replace('_', ' ').title()}")
            else:
                spell_descriptions.append(spell_type.value.replace('_', ' ').title())
    
    # Combine descriptions
    parts = []
    if unit_descriptions:
        parts.append(", ".join(unit_descriptions))
    if spell_descriptions:
        parts.append("Spells: " + ", ".join(spell_descriptions))
    
    return " | ".join(parts)


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
            RemoveRandomSpell(),
            RemoveRandomItem(),
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
    # battles = [get_battle_id("Behold the Wizard's Power!")]
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
                AllCountsPlotter(),
                AllValuesPlotter(),
            ],
        ),
        battle_plotters={
            battle.id: AllCountsPlotter()
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
                
                # Create detailed solution description
                solution_description = create_detailed_solution_description(best_individual)
                print(f"  Best solution: {solution_description}")
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
