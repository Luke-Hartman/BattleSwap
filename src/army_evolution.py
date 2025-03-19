from typing import List, Dict, Tuple
import random
from collections import Counter, defaultdict
import numpy as np
import multiprocessing
from battle_solver import (
    ALLOWED_UNIT_TYPES, Individual, Population, Mutation, RandomizeUnitPosition,
    PerturbPosition, MoveNextToAlly, RandomizeUnitType, ReplaceSubarmy, generate_random_army, Plotter, PlotGroup,
    UnitCountsPlotter, UnitValuesPlotter, get_process_pool, cleanup_process_pool
)
from auto_battle import BattleOutcome, simulate_battle_with_dependencies
from components.team import TeamType
from components.unit_type import UnitType
from unit_values import unit_values

class EloIndividual(Individual):
    def __init__(self, unit_placements: List[Tuple[UnitType, Tuple[int, int]]], elo: float = 1000.0):
        super().__init__("army_evolution", unit_placements)
        self.elo = elo
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.matches_played = 0

    def __str__(self) -> str:
        return f"{super().__str__()} (ELO: {self.elo:.1f}, W/L/D: {self.wins}/{self.losses}/{self.draws}, Matches: {self.matches_played})"

class EloPopulation:
    def __init__(self, individuals: List[EloIndividual]):
        self.individuals = individuals

    def get_median_elo(self) -> float:
        return np.median([ind.elo for ind in self.individuals])

    def get_best_individuals(self, n: int = 1) -> List[EloIndividual]:
        return sorted(self.individuals, key=lambda x: x.elo, reverse=True)[:n]

    def get_worst_individuals(self, n: int = 1) -> List[EloIndividual]:
        return sorted(self.individuals, key=lambda x: x.elo)[:n]

def _simulate_match(args: Tuple[Tuple[int, EloIndividual], Tuple[int, EloIndividual]]) -> Tuple[int, int, BattleOutcome]:
    (idx1, player1), (idx2, player2) = args
    outcome = simulate_battle_with_dependencies(
        ally_placements=player1.unit_placements,
        enemy_placements=player2.unit_placements,
        max_duration=120.0,
    )
    return idx1, idx2, outcome

class EloEvolution:
    def __init__(
        self,
        parents_per_generation: int,
        children_per_generation: int,
        matches_per_generation: int,
        mutations: List[Mutation],
        k_factor: float = 32.0,
        tournament_size: int = 1,
    ):
        self.parents_per_generation = parents_per_generation
        self.children_per_generation = children_per_generation
        self.matches_per_generation = matches_per_generation
        self.mutations = mutations
        self.k_factor = k_factor
        self.tournament_size = tournament_size
        self.plotter = PlotGroup(
            plotters=[
                UnitCountsPlotter(),
                UnitValuesPlotter(),
            ],
        )

    def _update_elo(self, player1: EloIndividual, player2: EloIndividual, outcome: BattleOutcome):
        # Calculate expected scores
        expected1 = 1 / (1 + 10 ** ((player2.elo - player1.elo) / 400))
        expected2 = 1 - expected1

        # Calculate actual scores
        if outcome == BattleOutcome.TEAM1_VICTORY:
            actual1, actual2 = 1.0, 0.0
            player1.wins += 1
            player2.losses += 1
        elif outcome == BattleOutcome.TEAM2_VICTORY:
            actual1, actual2 = 0.0, 1.0
            player1.losses += 1
            player2.wins += 1
        else:  # TIMEOUT
            actual1, actual2 = 0.5, 0.5
            player1.draws += 1
            player2.draws += 1

        # Update ELO ratings
        player1.elo += self.k_factor * (actual1 - expected1)
        player2.elo += self.k_factor * (actual2 - expected2)
        
        # Update matches played
        player1.matches_played += 1
        player2.matches_played += 1

    def _create_new_individual(self, parent: EloIndividual, median_elo: float) -> EloIndividual:
        # Start with a copy of the parent's unit placements
        unit_placements = list(parent.unit_placements)
        
        # Apply random mutations to create variety
        mutation = random.choice(self.mutations)
        # Create a temporary individual to apply the mutation
        temp_ind = EloIndividual(unit_placements)
        mutated_ind = mutation(temp_ind)
        unit_placements = mutated_ind.unit_placements
            
        return EloIndividual(unit_placements, elo=1000.0)

    def _select_parents(self, population: EloPopulation) -> List[EloIndividual]:
        parents = []
        while len(parents) < self.children_per_generation:
            competitors = random.choices(population.individuals, k=self.tournament_size)
            parents.append(max(competitors, key=lambda x: x.elo))
        return parents

    def __call__(self, population: EloPopulation) -> EloPopulation:
        # 1. Generate new individuals
        parents = self._select_parents(population)
        median_elo = population.get_median_elo()
        new_individuals = [self._create_new_individual(parent, median_elo) for parent in parents]
        
        # 2. Do battles between new and existing individuals
        # Generate random pairs of new and existing individuals
        new_indices = random.choices(range(len(new_individuals)), k=self.matches_per_generation)
        existing_indices = random.choices(range(len(population.individuals)), k=self.matches_per_generation)
        match_pairs = [
            ((new_idx, new_individuals[new_idx]), (existing_idx, population.individuals[existing_idx]))
            for new_idx, existing_idx in zip(new_indices, existing_indices)
        ]

        # Simulate matches in parallel
        if len(match_pairs) > 1:
            pool = get_process_pool()
            results = pool.map(_simulate_match, match_pairs)
        else:
            results = [_simulate_match(match_pair) for match_pair in match_pairs]

        # Update ELO ratings based on match results
        for new_idx, existing_idx, outcome in results:
            self._update_elo(new_individuals[new_idx], population.individuals[existing_idx], outcome)

        # 3. Keep the best self.parents_per_generation individuals
        # Combine existing and new individuals
        all_individuals = population.individuals + new_individuals
        # Sort by ELO and keep the best
        population.individuals = sorted(all_individuals, key=lambda x: x.elo, reverse=True)[:self.parents_per_generation]

        # Update plots
        self.plotter.update(population)
        self.plotter.save_plot("plots/army_evolution.html")

        return population

