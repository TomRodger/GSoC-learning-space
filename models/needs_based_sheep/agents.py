from mesa.discrete_space import CellAgent, FixedAgent


class Animal(CellAgent):
    """Base animal class with persistent internal drive states.

    Unlike simple reflex agents that recalculate state each step,
    drives accumulate and decay over time giving agents memory
    of past experiences. This is the core architectural difference
    explored in this model.
    """

    def __init__(self, model, energy=8, p_reproduce=0.04,
                 energy_from_food=4, cell=None):
        super().__init__(model)
        self.energy = energy
        self.max_energy = energy_from_food * 4
        self.p_reproduce = p_reproduce
        self.energy_from_food = energy_from_food
        self.cell = cell

        # Persistent drive states — these accumulate and decay over time
        # rather than being recalculated fresh each step
        self.hunger = 0.0   # 0 = satisfied, 1 = desperate
        self.fear = 0.0     # 0 = calm, 1 = panicked

    def update_drives(self):
        """Update drive states based on current situation.

        Hunger accumulates every step — an agent that hasn't eaten
        becomes progressively more desperate.
        Fear decays every step — an agent that has fled becomes
        progressively calmer unless wolves remain nearby.
        """
        # Hunger builds up every step regardless
        self.hunger = min(1.0, self.hunger + 0.05)

        # Fear naturally decays toward calm
        self.fear = max(0.0, self.fear - 0.1)

    def spawn_offspring(self):
        """Create offspring by splitting energy."""
        self.energy /= 2
        self.__class__(
            self.model,
            self.energy,
            self.p_reproduce,
            self.energy_from_food,
            self.cell,
        )

    def feed(self):
        """Abstract — implemented by subclasses."""
        pass

    def flee(self):
        """Move to a random safe cell away from wolves."""
        safe_cells = [
            c for c in self.cell.neighborhood
            if not any(isinstance(a, Wolf) for a in c.agents)
        ]
        if safe_cells:
            self.cell = self.random.choice(safe_cells)

    def step(self):
        """Execute one step."""
        self.energy -= 1

        if self.energy < 0:
            self.remove()
            return

        # Update drives based on current situation
        self.update_drives()

        # Make decision based on current drive states
        self.decide_and_act()

        # Reproduce only if calm, well-fed and high energy
        if (self.random.random() < self.p_reproduce
                and self.fear < 0.3
                and self.hunger < 0.4):
            self.spawn_offspring()

    def decide_and_act(self):
        """Default behaviour — move and feed."""
        self.move()
        self.feed()

    def move(self):
        """Move to a random neighbouring cell."""
        self.cell = self.cell.neighborhood.select_random_cell()


class Sheep(Animal):
    """A sheep with persistent hunger and fear drives.

    Key difference from original: fear persists across steps.
    A sheep that just escaped a wolf is still scared next step
    even if no wolves are currently visible. Hunger builds up
    over time making desperate sheep take risks they otherwise
    wouldn't.
    """

    def update_drives(self):
        """Update drives — spike fear if wolves are nearby."""
        # Call parent to handle decay/accumulation
        super().update_drives()

        # Spike fear based on nearby wolves
        nearby_wolves = sum(
            1 for c in self.cell.neighborhood
            for a in c.agents if isinstance(a, Wolf)
        )
        if nearby_wolves > 0:
            # Fear spikes proportionally to wolf count
            self.fear = min(1.0, self.fear + (nearby_wolves * 0.3))

        # Eating resets hunger
        # (handled in feed() but hunger accumulation
        # is overridden here by successful feeding)

    def decide_and_act(self):
        """Choose between fleeing and feeding based on drive states."""
        if self.fear > self.hunger:
            # Fear dominates — flee without eating
            self.flee()
        else:
            # Hunger dominates — move toward food
            self.move_to_food()
            self.feed()

    def feed(self):
        """Eat grass if available — resets hunger drive."""
        grass_patch = next(
            (obj for obj in self.cell.agents
             if isinstance(obj, GrassPatch)),
            None
        )
        if grass_patch and grass_patch.fully_grown:
            self.energy += self.energy_from_food
            self.hunger = 0.0  # Reset hunger on successful feed
            grass_patch.get_eaten()

    def move_to_food(self):
        """Move toward safe cells, preferring those with grass."""
        cells_without_wolves = []
        cells_with_grass = []

        for cell in self.cell.neighborhood:
            has_wolf = False
            has_grass = False

            for obj in cell.agents:
                if isinstance(obj, Wolf):
                    has_wolf = True
                    break
                elif isinstance(obj, GrassPatch) and obj.fully_grown:
                    has_grass = True

            if not has_wolf:
                cells_without_wolves.append(cell)
                if has_grass:
                    cells_with_grass.append(cell)

        if not cells_without_wolves:
            return

        target_cells = (
            cells_with_grass if cells_with_grass
            else cells_without_wolves
        )
        self.cell = self.random.choice(target_cells)


class Wolf(Animal):
    """A wolf that hunts sheep."""

    def feed(self):
        """Eat a sheep if present — resets hunger."""
        sheep = [obj for obj in self.cell.agents
                 if isinstance(obj, Sheep)]
        if sheep:
            sheep_to_eat = self.random.choice(sheep)
            self.energy += self.energy_from_food
            self.hunger = 0.0  # Reset hunger on successful hunt
            sheep_to_eat.remove()

    def move(self):
        """Move toward sheep if visible, otherwise random."""
        cells_with_sheep = self.cell.neighborhood.select(
            lambda cell: any(isinstance(obj, Sheep)
                             for obj in cell.agents)
        )
        target_cells = (
            cells_with_sheep if len(cells_with_sheep) > 0
            else self.cell.neighborhood
        )
        self.cell = target_cells.select_random_cell()


class GrassPatch(FixedAgent):
    """A grass patch that regrows after being eaten."""

    def __init__(self, model, countdown, grass_regrowth_time, cell):
        super().__init__(model)
        self.fully_grown = countdown == 0
        self.grass_regrowth_time = grass_regrowth_time
        self.cell = cell

        if not self.fully_grown:
            self.model.schedule_event(self.regrow, after=countdown)

    def regrow(self):
        """Regrow the grass."""
        self.fully_grown = True

    def get_eaten(self):
        """Mark as eaten and schedule regrowth."""
        self.fully_grown = False
        self.model.schedule_event(
            self.regrow, after=self.grass_regrowth_time
        )
