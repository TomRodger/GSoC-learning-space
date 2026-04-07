# Review: Darragh Moran — Needs-Based Village Model (PR #439)

## What the model does

A village model where agents manage four competing homeostatic needs: HUNGER, REST, 
SOCIAL, and SAFETY. Needs decay autonomously each tick and agents act on whichever 
is the most urgent, moving toward the relevant resource or partner. It also includes a 
ThreatAgent predator that spikes the SAFETY need via perception.

## Review left on GitHub

https://github.com/mesa/mesa-examples/pull/439

## Issues I raised

**FoodSource and HomePatch should be FixedAgent not CellAgent** — these are 
stationary environment objects that never move after placement. Mesa's convention 
for stationary agents is FixedAgent, which I saw used by GrassPatch in Mesa's built-in 
Sugarscape. Using CellAgent works but is semantically incorrect and could affect 
Mesa's internal agent tracking.

**SolaraViz expects a model instance not a class** — passing VillageModel directly 
causes AttributeError: type object 'VillageModel' has no attribute 'datacollector'. 
The fix is to instantiate first: model = VillageModel(), then pass model to SolaraViz.

**requirements.txt is unspecific** — mesa[viz]>=3.0 causes crashes on Mesa 3.5.1 
with AttributeError in mesa_signals/core.py. The model logic runs cleanly but the 
visualisation fails. Clarifying the version(s) tested on more specifically in the requirements would help improve reproducibility.

## What was good

**NeedSpec dataclass** is a clean design choice. Keeping need configuration 
separate from agent logic means someone extending the model only needs to touch one 
place when tweaking decay rates, or adding a fifth need. This makes VillagerAgent much 
cleaner to read as a result.

**Pain Points documentation** is well done. Labelling the workarounds with numbers and 
connecting them to specific Mesa limitations is directly useful evidence for the 
Behavioural Framework case.

**NeedsAgent abstraction** is also clean and reusable; any model could subclass it, 
which is more than most example models offer.

## What I learned from reading it

Darragh's persistent drive state (with needs that accumulate autonomously over time and 
can only be suppressed, never eliminated) is architecturally closer to homeostatic behaviour than recalculating urgency fresh each tick. Reading this directly influenced how I refactored my Wolf-Sheep model to use persistent drives rather than instantaneous utility calculations. It also showed me that the NeedSpec dataclass pattern is cleaner than storing drive parameters directly on the agent, something I'd do differently if I rebuilt my models.