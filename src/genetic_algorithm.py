"""Generic genetic algorithm framework based on DEAP.

This module provides a flexible framework for genetic algorithms using the DEAP library.
It includes customizable fitness evaluation, crossover, mutation, and selection operations.
"""

import random
import multiprocessing
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Generic, Union

import numpy as np
from deap import algorithms, base, creator, tools

# Type variables for generic type hints
T = TypeVar('T')  # Individual type
F = TypeVar('F')  # Fitness type


class LexicographicFitness(base.Fitness):
    """Fitness class that implements lexicographic ordering for multi-objective optimization.
    
    Lexicographic ordering prioritizes objectives in order, only considering the next objective
    when the current objective values are equal.
    """
    
    def __gt__(self, other: 'LexicographicFitness') -> bool:
        """Compare two fitness values using lexicographic ordering.
        
        Args:
            other: Another fitness object to compare with.
            
        Returns:
            True if this fitness is better than the other, False otherwise.
        """
        if not self.valid or not other.valid:
            raise ValueError("Invalid fitness values in comparison")
            
        # Compare values lexicographically
        for i in range(len(self.values)):
            # If weights[i] > 0, higher is better; otherwise, lower is better
            if self.weights[i] > 0:
                if self.values[i] > other.values[i]:
                    return True
                if self.values[i] < other.values[i]:
                    return False
            else:
                if self.values[i] < other.values[i]:
                    return True
                if self.values[i] > other.values[i]:
                    return False
        
        # All values are equal
        return False
        
    def __lt__(self, other: 'LexicographicFitness') -> bool:
        """Compare two fitness values using lexicographic ordering.
        
        Args:
            other: Another fitness object to compare with.
            
        Returns:
            True if this fitness is worse than the other, False otherwise.
        """
        if not self.valid or not other.valid:
            raise ValueError("Invalid fitness values in comparison")
            
        # Compare values lexicographically
        for i in range(len(self.values)):
            # If weights[i] > 0, higher is better; otherwise, lower is better
            if self.weights[i] > 0:
                if self.values[i] < other.values[i]:
                    return True
                if self.values[i] > other.values[i]:
                    return False
            else:
                if self.values[i] > other.values[i]:
                    return True
                if self.values[i] < other.values[i]:
                    return False
        
        # All values are equal
        return False


def setup_deap_types(fitness_weights: Tuple[float, ...], 
                     individual_type: type = list) -> None:
    """Set up DEAP creator types for genetic algorithm.
    
    Args:
        fitness_weights: The weights for fitness objectives. Positive values
            indicate maximization, negative values indicate minimization.
        individual_type: Base type for individuals (default: list).
    """
    # Clean up existing types if they exist to avoid errors when reusing
    if hasattr(creator, "FitnessLex"):
        del creator.FitnessLex
    if hasattr(creator, "Individual"):
        del creator.Individual
    
    # Create custom fitness class with lexicographic ordering
    creator.create("FitnessLex", LexicographicFitness, weights=fitness_weights)
    
    # Create individual type
    creator.create("Individual", individual_type, fitness=creator.FitnessLex)


def tournament_selection(individuals: List[T], k: int, tournsize: int, 
                        fit_attr: str = "fitness") -> List[T]:
    """Select individuals using tournament selection.
    
    Args:
        individuals: A list of individuals to select from.
        k: The number of individuals to select.
        tournsize: The number of individuals in each tournament.
        fit_attr: The attribute of individuals holding the fitness.
        
    Returns:
        List of selected individuals.
    """
    chosen = []
    for _ in range(k):
        # Select tournsize competitors randomly
        competitors = random.sample(individuals, tournsize)
        
        # Find the best individual among competitors
        best = max(competitors, key=lambda ind: getattr(ind, fit_attr))
        
        # Add a copy of the winner to the chosen list
        chosen.append(best)
    
    return chosen


