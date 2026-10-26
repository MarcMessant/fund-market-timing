"""How much timing can a Henriksson-Merton test detect with two years of weekly data?

Monte Carlo: market excess returns x ~ N(mu, sigma) calibrated on the MSCI ACWI over the sample
(13.6% annual premium, 12.5% annual volatility), a fund with beta_down = 0.85 and beta_up = 0.85 + beta2,
idiosyncratic weekly volatility 1.2% (R2 ~ 0.8). Share of samples where beta2 is significant at 5%
(one-sided, Newey-West), for 2 years weekly, 2 years monthly and 10 years weekly.

    python scripts/power_simulation.py --out results
"""
import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from market_timing import plots  # noqa: E402,F401  (shared figure style)
from market_timing.models import henriksson_merton  # noqa: E402

PREMIUM, VOL, IDIO_W = 0.136, 0.125, 0.012


def power(beta2, T, per_year, reps, rng):
    mu, sd = PREMIUM / per_year, VOL / np.sqrt(per_year)
    idio = IDIO_W * np.sqrt(52 / per_year)
    hits = 0
    for _ in range(reps):
        x = mu + sd * rng.standard_normal(T)
        y = 0.85 * x + beta2 * np.maximum(x, 0) + idio * rng.standard_normal(T)
        out = henriksson_merton(pd.DataFrame({"x": x, "y": y}), ann=per_year)[0]
        hits += out["t_beta2"] > 1.645
    return hits / reps


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="results")
    p.add_argument("--reps", type=int, default=1000)
    p.add_argument("--plot-only", action="store_true", help="redraw the figure from the saved table")
    a = p.parse_args()
    if a.plot_only:
        plot(pd.read_csv(f"{a.out}/tables/power_simulation.csv", index_col=0), a.out)
        return
    rng = np.random.default_rng(0)
    grid = np.round(np.arange(0, 0.61, 0.05), 2)
    designs = {"2 years, weekly (T=104)": (104, 52), "2 years, monthly (T=24)": (24, 12),
               "10 years, weekly (T=520)": (520, 52)}
    tab = pd.DataFrame({k: [power(b, T, f, a.reps, rng) for b in grid] for k, (T, f) in designs.items()}, index=grid)
    tab.index.name = "beta2"
    os.makedirs(f"{a.out}/tables", exist_ok=True)
    os.makedirs(f"{a.out}/figures", exist_ok=True)
    tab.to_csv(f"{a.out}/tables/power_simulation.csv", float_format="%.3f")
    print(tab.round(2).to_string())
    plot(tab, a.out)


def plot(tab, out):
    fig, ax = plt.subplots(figsize=(9, 5.2))
    for (k, col), c in zip(tab.items(), ["#2a78d6", "#eda100", "#4a3aa7"]):
        ax.plot(tab.index, col, marker="o", lw=2.2, color=c, label=k)
    ax.axhline(0.05, color="#8a8984", ls=(0, (4, 3)), lw=1.2)
    ax.axhline(0.8, color="#8a8984", ls=(0, (4, 3)), lw=1.2)
    ax.text(0.6, 0.035, "5% (size)", ha="right", va="top", color="#52514e", fontsize=11)
    ax.text(0.0, 0.815, "80% (power)", ha="left", va="bottom", color="#52514e", fontsize=11)
    ax.set_xlabel("True timing β₂ (β up − β down)")
    ax.set_ylabel("Probability of detecting it (5%, one-sided)")
    ax.set_ylim(0, 1.02)
    ax.set_title("Power of the Henriksson-Merton test", loc="left", fontsize=14)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, fontsize=11.5)
    fig.tight_layout()
    fig.savefig(f"{out}/figures/fig7_power_simulation.png", dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    main()
