"""
Run script for the Needs-Based Wolf-Sheep model.

Runs both the original Wolf-Sheep model and the needs-based version
multiple times with different seeds, then plots the mean population
dynamics with shaded variance bands for comparison.

Running multiple seeds controls for randomness and ensures any observed
difference is due to the behavioural change, not random variation.
"""

import pandas as pd
import matplotlib.pyplot as plt
from mesa.examples.advanced.wolf_sheep.model import WolfSheep, WolfSheepScenario
from model import NeedsBasedWolfSheep

STEPS = 500
N_RUNS = 1000


def run_model(model, steps):
    """Run a model for a given number of steps and return collected data."""
    for _ in range(steps):
        model.step()
    return model.datacollector.get_model_vars_dataframe()


def run_multiple_original(steps, n_runs):
    """Run the original model multiple times and return mean and std."""
    all_data = []
    for seed in range(n_runs):
        model = WolfSheep(scenario=WolfSheepScenario(
            initial_wolves=20,
            initial_sheep=150,
            sheep_reproduce=0.08,
            wolf_gain_from_food=12.0,
            grass_regrowth_time=20,
            rng=seed,
        ))
        data = run_model(model, steps)
        all_data.append(data)
    mean = pd.concat(all_data).groupby(level=0).mean()
    std = pd.concat(all_data).groupby(level=0).std()
    return mean, std


def run_multiple_needs_based(steps, n_runs):
    """Run the needs-based model multiple times and return mean and std."""
    all_data = []
    for seed in range(n_runs):
        model = NeedsBasedWolfSheep(
            initial_sheep=150,
            initial_wolves=20,
            sheep_reproduce=0.08,
            wolf_gain_from_food=12.0,
            grass_regrowth_time=20,
            seed=seed,
        )
        data = run_model(model, steps)
        all_data.append(data)
    mean = pd.concat(all_data).groupby(level=0).mean()
    std = pd.concat(all_data).groupby(level=0).std()
    return mean, std


def plot_population(ax_animals, ax_grass, mean, std, title):
    """Plot animals and grass on separate subplots."""
    steps = range(len(mean))

    # Animals on top subplot
    ax_animals.plot(steps, mean["Wolves"], label="Wolves", color="red")
    ax_animals.fill_between(steps,
                            mean["Wolves"] - std["Wolves"],
                            mean["Wolves"] + std["Wolves"],
                            alpha=0.2, color="red")
    ax_animals.plot(steps, mean["Sheep"], label="Sheep", color="blue")
    ax_animals.fill_between(steps,
                            mean["Sheep"] - std["Sheep"],
                            mean["Sheep"] + std["Sheep"],
                            alpha=0.2, color="blue")
    ax_animals.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax_animals.set_ylim(bottom=0)
    ax_animals.set_title(title)
    ax_animals.set_ylabel("Population")
    ax_animals.legend()

    # Grass on bottom subplot
    ax_grass.plot(steps, mean["Grass"], label="Grass", color="green")
    ax_grass.fill_between(steps,
                          mean["Grass"] - std["Grass"],
                          mean["Grass"] + std["Grass"],
                          alpha=0.2, color="green")
    ax_grass.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax_grass.set_ylim(bottom=0)
    ax_grass.set_xlabel("Steps")
    ax_grass.set_ylabel("Grass")
    ax_grass.legend()


def main():
    print(f"Running original Wolf-Sheep model {N_RUNS} times...")
    original_mean, original_std = run_multiple_original(STEPS, N_RUNS)

    print(f"Running needs-based Wolf-Sheep model {N_RUNS} times...")
    needs_based_mean, needs_based_std = run_multiple_needs_based(STEPS, N_RUNS)

   # Plot population Changes

    fig, axes = plt.subplots(2, 2, figsize=(14, 8))

    plot_population(axes[0][0], axes[1][0],
                    original_mean, original_std,
                    "Original Wolf-Sheep\n(mean ± std over 500 runs)")
    plot_population(axes[0][1], axes[1][1],
                    needs_based_mean, needs_based_std,
                    "Needs-Based Wolf-Sheep\n(mean ± std over 500 runs)")

    plt.suptitle(
        "Population Dynamics: Original vs Needs-Based Sheep Behaviour")
    plt.tight_layout()
    plt.savefig("comparison.png")
    plt.show()
    print("Plot saved to comparison.png")


if __name__ == "__main__":
    main()