class GeneticAlgorithm(Generic[T, F]):
    """Generic genetic algorithm implementation using DEAP.
    
    This class provides a framework for genetic algorithms with customizable
    evaluation, crossover, mutation, and selection operations.
    """
    
    def __init__(
        self,
        population_size: int = 50,
        generations: int = 50,
        crossover_rate: float = 0.7,
        mutation_rate: float = 0.2,
        tournament_size: int = 3,
        elite_size: int = 1,
        n_jobs: int = -1,
    ):
        """Initialize the genetic algorithm.
        
        Args:
            population_size: Size of the population.
            generations: Number of generations to evolve.
            crossover_rate: Probability of crossover.
            mutation_rate: Probability of mutation.
            tournament_size: Size of tournament for selection.
            elite_size: Number of elite individuals to preserve.
            n_jobs: Number of parallel processes for evaluation (-1 = all cores).
        """
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elite_size = elite_size
        
        # Set up multiprocessing
        if n_jobs == -1:
            self.n_jobs = multiprocessing.cpu_count()
        else:
            self.n_jobs = n_jobs
        
        # Initialize toolbox
        self.toolbox = base.Toolbox()
        
    def register_population(
        self,
        individual_generator: Callable[[], T],
    ) -> None:
        """Register functions for creating individuals and population.
        
        Args:
            individual_generator: Function that generates a single individual.
        """
        # Register individual and population generation
        self.toolbox.register(
            "individual",
            individual_generator
        )
        
        self.toolbox.register(
            "population",
            tools.initRepeat,
            list,
            self.toolbox.individual,
            n=self.population_size
        )
    
    def register_evaluation(
        self,
        evaluate_function: Callable[[T], F],
        parallel: bool = False
    ) -> None:
        """Register evaluation function.
        
        Args:
            evaluate_function: Function to evaluate an individual and return fitness.
            parallel: Whether to use parallel evaluation.
        """
        if parallel and self.n_jobs > 1:
            # Set up parallel evaluation with multiprocessing
            pool = multiprocessing.Pool(processes=self.n_jobs)
            self.toolbox.register("map", pool.map)
        
        self.toolbox.register("evaluate", evaluate_function)
    
    def register_operations(
        self,
        crossover_function: Callable[[T, T], Tuple[T, T]],
        mutation_function: Callable[[T], Tuple[T]],
    ) -> None:
        """Register genetic operations.
        
        Args:
            crossover_function: Function to perform crossover.
            mutation_function: Function to perform mutation.
        """
        # Register genetic operators
        self.toolbox.register("mate", crossover_function)
        self.toolbox.register("mutate", mutation_function)
        
        # Register selection using tournament selection
        self.toolbox.register(
            "select",
            tournament_selection,
            tournsize=self.tournament_size
        )
    
    def run(
        self,
        seed_population: Optional[List[T]] = None,
        early_stopping: bool = False,
        early_stopping_generations: int = 5,
        progress_callback: Optional[Callable[[int, T, F], None]] = None,
    ) -> Tuple[T, F]:
        """Run the genetic algorithm.
        
        Args:
            seed_population: Optional list of individuals to seed the population.
            early_stopping: Whether to stop early if no improvement is found.
            early_stopping_generations: Number of generations with no improvement before stopping.
            progress_callback: Function to call after each generation with progress information.
            
        Returns:
            Tuple of (best individual, best fitness).
        """
        # Create initial population
        if seed_population:
            # If seed population is provided, incorporate it into the initial population
            population = self.toolbox.population()
            
            # Replace some individuals with seed individuals
            for i, ind in enumerate(seed_population):
                if i < len(population):
                    population[i] = ind
        else:
            population = self.toolbox.population()
            
        # Variables for statistics
        best_fitness = None
        best_individual = None
        generations_without_improvement = 0
        
        # Evaluate initial population
        fitnesses = list(map(self.toolbox.evaluate, population))
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
        
        # Evolution loop
        for generation in range(self.generations):
            # Select and clone individuals for reproduction
            offspring = self.toolbox.select(population, len(population) - self.elite_size)
            offspring = list(map(self.toolbox.clone, offspring))
            
            # Apply elitism (preserve best individuals)
            elites = tools.selBest(population, self.elite_size)
            elites = list(map(self.toolbox.clone, elites))
            
            # Apply crossover
            for i in range(1, len(offspring), 2):
                if i < len(offspring) - 1 and random.random() < self.crossover_rate:
                    offspring[i-1], offspring[i] = self.toolbox.mate(offspring[i-1], offspring[i])
                    # Clear fitness values of modified individuals
                    del offspring[i-1].fitness.values
                    del offspring[i].fitness.values
            
            # Apply mutation
            for i in range(len(offspring)):
                if random.random() < self.mutation_rate:
                    offspring[i], = self.toolbox.mutate(offspring[i])
                    # Clear fitness value of modified individual
                    del offspring[i].fitness.values
            
            # Evaluate offspring with invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = list(map(self.toolbox.evaluate, invalid_ind))
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit
            
            # Replace population with offspring and elites
            population[:] = offspring + elites
            
            # Find best individual
            current_best = tools.selBest(population, 1)[0]
            current_best_fitness = current_best.fitness.values
            
            # Update best overall
            if best_fitness is None or current_best.fitness > creator.FitnessLex(best_fitness):
                best_fitness = current_best_fitness
                best_individual = self.toolbox.clone(current_best)
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(generation, best_individual, best_fitness)
            
            # Early stopping
            if early_stopping and generations_without_improvement >= early_stopping_generations:
                break
        
        return best_individual, best_fitness


def adaptive_mutation_rate(
    base_rate: float,
    current_gen: int,
    max_gen: int,
    min_rate: float = 0.05,
    max_rate: float = 0.5
) -> float:
    """Calculate an adaptive mutation rate based on generation.
    
    The mutation rate decreases over time, allowing for more exploration
    early and more exploitation later.
    
    Args:
        base_rate: The base mutation rate.
        current_gen: Current generation number.
        max_gen: Maximum number of generations.
        min_rate: Minimum mutation rate.
        max_rate: Maximum mutation rate.
        
    Returns:
        The adjusted mutation rate.
    """
    # Linear decrease from max_rate to min_rate
    if max_gen <= 1:
        return base_rate
    
    progress = current_gen / (max_gen - 1)
    rate = max_rate - progress * (max_rate - min_rate)
    
    return max(min_rate, min(max_rate, rate)) 