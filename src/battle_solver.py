from abc import ABC, abstractmethod
import random
from typing import Dict, List, Tuple
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
from scene_utils import get_legal_placement_area
from unit_values import unit_values

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
#     UnitType.CRUSADER_COMMANDER,
#     UnitType.CRUSADER_DEFENDER,
#     UnitType.CRUSADER_GOLD_KNIGHT,
#     UnitType.CRUSADER_LONGBOWMAN,
#     UnitType.CRUSADER_PALADIN,
#     UnitType.CRUSADER_PIKEMAN,
#     UnitType.ZOMBIE_TANK,
# ]
ALLOWED_UNIT_TYPES = [
    UnitType.CORE_ARCHER,
    UnitType.CORE_CAVALRY,
    UnitType.CORE_DUELIST,
    UnitType.CORE_SWORDSMAN,
    UnitType.CORE_WIZARD,
    UnitType.CRUSADER_BANNER_BEARER,
    UnitType.CRUSADER_BLACK_KNIGHT,
    UnitType.CRUSADER_CATAPULT,
    UnitType.CRUSADER_CLERIC,
    UnitType.CRUSADER_CROSSBOWMAN,
    UnitType.CRUSADER_DEFENDER,
    UnitType.CRUSADER_GOLD_KNIGHT,
    UnitType.CRUSADER_GUARDIAN_ANGEL,
    UnitType.CRUSADER_LONGBOWMAN,
    UnitType.CRUSADER_PALADIN,
    UnitType.CRUSADER_PIKEMAN,
    UnitType.CRUSADER_SOLDIER,
    UnitType.ZOMBIE_JUMPER,
    UnitType.ZOMBIE_SPITTER,
    UnitType.ZOMBIE_TANK,
]

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
    def __init__(self, unit_placements: List[Tuple[UnitType, Tuple[int, int]]]):
        self.unit_placements = sorted(unit_placements)
        self._fitness = None
    
    @property
    def points(self) -> float:
        return sum(unit_values[unit_type] for unit_type, _ in self.unit_placements)
    
    def __str__(self) -> str:
        counts = Counter(unit_type for unit_type, _ in self.unit_placements)
        return ", ".join(f"{count} {unit_type}" for unit_type, count in counts.items())

    @property
    def fitness(self) -> Fitness:
        if self._fitness is None:
            raise ValueError("Fitness not evaluated")
        return self._fitness

    def short_str(self) -> str:
        return ", ".join(f"{count} {unit_type}" for unit_type, count in sorted(Counter(unit_type for unit_type, _ in self.unit_placements).items()))
    
    def _evaluate(
        self,
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        max_duration: float,
    ) -> Fitness:
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
            post_battle_callback=lambda outcome: Fitness(
                outcome=outcome,
                points=self.points,
                team1_health=_get_team_health(TeamType.TEAM1),
                team2_health=_get_team_health(TeamType.TEAM2)
            )
        )
        self._fitness = fitness_result
        return fitness_result

    def evaluate(
        self,
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        max_duration: float = 120.0
    ) -> Fitness:
        if self._fitness is None:
            self._fitness = self._evaluate(enemy_placements, max_duration)
        return self._fitness

    def __str__(self) -> str:
        return self.short_str()

    def __eq__(self, other: 'Individual') -> bool:
        return self.unit_placements == other.unit_placements
    
    def __hash__(self) -> int:
        return hash(tuple(self.unit_placements))

def _evaluate(individual: Individual, enemy_placements: List[Tuple[UnitType, Tuple[int, int]]], max_duration: float):
    return individual.evaluate(enemy_placements, max_duration)

class Population:
    def __init__(self, individuals: List[Individual]):
        self.individuals = individuals

    def evaluate(self, enemy_placements: List[Tuple[UnitType, Tuple[int, int]]], max_duration: float = 120.0):
        num_jobs = min(len(self.individuals), multiprocessing.cpu_count())
        with multiprocessing.Pool(processes=num_jobs) as pool:
            # Use starmap to evaluate each individual and collect their fitness
            results = pool.starmap(_evaluate, [(ind, enemy_placements, max_duration) for ind in self.individuals])

        # Update the fitness for each individual in the main process
        for ind, fitness in zip(self.individuals, results):
            ind._fitness = fitness

    @property
    def best_individuals(self) -> List[Individual]:
        best_score = max(ind.fitness for ind in self.individuals).points
        best_individuals = []
        short_strs = set()
        for individual in self.individuals:
            if individual.fitness.outcome == BattleOutcome.TEAM1_VICTORY and individual.fitness.points == best_score and individual.short_str() not in short_strs:
                best_individuals.append(individual)
                short_strs.add(individual.short_str())
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
        return str

