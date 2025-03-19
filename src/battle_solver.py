from abc import ABC, abstractmethod
import math
import random
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
from functools import total_ordering
import esper
import shapely
from auto_battle import BattleOutcome, simulate_battle_with_dependencies
from battles import BattleGrades, get_battle_id
from components.health import Health
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType
from scene_utils import get_legal_placement_area
from unit_values import unit_values
from game_constants import get_game_constants_hash
import plotly.graph_objects as go
from pathlib import Path
import os

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
    UnitType.CORE_BARBARIAN,
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

def grade_solution(outcome: BattleOutcome, points_used: int, battle_grades: BattleGrades) -> str:
    """Grade a solution based on points used."""
    if outcome != BattleOutcome.TEAM1_VICTORY:
        return "Failed"

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

@total_ordering
class Fitness:

    def __init__(self, outcome: BattleOutcome, points: float, team1_health: float, team2_health: float, grade: str):
        self.outcome = outcome
        self.points = points
        self.team1_health = team1_health
        self.team2_health = team2_health
        self.grade = grade

    def __str__(self) -> str:
        return f"Outcome: {self.outcome}, Points: {self.points} ({self.grade}), Team 1 Health: {self.team1_health}, Team 2 Health: {self.team2_health}"

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
    def __init__(self, battle_id: str, unit_placements: List[Tuple[UnitType, Tuple[int, int]]]):
        self.battle_id = battle_id
        self.unit_placements = sorted(unit_placements)
        self._fitness = None
    
    @property
    def points(self) -> float:
        return sum(unit_values[unit_type] for unit_type, _ in self.unit_placements)
    
    def __str__(self) -> str:
        counts = Counter(unit_type for unit_type, _ in self.unit_placements)
        return ", ".join(f"{count} {unit_type}" for unit_type, count in counts.items())
    
    def needs_evaluation(self) -> bool:
        return self._fitness is None

    @property
    def fitness(self) -> Fitness:
        if self._fitness is None:
            raise ValueError("Fitness not evaluated")
        return self._fitness

    def short_str(self) -> str:
        return ", ".join(f"{count} {unit_type}" for unit_type, count in sorted(Counter(unit_type for unit_type, _ in self.unit_placements).items()))
    
    def evaluate(
        self,
        max_duration: float,
    ) -> Fitness:
        battle = get_battle_id(self.battle_id)
        enemy_placements = battle.enemies
        grades = battle.grades
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
                team2_health=_get_team_health(TeamType.TEAM2),
                grade=grade_solution(outcome, self.points, grades),
            )
        )
        self._fitness = fitness_result
        return fitness_result

    def __str__(self) -> str:
        return self.short_str()

    def __eq__(self, other: 'Individual') -> bool:
        return self.unit_placements == other.unit_placements
    
    def __hash__(self) -> int:
        return hash(tuple(self.unit_placements))

def _evaluate(individual: Individual, max_duration: float):
    return individual.evaluate(max_duration)

# Add this at the module level
_global_process_pool = None

def get_process_pool(num_processes=None):
    """Get or create the global process pool."""
    global _global_process_pool
    if _global_process_pool is None:
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()
        _global_process_pool = multiprocessing.Pool(processes=num_processes)
    return _global_process_pool

def cleanup_process_pool():
    """Clean up the global process pool when the program exits."""
    global _global_process_pool
    if _global_process_pool is not None:
        _global_process_pool.close()
        _global_process_pool.join()
        _global_process_pool = None

