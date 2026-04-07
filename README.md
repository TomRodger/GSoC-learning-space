# Tom Rodger - Mesa Learning Space

Second Year Computer Science student at the University of Edinburgh. This is my learning space for the GSoC 2026 Mesa behavioural Framework Project. 

Both models were built to explore the same question: what happens when you try to implement drive-based agents in Mesa, and what does that reveal about what the Behavioural Framework needs to provide?

## Models 

### [Needs-Based Wolf-Sheep](models/needs_based_sheep/)
This model extends Mesa's original Wolf-sheep with persistent hunger and fear drives that accumulate and decay over time. The sheep accumulate wiegh competnig drives each tick and choose between fleeing and feeding based on whichever drive is most urgent.

**Key findings:** A 500-run statistical comparison made against the original showed both models produce similar mean population dynamics, but the needs-based version produces lower variance across runs. However, the more important finding was in the architecture: implementing drive-based decision making required dismantling Mesa's existing step() structure entirely and building a custom decide_and_act() method from scratch. There is currently no native Mesa primitive for this. 

### [Drive-Based Sugarscape](models/sugarscape/)
Three-version architectural comparison of Epstein & Axtell's Sugarscape with trader: original Mesa G1MT, monolith (four drives crammed into step() via if/elif chains), and bevaioural (same four drives as decoupled Behaviour classes, each owning their own urgency scoring and action logic).

**Key finding**: the 100-seed batch comparison showed that the behavioural version resulted in a 53% increase in trade volume (13,036 vs 8541, with non-overlapping standard deviations) with a tighter price convergence as well. The increase was unintended during implementation, but it emerged as a consequence of moving trading inside each agent's step() rather than running a separate model pass. shuffle_do() looks like a netural activation call, but it implicitly decides when each agent's actions happen realtive to every other agent's; a choice with consequences that only become visible in the results. 

## What I Learned

Both models independently hit the same wall: implementing drive-based agents required building a custom Behaviour class abstraction that Mesa doesn't currently provide. The monlith version of Sugarscape showed exactly why this matters; with four drives and two resources types, the if/elif chains in step() grow very quickly, coupling between methods becomes implicit, and adding any new drive requires changes across step(), move(), and trade_with_neighbors() simultaneously.

I also learnt that the origanal Mesa agents are smarter than they look. The built-in Sugarscape uses a Cobb-Douglas welfare unction, which makes it a utility-based optimiser, not just a simple reflex agent. The original Mesa Sugarscape agent is not simply lacking goals, but is lacking in temporal depth and action selection: the ability to choose between actions, prioritise one resource over another, or pursue a strategy across multiple ticks. The Behavioural Framework needs to fill this gap. 

## Motivation
[Motivation](motivation.md)

## PR 
[mesa-examples#457](https://github.com/mesa/mesa-examples/pull/457): Drive-Based Sugarscape with three-version architectural comparison

## Reviews
[Reviews of other candidates' work](reviews/)