def run_army_evolution(
    parents_per_generation: int = 100,
    children_per_generation: int = 1,
    matches_per_generation: int = 30,
    target_cost: int = 200,
    tournament_size: int = 3,
):
    """
    Run the army evolution algorithm.
    
    Args:
        parents_per_generation: Number of individuals to keep each generation
        children_per_generation: Number of new individuals to create each generation
        matches_per_generation: Number of random matches to simulate each generation
        target_cost: Target cost for each army
        tournament_size: Number of competitors to compete in each tournament
    """
    print(f"Running army evolution with {multiprocessing.cpu_count()} cores")
    
    # Initialize population
    population = EloPopulation([
        EloIndividual(generate_random_army(target_cost, max_decrease=0))
        for _ in range(parents_per_generation)
    ])

    # Create evolution strategy
    evolution = EloEvolution(
        parents_per_generation=parents_per_generation,
        children_per_generation=children_per_generation,
        matches_per_generation=matches_per_generation,
        tournament_size=tournament_size,
        mutations=[
            RandomizeUnitPosition(),
            PerturbPosition(noise_scale=10),
            PerturbPosition(noise_scale=100),
            RandomizeUnitType(max_decrease=0),
            MoveNextToAlly(noise_scale=20),
            ReplaceSubarmy(max_decrease=0),
            ReplaceSubarmy(max_decrease=0),
            ReplaceSubarmy(max_decrease=0),
            ReplaceSubarmy(max_decrease=0),
        ],
    )

    try:
        # Run generations
        generation = 0
        while True:
            print(f"\nGeneration {generation + 1}")
            print(f"Best ELO: {population.get_best_individuals(1)[0].elo:.1f}")
            print(f"Median ELO: {population.get_median_elo():.1f}")
            print(f"Worst ELO: {population.get_worst_individuals(1)[0].elo:.1f}")
            print("\nTop 3 armies:")
            for i, ind in enumerate(population.get_best_individuals(3), 1):
                print(f"{i}. {ind}")

            print("\nBottom 3 armies:")
            for i, ind in enumerate(population.get_worst_individuals(3), 1):
                print(f"{i}. {ind}")

            population = evolution(population)
            generation += 1
    finally:
        cleanup_process_pool()

if __name__ == "__main__":
    run_army_evolution() 