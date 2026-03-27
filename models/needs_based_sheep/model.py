"""
Needs-Based Wolf-Sheep Predation Model
=======================================

An extension of the classic Wolf-Sheep Predation model that replaces
the sheep's fixed step sequence with a needs-based decision system.

Sheep now weigh two competing drives — hunger and fear — and choose
their action based on whichever drive is stronger. This demonstrates
the gap between Mesa's current simple reflex behaviour and the
goal-directed, utility-based architectures described in agent theory.

Based on the original NetLogo model:
    Wilensky, U. (1997). NetLogo Wolf Sheep Predation model.
    http://ccl.northwestern.edu/netlogo/models/WolfSheepPredation.
    Center for Connected Learning and Computer-Based Modeling,
    Northwestern University, Evanston, IL.
"""

import math

from mesa import Model
from mesa.datacollection import DataCollector
from mesa.discrete_space import OrthogonalVonNeumannGrid

from agents import GrassPatch, Sheep, Wolf


class NeedsBasedWolfSheep(Model):
    """Wolf-Sheep Predation Model with needs-based sheep behaviour.

    Sheep use a utility function to weigh hunger against fear of nearby
    wolves, choosing to flee or feed based on whichever drive is stronger.
    This contrasts with the original model where sheep execute a fixed
    sequence every step regardless of their internal state.
    """

    description = (
        "Wolf-Sheep model where sheep weigh competing drives "
        "(hunger vs fear) to decide their behaviour each step."
    )

    def __init__(
        self,
        height=20,
        width=20,
        initial_sheep=150,
        initial_wolves=20,
        sheep_reproduce=0.08,
        wolf_reproduce=0.05,
        wolf_gain_from_food=1.0,
        grass_regrowth_time=20,
        sheep_gain_from_food=4.0,
        seed=None,
    ):
        """Create a new NeedsBasedWolfSheep model.

        Args:
            height: Height of the grid
            width: Width of the grid
            initial_sheep: Number of sheep to start with
            initial_wolves: Number of wolves to start with
            sheep_reproduce: Probability of each sheep reproducing each step
            wolf_reproduce: Probability of each wolf reproducing each step
            wolf_gain_from_food: Energy a wolf gains from eating a sheep
            grass_regrowth_time: Steps for grass to regrow after being eaten
            sheep_gain_from_food: Energy sheep gain from eating grass
            seed: Random seed for reproducibility
        """
        super().__init__(rng=seed)

        self.height = height
        self.width = width

        # Create grid
        self.grid = OrthogonalVonNeumannGrid(
            [self.height, self.width],
            torus=True,
            capacity=math.inf,
            random=self.random,
        )

        # Track wolf, sheep and grass counts over time
        self.datacollector = DataCollector({
            "Wolves": lambda m: len(m.agents_by_type[Wolf]),
            "Sheep": lambda m: len(m.agents_by_type[Sheep]),
            "Grass": lambda m: len(
                m.agents_by_type[GrassPatch].select(lambda a: a.fully_grown)
            ),
        })

        # Create sheep with random starting energy
        Sheep.create_agents(
            self,
            initial_sheep,
            energy=self.rng.random((initial_sheep,)) *
            2 * sheep_gain_from_food,
            p_reproduce=sheep_reproduce,
            energy_from_food=sheep_gain_from_food,
            cell=self.random.choices(
                self.grid.all_cells.cells, k=initial_sheep
            ),
        )

        # Create wolves with random starting energy
        Wolf.create_agents(
            self,
            initial_wolves,
            energy=self.rng.random((initial_wolves,)) *
            2 * wolf_gain_from_food,
            p_reproduce=wolf_reproduce,
            energy_from_food=wolf_gain_from_food,
            cell=self.random.choices(
                self.grid.all_cells.cells, k=initial_wolves
            ),
        )

        # Create grass patches with random initial growth state
        for cell in self.grid:
            fully_grown = self.random.choice([True, False])
            countdown = (
                0 if fully_grown
                else self.random.randrange(0, grass_regrowth_time)
            )
            GrassPatch(self, countdown, grass_regrowth_time, cell)

        self.running = True
        self.datacollector.collect(self)

    def step(self):
        """Execute one step of the model.

        Sheep act first, then wolves, both in random order to avoid
        any bias from activation sequence.
        """
        self.agents_by_type[Sheep].shuffle_do("step")
        self.agents_by_type[Wolf].shuffle_do("step")
        self.datacollector.collect(self)