def _get_random_legal_position(team_type: TeamType) -> Tuple[float, float]:
    """Generate a random position within the legal placement area.
    
    Args:
        team_type: The team type to get legal area for.
        
    Returns:
        A tuple of (x, y) coordinates within the legal area.
    """
    # Get the legal placement area for the team
    legal_area = get_legal_placement_area(
        battle_id="unused",
        hex_coords=(0, 0),
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

def generate_random_army(target_cost: int) -> List[Tuple[UnitType, Tuple[int, int]]]:
    current_cost = 0
    unit_placements = []
    while current_cost != target_cost:
        if current_cost > target_cost:
            delete_index = random.randint(0, len(unit_placements) - 1)
            current_cost -= unit_values[unit_placements[delete_index][0]]
            unit_placements = unit_placements[:delete_index] + unit_placements[delete_index + 1:]
        else:
            unit_type = _get_random_legal_unit_type()
            unit_placements.append((unit_type, _get_random_legal_position(TeamType.TEAM1)))
            current_cost += unit_values[unit_type]
    return unit_placements

class Mutation(ABC):

    @abstractmethod
    def __call__(self, individual: Individual) -> Individual:
        pass

class AddRandomUnit(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        new_unit = _get_random_legal_unit_type()
        new_position = _get_random_legal_position(TeamType.TEAM1)
        index = random.randint(0, len(individual.unit_placements))
        new_unit_placements = individual.unit_placements[:index] + [(new_unit, new_position)] + individual.unit_placements[index:]
        return Individual(new_unit_placements)

class RemoveRandomUnit(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        index = random.randint(0, len(individual.unit_placements) - 1)
        new_unit_placements = individual.unit_placements[:index] + individual.unit_placements[index + 1:]
        if len(new_unit_placements) == 0:
            return Individual([(_get_random_legal_unit_type(), _get_random_legal_position(TeamType.TEAM1))])
        return Individual(new_unit_placements)

class RandomizeUnitPosition(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        new_position = _get_random_legal_position(TeamType.TEAM1)
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        new_unit_placements = individual.unit_placements[:index] + [(unit_to_mutate[0], new_position)] + individual.unit_placements[index + 1:]
        return Individual(new_unit_placements)

class RandomizeUnitType(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        new_unit = _get_random_legal_unit_type()
        while new_unit == unit_to_mutate[0] or unit_values[new_unit] > unit_values[unit_to_mutate[0]]:
            new_unit = _get_random_legal_unit_type()
        new_unit_placements = individual.unit_placements[:index] + [(new_unit, unit_to_mutate[1])] + individual.unit_placements[index + 1:]
        return Individual(new_unit_placements)

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
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        new_position = (unit_to_mutate[1][0] + random.gauss(0, self.noise_scale), unit_to_mutate[1][1] + random.gauss(0, self.noise_scale))
        new_unit_placements = individual.unit_placements[:index] + [(unit_to_mutate[0], new_position)] + individual.unit_placements[index + 1:]
        return Individual(new_unit_placements)


class ReplaceSubarmy(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        original_score = individual.points
        kept_unit_placements = list(individual.unit_placements)
        random.shuffle(kept_unit_placements)
        index = random.randint(0, len(kept_unit_placements) - 1)
        kept_unit_placements = kept_unit_placements[:index]
        new_score = sum(unit_values[unit_type] for unit_type, _ in kept_unit_placements)

        new_subarmy = generate_random_army(original_score - new_score)
        return Individual(kept_unit_placements + new_subarmy)


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
            return Individual(left_unit_placements), Individual(right_unit_placements)


class RandomMixCrossover(Crossover):

    def __call__(self, individual1: Individual, individual2: Individual) -> Tuple[Individual, Individual]:
        while True:
            new_unit_placements1 = []
            new_unit_placements2 = []
            for unit_type, position in individual1.unit_placements:
                if random.random() < 0.5:
                    new_unit_placements1.append((unit_type, position))  
                else:
                    new_unit_placements2.append((unit_type, position))
            for unit_type, position in individual2.unit_placements:
                if random.random() < 0.5:
                    new_unit_placements1.append((unit_type, position))
                else:
                    new_unit_placements2.append((unit_type, position))
            if not new_unit_placements1 or not new_unit_placements2:
                continue
            return Individual(new_unit_placements1), Individual(new_unit_placements2)


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
        parents_per_generation: int,
        children_per_generation: int,
        mutation_adaptation_rate: float = 0.1,
        category_cap: int = 3,
    ):
        self.mutations = mutations
        self.parents_per_generation = parents_per_generation
        self.children_per_generation = children_per_generation
        self.mutation_rates = {
            mutation: 1/len(mutations)
            for mutation in mutations
        }
        self.mutation_adaptation_rate = mutation_adaptation_rate
        self.category_cap = category_cap
    def __call__(self, population: Population, enemy_placements: List[Tuple[UnitType, Tuple[int, int]]]) -> Population:
        parents = population.individuals

        # Generate children
        next_generation = set(parents)
        mutation_pairs = []
        while len(next_generation) < self.children_per_generation + self.parents_per_generation:
            parent = random.choice(parents)
            mutation = random.choices(list(self.mutation_rates.keys()), weights=list(self.mutation_rates.values()))[0]
            child = mutation(parent)
            if child not in next_generation:
                mutation_pairs.append((mutation, parent, child))
                next_generation.add(child)

        # Evaluate parents + children
        parents_and_children = Population(list(next_generation))
        parents_and_children.evaluate(enemy_placements)

        # Select the next generation
        individuals = []
        category_counts = defaultdict(int)
        for individual in sorted(parents_and_children.individuals, key=lambda x: x.fitness, reverse=True):
            category = tuple(sorted(Counter(
                unit_type for unit_type, _ in individual.unit_placements
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

def random_population(
    size: int,
    target_cost: int,
) -> Population:
    return Population([
        Individual(generate_random_army(target_cost))
        for _ in range(size)
    ])

def main():
    enemy_placements = get_battle_id("A Balanced Army").enemies
    population = random_population(size=3, target_cost=900)
    population.evaluate(enemy_placements)
    evolution = EvolutionStrategy(
        mutations=[
            RemoveRandomUnit(),
            PerturbPosition(noise_scale=10),
            PerturbPosition(noise_scale=100),
            RandomizeUnitPosition(),
            ReplaceSubarmy(),
            RandomizeUnitType(),
        ],
        parents_per_generation=3,
        children_per_generation=10,
        mutation_adaptation_rate=0.1,
    )
    generation = 0
    while True:
        print(f"Generation {generation}")
        #population.evaluate(enemy_placements)
        print(population)
        population = evolution(population, enemy_placements)
        print(evolution.mutation_rates)
        generation += 1

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
