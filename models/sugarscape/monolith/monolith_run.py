"""
Run script for the monolith Sugarscape model.

Runs the model for a set number of steps and prints key statistics,
including drive distribution over time. Outputs data to CSV for analysis.
"""

from monolith_model import SugarscapeMonolith

STEPS = 500
SEED = 42


def run():
    model = SugarscapeMonolith(rng=SEED)
    model.run_model(step_count=STEPS)

    data = model.datacollector.get_model_vars_dataframe()

    # Print summary
    print(f"{'='*60}")
    print(f"Sugarscape Monolith — {STEPS} steps, seed {SEED}")
    print(f"{'='*60}")
    print(f"\nFinal traders alive: {data['#Traders'].iloc[-1]:.0f} / 200")
    print(f"Final trade volume:  {data['Trade Volume'].iloc[-1]:.0f}")
    print(f"Final price:         {data['Price'].iloc[-1]:.3f}")

    # Drive distribution at final step
    print(f"\n{'Drive Distribution (final step)':}")
    print(f"  Survive:      {data['Survive'].iloc[-1]:.0f}")
    print(f"  Gather Sugar: {data['Gather Sugar'].iloc[-1]:.0f}")
    print(f"  Gather Spice: {data['Gather Spice'].iloc[-1]:.0f}")
    print(f"  Seek Trade:   {data['Seek Trade'].iloc[-1]:.0f}")
    print(f"  Default:      {data['Default'].iloc[-1]:.0f}")

    # Drive distribution at step 10 (early) vs step 250 (mid) vs final
    print(f"\n{'Drive Distribution Over Time':}")
    print(f"{'Step':>6} {'Alive':>6} {'Survive':>8} {'Sugar':>8} {'Spice':>8} {'Trade':>8} {'Default':>8}")
    print(f"{'-'*54}")
    for step in [0, 10, 50, 100, 250, STEPS - 1]:
        if step < len(data):
            row = data.iloc[step]
            print(
                f"{step:>6} "
                f"{row['#Traders']:>6.0f} "
                f"{row['Survive']:>8.0f} "
                f"{row['Gather Sugar']:>8.0f} "
                f"{row['Gather Spice']:>8.0f} "
                f"{row['Seek Trade']:>8.0f} "
                f"{row['Default']:>8.0f}"
            )

    # Save to CSV
    data.to_csv("monolith_results.csv")
    print(f"\nFull data saved to monolith_results.csv")


if __name__ == "__main__":
    run()