class Population:
    def __init__(self, individuals: List[Individual]):
        self.individuals = individuals

    def evaluate(self, max_duration: float = 120.0):
        game_constants_hash = get_game_constants_hash()
        game_constants_hash_changed = False
        individuals_to_evaluate = []
        for ind in self.individuals:
            if ind.needs_evaluation():
                individuals_to_evaluate.append(ind)
            elif getattr(ind, "_constants_hash", game_constants_hash) != game_constants_hash:
                individuals_to_evaluate.append(ind)
                game_constants_hash_changed = True

        if game_constants_hash_changed:
            print(f"Game constants hash changed to {game_constants_hash}")
            cleanup_process_pool()

        if not individuals_to_evaluate:
            return
        
        if len(individuals_to_evaluate) > 1:
            pool = get_process_pool()
            results = pool.starmap(_evaluate, [(ind, max_duration) for ind in individuals_to_evaluate])
            
            # Update the fitness for each individual in the main process
            for ind, fitness in zip(individuals_to_evaluate, results):
                ind._fitness = fitness
                ind._constants_hash = game_constants_hash
        else:
            # For a single individual, avoid the overhead of using the pool
            for ind in individuals_to_evaluate:
                ind._fitness = ind.evaluate(max_duration)
                ind._constants_hash = game_constants_hash
    @property
    def best_individuals(self) -> List[Individual]:
        best_score = max(ind.fitness for ind in self.individuals).points
        best_individuals = []
        short_strs = set()
        for individual in self.individuals:
            if individual.fitness.outcome == BattleOutcome.TEAM1_VICTORY and individual.fitness.points == best_score and individual.short_str() not in short_strs:
                best_individuals.append(individual)
                short_strs.add(individual.short_str())
        if not best_individuals:
            return [max(self.individuals, key=lambda x: x.fitness)]
        else:
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

        str += f"Number of each unit type in population:\n"
        population_counts = Counter(unit_type for ind in self.individuals for unit_type, _ in ind.unit_placements)
        for unit_type, count in sorted(population_counts.items(), key=lambda x: x[1], reverse=True):
            str += f"\t{unit_type:<20}: {count:<5}\n"
        
        str += f"Number of each unit type in best individuals:\n"
        best_population_counts = Counter(unit_type for ind in self.best_individuals for unit_type, _ in ind.unit_placements)
        for unit_type, count in sorted(best_population_counts.items(), key=lambda x: x[1], reverse=True):
            str += f"\t{unit_type:<20}: {count:<5}\n"
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

def generate_random_army(target_cost: int, max_decrease: int = 100) -> List[Tuple[UnitType, Tuple[int, int]]]:
    current_cost = 0
    unit_placements = []
    while not (target_cost - max_decrease <= current_cost <= target_cost):
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
        return Individual(individual.battle_id, new_unit_placements)

