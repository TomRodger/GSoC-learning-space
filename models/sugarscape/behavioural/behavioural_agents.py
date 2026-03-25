import math

from mesa.discrete_space import CellAgent

# Thresholds (module-level constants)
CRITICAL_THRESHOLD = 3
COMFORTABLE_THRESHOLD = 7
IMBALANCE_RATIO = 1.5


# Helper function
def get_distance(cell_1, cell_2):
    """
    Calculate the Euclidean distance between two positions.

    Used in Trader.move()
    """
    x1, y1 = cell_1.coordinate
    x2, y2 = cell_2.coordinate
    dx = x1 - x2
    dy = y1 - y2
    return math.sqrt(dx**2 + dy**2)


######################################################################
#                                                                    #
#                        BEHAVIOUR CLASSES                           #
#                                                                    #
######################################################################


class Behaviour:
    """
    Base class for agent drives.

    Each behaviour defines:
      - name: string identifier used for data collection
      - score(): how urgent this behaviour is for the given agent
      - act(): the full action sequence when this behaviour is selected
    """
    name = "default"

    def score(self, agent):
        raise NotImplementedError

    def act(self, agent):
        raise NotImplementedError


class SurviveBehaviour(Behaviour):
    """
    Emergency drive: fires when either resource is critically low.

    Overrides normal behaviour — agent moves greedily toward the
    most urgent resource and skips trading entirely.
    """
    name = "survive"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Score is positive only when below critical threshold
        return max(0, CRITICAL_THRESHOLD - min(sugar_ticks, spice_ticks))

    def act(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        urgent = "sugar" if sugar_ticks < spice_ticks else "spice"
        agent.move(mode="survive", urgent_resource=urgent)
        agent.eat()
        # No trading — survival is all that matters
        agent.maybe_die()


class GatherSugarBehaviour(Behaviour):
    """
    Resource drive: agent needs sugar more than spice.

    Moves toward sugar-rich cells with welfare as tiebreaker.
    Still trades opportunistically if neighbours are available.
    """
    name = "gather_sugar"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Score is the deficit — how much more spice ticks we have than sugar
        return max(0, spice_ticks - sugar_ticks)

    def act(self, agent):
        agent.move(mode="gather_sugar")
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


class GatherSpiceBehaviour(Behaviour):
    """
    Resource drive: agent needs spice more than sugar.

    Moves toward spice-rich cells with welfare as tiebreaker.
    Still trades opportunistically if neighbours are available.
    """
    name = "gather_spice"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Score is the deficit — how much more sugar ticks we have than spice
        return max(0, sugar_ticks - spice_ticks)

    def act(self, agent):
        agent.move(mode="gather_spice")
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


class SeekTradeBehaviour(Behaviour):
    """
    Trade drive: agent is comfortable but has an imbalanced surplus.

    Only activates when both resources are above the comfortable
    threshold. Moves toward cells near complementary traders.
    """
    name = "seek_trade"

    def score(self, agent):
        sugar_ticks = agent.sugar / agent.metabolism_sugar
        spice_ticks = agent.spice / agent.metabolism_spice
        # Only scores positive when both resources are comfortable
        if sugar_ticks > COMFORTABLE_THRESHOLD and spice_ticks > COMFORTABLE_THRESHOLD:
            return max(sugar_ticks / spice_ticks, spice_ticks / sugar_ticks)
        return 0

    def act(self, agent):
        agent.move(mode="seek_trade")
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


class DefaultBehaviour(Behaviour):
    """
    Fallback drive: resources are roughly balanced.

    Uses the original welfare-maximising movement.
    Always scores just above zero so it loses to any real drive.
    """
    name = "default"

    def score(self, agent):
        return 0.01

    def act(self, agent):
        agent.move(mode="default")
        agent.eat()
        agent.maybe_die()
        if agent.cell is not None and agent.model.enable_trade:
            agent.trade_with_neighbors()


######################################################################
#                                                                    #
#                          TRADER AGENT                              #
#                                                                    #
######################################################################


class Trader(CellAgent):
    """
    Trader agent with behaviour-driven decision making.

    Instead of a monolithic step() with inline conditionals,
    the agent holds a list of Behaviour objects. Each tick,
    the behaviour with the highest score is selected and
    executes the full action sequence.

    Adding a new drive means writing a new Behaviour class
    and appending it to self.behaviours — no changes to
    step(), move(), or trade_with_neighbors().
    """

    def __init__(
        self,
        model,
        cell,
        sugar=0,
        spice=0,
        metabolism_sugar=0,
        metabolism_spice=0,
        vision=0,
    ):
        super().__init__(model)
        self.cell = cell
        self.sugar = sugar
        self.spice = spice
        self.metabolism_sugar = metabolism_sugar
        self.metabolism_spice = metabolism_spice
        self.vision = vision
        self.prices = []
        self.trade_partners = []
        self.active_drive = None

        # Behaviours — extend by appending new Behaviour subclasses
        self.behaviours = [
            SurviveBehaviour(),
            GatherSugarBehaviour(),
            GatherSpiceBehaviour(),
            SeekTradeBehaviour(),
            DefaultBehaviour(),
        ]

    ######################################################################
    #                                                                    #
    #                        TRADE HELPERS                               #
    #                                                                    #
    ######################################################################

    def get_trader(self, cell):
        """Helper function used in self.trade_with_neighbors()"""
        for agent in cell.agents:
            if isinstance(agent, Trader):
                return agent

    def calculate_welfare(self, sugar, spice):
        """
        Cobb-Douglas welfare function.

        From Growing Artificial Societies p. 97.
        Used in move() for cell scoring and in trade() for
        evaluating whether a trade improves both agents' welfare.
        """
        m_total = self.metabolism_sugar + self.metabolism_spice
        return sugar ** (self.metabolism_sugar / m_total) * spice ** (
            self.metabolism_spice / m_total
        )

    def is_starved(self):
        """Helper function for self.maybe_die()"""
        return (self.sugar <= 0) or (self.spice <= 0)

    def calculate_MRS(self, sugar, spice):
        """
        Marginal Rate of Substitution.

        From Growing Artificial Societies p. 101.
        Determines what the trader needs and can give up.
        """
        return (spice / self.metabolism_spice) / (sugar / self.metabolism_sugar)

    def calculate_sell_spice_amount(self, price):
        """
        Helper function for self.maybe_sell_spice().

        Determines the quantities of sugar and spice to exchange
        at a given price.
        """
        if price >= 1:
            sugar = 1
            spice = int(price)
        else:
            sugar = int(1 / price)
            spice = 1
        return sugar, spice

    def sell_spice(self, other, sugar, spice):
        """
        Execute a spice-for-sugar exchange between two traders.

        Used in self.maybe_sell_spice().
        """
        self.sugar += sugar
        other.sugar -= sugar
        self.spice -= spice
        other.spice += spice

    def maybe_sell_spice(self, other, price, welfare_self, welfare_other):
        """
        Evaluate and potentially execute a spice sale.

        Checks two criteria before trading:
        1. Both agents must be better off after the trade
        2. MRS crossing condition must not be violated
        """
        sugar_exchanged, spice_exchanged = self.calculate_sell_spice_amount(
            price)

        # Assess hypothetical post-trade amounts
        self_sugar = self.sugar + sugar_exchanged
        other_sugar = other.sugar - sugar_exchanged
        self_spice = self.spice - spice_exchanged
        other_spice = other.spice + spice_exchanged

        # Ensure neither agent runs out of either resource
        if (
            (self_sugar <= 0)
            or (other_sugar <= 0)
            or (self_spice <= 0)
            or (other_spice <= 0)
        ):
            return False

        # Trade criteria #1 — are both agents better off?
        both_agents_better_off = (
            welfare_self < self.calculate_welfare(self_sugar, self_spice)
        ) and (welfare_other < other.calculate_welfare(other_sugar, other_spice))

        # Trade criteria #2 — MRS crossing condition
        mrs_not_crossing = self.calculate_MRS(
            self_sugar, self_spice
        ) > other.calculate_MRS(other_sugar, other_spice)

        if not (both_agents_better_off and mrs_not_crossing):
            return False

        # Criteria met, execute trade
        self.sell_spice(other, sugar_exchanged, spice_exchanged)
        return True

    def trade(self, other):
        """
        Bilateral trade between self and other.

        Computes MRS for both agents, determines price as the
        geometric mean, and executes the trade if beneficial.
        Recurses until no further beneficial trades are possible.
        """
        assert self.sugar > 0
        assert self.spice > 0
        assert other.sugar > 0
        assert other.spice > 0

        # Calculate marginal rate of substitution (p. 101)
        mrs_self = self.calculate_MRS(self.sugar, self.spice)
        mrs_other = other.calculate_MRS(other.sugar, other.spice)

        # Calculate each agent's welfare
        welfare_self = self.calculate_welfare(self.sugar, self.spice)
        welfare_other = other.calculate_welfare(other.sugar, other.spice)

        if math.isclose(mrs_self, mrs_other):
            return

        # Price is geometric mean of both MRS values
        price = math.sqrt(mrs_self * mrs_other)

        if mrs_self > mrs_other:
            # Self is a sugar buyer, spice seller
            sold = self.maybe_sell_spice(
                other, price, welfare_self, welfare_other)
        else:
            # Self is a spice buyer, sugar seller
            sold = other.maybe_sell_spice(
                self, price, welfare_other, welfare_self)

        if not sold:
            return

        # Capture data
        self.prices.append(price)
        self.trade_partners.append(other.unique_id)

        # Continue trading until no further benefit
        self.trade(other)

    ######################################################################
    #                                                                    #
    #                      MAIN AGENT FUNCTIONS                          #
    #                                                                    #
    ######################################################################

    def move(self, mode="default", urgent_resource=None):
        """
        Move to the best available cell within vision.

        Cell scoring depends on the active behaviour's mode:
        - survive: pure greedy toward the critical resource
        - gather_sugar: max sugar first, welfare as tiebreaker
        - gather_spice: max spice first, welfare as tiebreaker
        - seek_trade: welfare weighted by nearby complementary traders
        - default: original welfare-maximising behaviour
        """

        # 1. Identify all possible moves
        neighboring_cells = [
            cell
            for cell in self.cell.get_neighborhood(self.vision, include_center=True)
            if cell.is_empty
        ]

        if not neighboring_cells:
            return

        # 2. Score cells depending on mode

        if mode == "survive":
            # Pure greedy: only care about the critical resource
            if urgent_resource == "sugar":
                scores = [cell.sugar for cell in neighboring_cells]
            else:
                scores = [cell.spice for cell in neighboring_cells]

        elif mode == "gather_sugar":
            # Two-pass: filter to cells with the most sugar,
            # then rank those by welfare as tiebreaker
            max_sugar = max(cell.sugar for cell in neighboring_cells)
            neighboring_cells = [
                cell for cell in neighboring_cells
                if cell.sugar == max_sugar
            ]
            scores = [
                self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                for cell in neighboring_cells
            ]

        elif mode == "gather_spice":
            # Two-pass: filter to cells with the most spice,
            # then rank those by welfare as tiebreaker
            max_spice = max(cell.spice for cell in neighboring_cells)
            neighboring_cells = [
                cell for cell in neighboring_cells
                if cell.spice == max_spice
            ]
            scores = [
                self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                for cell in neighboring_cells
            ]

        elif mode == "seek_trade":
            # Score cells by base welfare weighted by count of
            # complementary traders reachable from that cell
            sugar_ticks = self.sugar / self.metabolism_sugar
            spice_ticks = self.spice / self.metabolism_spice
            need_sugar = spice_ticks > sugar_ticks
            need_spice = sugar_ticks > spice_ticks

            scores = []
            for cell in neighboring_cells:
                base = self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                # Count traders reachable from this cell who have
                # a complementary surplus
                complementary_count = 0
                for agent in cell.get_neighborhood(radius=self.vision).agents:
                    if not isinstance(agent, Trader) or agent is self:
                        continue
                    other_sugar_t = agent.sugar / agent.metabolism_sugar
                    other_spice_t = agent.spice / agent.metabolism_spice
                    # I need sugar and they have more sugar than spice
                    if need_sugar and other_sugar_t > other_spice_t:
                        complementary_count += 1
                    # I need spice and they have more spice than sugar
                    elif need_spice and other_spice_t > other_sugar_t:
                        complementary_count += 1

                # Proportional bonus: cell near 2 good partners
                # scores 3x a cell near none
                scores.append(base * (1 + complementary_count))

        else:
            # Default: original welfare-maximising behaviour
            scores = [
                self.calculate_welfare(
                    self.sugar + cell.sugar,
                    self.spice + cell.spice,
                )
                for cell in neighboring_cells
            ]

        # 3. Select best cell (same tiebreaking as original)

        max_score = max(scores)
        candidates = [
            cell
            for cell, score in zip(neighboring_cells, scores)
            if math.isclose(score, max_score)
        ]

        min_dist = min(get_distance(self.cell, cell) for cell in candidates)

        final_candidates = [
            cell
            for cell in candidates
            if math.isclose(get_distance(self.cell, cell), min_dist, rel_tol=1e-02)
        ]

        # Random choice as final tiebreaker
        self.cell = self.random.choice(final_candidates)

    def eat(self):
        """Harvest resources from current cell and pay metabolism costs."""
        self.sugar += self.cell.sugar
        self.cell.sugar = 0
        self.sugar -= self.metabolism_sugar

        self.spice += self.cell.spice
        self.cell.spice = 0
        self.spice -= self.metabolism_spice

    def maybe_die(self):
        """Remove trader if either sugar or spice is exhausted."""
        if self.is_starved():
            self.remove()

    def step(self):
        """
        Behaviour-driven step.

        The highest-scoring behaviour determines the full action
        sequence for this tick — movement, eating, and trading
        are all controlled by the selected behaviour.

        Compare to the monolith version where this logic is
        spread across step(), move(), and trade_with_neighbors()
        via string flags and inline conditionals.
        """
        self.prices = []
        self.trade_partners = []

        # Select the most urgent behaviour
        best = max(self.behaviours, key=lambda b: b.score(self))
        self.active_drive = best.name

        # Behaviour controls the full action sequence
        best.act(self)

    def trade_with_neighbors(self):
        """
        Trade with all traders within vision.

        Called by the active behaviour's act() method — not by the
        model. This means the behaviour controls whether trading
        happens at all (survive skips it) and when it happens
        relative to movement and eating.
        """
        for a in self.cell.get_neighborhood(radius=self.vision).agents:
            self.trade(a)
