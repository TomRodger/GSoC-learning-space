# Platform Analysis

Comparison of how Mesa, NetLogo, GAMA, and Agents.jl handle behavioural agent 
architecture. Built as background research for the GSoC 2026 Behavioural Framework 
project.

## The core problem

The lack of behavioural primitives is not inherent to ABM frameworks. Mesa is 
behind its peers in this specific area.

## NetLogo

Provides built-in support for agent state variables with automatic UI binding. 
Its ask construct allows agents to interleave actions within a single tick, meaning 
an agent can move, check conditions, and act again within one step. Agents can have 
named state variables that are tracked automatically. However, NetLogo has no 
explicit drive or goal architecture, so behaviour still gets structured as rules rather 
than composable components.

## GAMA

Provides a native BDI architecture through its simple_bdi plugin, with built-in 
beliefs, desires, intentions, and plan selection. Modellers can express 
goal-directed agents without building the abstractions from scratch. This is the 
most advanced behavioural architecture of any mainstream ABM platform. There is a trade-off though since GAMA seemingly has a steep learning curve and looks to be less accessible than Mesa for Python users.

## Agents.jl

Supports continuous-time agent dynamics and event-driven scheduling natively. 
Agents activate based on events rather than fixed ticks, which avoids the execution 
timing problem I hit in Sugarscape. However, it lacks explicit drive or goal 
primitives in the same way Mesa does.

## Mesa

Mesa's strength is Python ecosystem integration and accessibility. However for 
behavioural modelling specifically it is behind all three platforms above. There is 
no native support for drive states, action selection, goal representation, or 
event-driven behaviour activation. All of these must be built from scratch inside 
step().

## Key insight

The platforms differ in syntax and scheduling flexibility but the more important 
difference is in what they provide natively. GAMA gives you BDI, Agents.jl gives you event-driven activation, NetLogo gives you interleaved actions, and Mesa gives you step().

The Behavioural Framework project's job is to close this gap while maintaining 
Mesa's design philosophy: flexible building blocks rather than rigid architectures. 
The goal is not to copy GAMA's BDI system as a whole, but instead to provide the primitives from which modellers can assemble whatever architecture their model needs.

## Deeper comparison planned

Phase 2 of the GSoC project involves implementing the same behavioural patterns in NetLogo and GAMA directly (the predator-prey and market agent patterns I have already built in Mesa) and documenting how each platform handles state management, decision selection, and action timing. BDI architecture will be added to this comparison once built in Phase 1. This will ground the framework design in strong cross-platform evidence rather than just a quick survey.