class RemoveRandomUnit(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        if len(individual.unit_placements) == 0:
            return individual
        index = random.randint(0, len(individual.unit_placements) - 1)
        new_unit_placements = individual.unit_placements[:index] + individual.unit_placements[index + 1:]
        if len(new_unit_placements) == 0:
            return Individual(individual.battle_id, [(_get_random_legal_unit_type(), _get_random_legal_position(TeamType.TEAM1))])
        return Individual(individual.battle_id, new_unit_placements)

class RandomizeUnitPosition(Mutation):

    def __call__(self, individual: Individual) -> Individual:
        new_position = _get_random_legal_position(TeamType.TEAM1)
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        new_unit_placements = individual.unit_placements[:index] + [(unit_to_mutate[0], new_position)] + individual.unit_placements[index + 1:]
        return Individual(individual.battle_id, new_unit_placements)

class RandomizeUnitType(Mutation):

    def __init__(self, max_decrease: int = 100):
        self.max_decrease = max_decrease

    def __call__(self, individual: Individual) -> Individual:
        index = random.randint(0, len(individual.unit_placements) - 1)
        unit_to_mutate = individual.unit_placements[index]
        current_value = unit_values[unit_to_mutate[0]]
        legal_options = [
            unit_type
            for unit_type in ALLOWED_UNIT_TYPES
            if unit_type != unit_to_mutate[0] and current_value - self.max_decrease <= unit_values[unit_type] <= current_value
        ]
        if not legal_options:
            return individual
        new_unit = random.choice(legal_options)
        new_unit_placements = individual.unit_placements[:index] + [(new_unit, unit_to_mutate[1])] + individual.unit_placements[index + 1:]
        return Individual(individual.battle_id, new_unit_placements)

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
        return Individual(individual.battle_id, new_unit_placements)


class ReplaceSubarmy(Mutation):

    def __init__(self, max_decrease: int = 100):
        self.max_decrease = max_decrease

    def __call__(self, individual: Individual) -> Individual:
        original_score = individual.points
        kept_unit_placements = list(individual.unit_placements)
        random.shuffle(kept_unit_placements)
        index = random.randint(0, len(kept_unit_placements) - 1)
        kept_unit_placements = kept_unit_placements[:index]
        new_score = sum(unit_values[unit_type] for unit_type, _ in kept_unit_placements)

        new_subarmy = generate_random_army(original_score - new_score, self.max_decrease)
        return Individual(individual.battle_id, kept_unit_placements + new_subarmy)


class MoveNextToAlly(Mutation):

    def __init__(self, noise_scale: float):
        self.noise_scale = noise_scale

    def __call__(self, individual: Individual) -> Individual:
        random_ally_index = random.randint(0, len(individual.unit_placements) - 1)
        random_other_ally_index = random.randint(0, len(individual.unit_placements) - 1)
        # Can be the same ally
        random_ally = individual.unit_placements[random_ally_index]
        random_other_ally = individual.unit_placements[random_other_ally_index]
        # Move random_ally next to random_other_ally
        new_position = random_other_ally[1]
        def distance(position1: Tuple[float, float], position2: Tuple[float, float]) -> float:
            return math.sqrt((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2)
        while distance(new_position, random_other_ally[1]) < 10:
            new_position = (
                random.gauss(random_other_ally[1][0], self.noise_scale),
                random.gauss(random_other_ally[1][1], self.noise_scale)
            )
        return Individual(
            individual.battle_id,
            individual.unit_placements[:random_ally_index] + [(random_ally[0], new_position)] + individual.unit_placements[random_ally_index + 1:]
        )


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
            return Individual(individual1.battle_id, left_unit_placements), Individual(individual2.battle_id, right_unit_placements)


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
            return Individual(individual1.battle_id, new_unit_placements1), Individual(individual2.battle_id, new_unit_placements2)


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


class UniformSelection(SelectIndividual):

    def __call__(self, population: Population) -> Individual:
        return random.choice(population.individuals)


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
        selector: SelectIndividual,
        parents_per_generation: int,
        children_per_generation: int,
        mutation_adaptation_rate: float = 0.1,
        category_cap: int = 3,
        n_mutations: int = 1,
    ):
        self.mutations = mutations
        self.selector = selector
        self.parents_per_generation = parents_per_generation
        self.children_per_generation = children_per_generation
        self.mutation_rates = {
            mutation: 1/len(mutations)
            for mutation in mutations
        }
        self.mutation_adaptation_rate = mutation_adaptation_rate
        self.category_cap = category_cap
        self.n_mutations = n_mutations

    def __call__(self, population: Population) -> Population:
        parents = population.individuals

        # Generate children
        next_generation = set(parents)
        mutation_pairs = []
        while len(next_generation) < self.children_per_generation + self.parents_per_generation:
            parent = self.selector(population)
            mutations = random.choices(list(self.mutation_rates.keys()), weights=list(self.mutation_rates.values()), k=self.n_mutations)
            child = parent
            for mutation in mutations:
                child = mutation(child)
            if child not in next_generation:
                mutation_pairs.extend((mutation, parent, child) for mutation in mutations)
                next_generation.add(child)

        # Evaluate parents + children
        parents_and_children = Population(list(next_generation))
        parents_and_children.evaluate()

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


class Plotter(ABC):

    @abstractmethod
    def update(self, population: Population):
        pass

    @abstractmethod
    def create_plot(self) -> str:
        pass

    def save_plot(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.create_plot())


class UnitCountsPlotter(Plotter):

    def __init__(self):
        self.unit_counts_history = defaultdict(list)
    
    def update(self, population: Population):
        population_counts = Counter(
            unit_type 
            for ind in population.individuals 
            for unit_type, _ in ind.unit_placements
        )
        for unit_type in ALLOWED_UNIT_TYPES:
            self.unit_counts_history[unit_type].append(population_counts.get(unit_type, 0))
        
    def create_plot(self) -> str:
        """Create and save the unit counts plot."""
        fig = go.Figure()
        
        for unit_type in ALLOWED_UNIT_TYPES:
            counts = self.unit_counts_history[unit_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=unit_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        
        fig.update_layout(
            title="Unit Type Population Over Generations",
            xaxis_title="Generation",
            yaxis_title="Unit Count",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)  # Add right margin for legend
        )
        return fig.to_html()


class UnitValuesPlotter(Plotter):

    def __init__(self):
        self.unit_values_history = defaultdict(list)

    def update(self, population: Population):
        total_unit_values = defaultdict(int)
        for ind in population.individuals:
            for unit_type, _ in ind.unit_placements:
                total_unit_values[unit_type] += unit_values[unit_type]
        for unit_type in ALLOWED_UNIT_TYPES:
            self.unit_values_history[unit_type].append(total_unit_values[unit_type])

    def create_plot(self) -> str:
        fig = go.Figure()
        for unit_type in ALLOWED_UNIT_TYPES:
            counts = self.unit_values_history[unit_type]
            fig.add_trace(go.Scatter(
                x=list(range(len(counts))),
                y=counts,
                name=unit_type.name,
                mode='lines',
                hovertemplate='%{fullData.name}<extra></extra>',
            ))
        return fig.to_html()


class GradeDistributionPlotter(Plotter):

    GRADE_ORDER = ["S", "A", "B", "C", "D", "F", "Failed"]
    GRADE_COLORS = {
        "S": "#4CAF50",  # Green
        "A": "#8BC34A",  # Light Green
        "B": "#CDDC39",  # Lime
        "C": "#FFEB3B",  # Yellow
        "D": "#FFC107",  # Amber
        "F": "#F44336",  # Red
        "Failed": "#9E9E9E"  # Gray
    }
    def __init__(self):
        self.grade_history = defaultdict(list)
        self.best_points_history = []

    def update(self, population: Population):
        grade_distribution = Counter()
        for ind in population.individuals:
            grade_distribution[ind.fitness.grade] += 1
        for grade in self.GRADE_ORDER:
            self.grade_history[grade].append(grade_distribution[grade])
        self.best_points_history.append(population.best_individuals[0].points)

    def create_plot(self) -> str:
        """Create and save the grade distribution plot."""
        fig = go.Figure()
        
        # Define grade order and colors
        # For each grade, create a trace showing count over generations
        for grade in self.GRADE_ORDER:
            y_values = self.grade_history[grade]
            generations = list(range(len(self.grade_history[grade])))

            # Only add the trace if this grade appears at least once
            if sum(y_values) > 0:
                fig.add_trace(go.Scatter(
                    x=generations,
                    y=y_values,
                    name=grade,
                    mode='lines+markers',
                    line=dict(width=3, color=self.GRADE_COLORS.get(grade)),
                    marker=dict(size=8),
                    hovertemplate=f'Grade: {grade}<br>Generation: %{{x}}<br>Count: %{{y}}<extra></extra>',
                ))
        
        # Add best solution points as a secondary y-axis
        if any(p is not None for p in self.best_points_history):
            fig.add_trace(go.Scatter(
                x=list(range(len(self.best_points_history))),
                y=self.best_points_history,
                name="Best Solution Points",
                mode='lines+markers',
                line=dict(width=3, color='#000000', dash='dash'),  # Black dashed line
                marker=dict(size=8, symbol='diamond'),
                hovertemplate='Generation: %{x}<br>Best Solution Points: %{y}<extra></extra>',
                yaxis="y2"
            ))
            
        # Update layout
        fig.update_layout(
            title="Grade Distribution Over Generations",
            xaxis_title="Generation",
            yaxis_title="Number of Individuals",
            yaxis2=dict(
                title="Points",
                overlaying="y",
                side="right",
                showgrid=False
            ),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.05
            ),
            margin=dict(r=150)  # Add right margin for legend
        )
        
        return fig.to_html()

class PlotGroup(Plotter):

    def __init__(
        self,
        plotters: List[Plotter],
    ):
        self.plotters = plotters

    def update(self, population: Population):
        for plotter in self.plotters:
            plotter.update(population)

    def create_plot(self) -> str:
        html = ""
        for plotter in self.plotters:
            html += plotter.create_plot()
        return html

def random_population(
    battle_id: str,
    size: int,
    target_cost: int,
) -> Population:
    return Population([
        Individual(battle_id, generate_random_army(target_cost))
        for _ in range(size)
    ])

def main():

    BATTLE_ID = "I need a medic!"
    PARENTS_PER_GENERATION = 10
    CHILDREN_PER_GENERATION = 10
    CATEGORY_CAP = None
    TOURNAMENT_SIZE = None
    population = random_population(battle_id=BATTLE_ID, size=PARENTS_PER_GENERATION, target_cost=get_battle_id(BATTLE_ID).grades.d_cutoff)
    population.evaluate()
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
        mutation_adaptation_rate=0.1,
        n_mutations=1,
        category_cap=CATEGORY_CAP if CATEGORY_CAP is not None else PARENTS_PER_GENERATION,
    )
    
    # Initialize the population plotter
    plotter = PlotGroup(
        plotters=[
            UnitCountsPlotter(),
            UnitValuesPlotter(),
            GradeDistributionPlotter(),
        ],
    )
    
    # Plot initial population
    plotter.update(population)
    
    generation = 1  # Start at 1 since we've plotted generation 0
    try:
        while True:
            print(f"Generation {generation}")
            
            # Evolve the population
            population = evolution(population)
            
            # Print status
            # print(population)
            # print(evolution.mutation_rates)
            
            # Update the plot with the evolved population
            plotter.update(population)
            plotter.save_plot(f"plots/battle.html")
            
            generation += 1
    finally:
        # Make sure to clean up the process pool when done
        cleanup_process_pool()

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
