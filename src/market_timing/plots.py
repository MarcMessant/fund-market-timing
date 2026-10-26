"""Figures. One colour per fund (config.PALETTE) on every chart."""
from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.ticker import FuncFormatter, MultipleLocator  # noqa: E402

from .config import COMPONENTS, CRASH_WEEK, FUNDS, PALETTE, SHORT  # noqa: E402
from .models import henriksson_merton, treynor_mazuy  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 13, "font.family": "DejaVu Sans", "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 200,
})


def _pct(ax, axis="both", dec=0):
    fm = FuncFormatter(lambda v, _: f"{100 * v:.{dec}f}%")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(fm)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(fm)


def _save(fig, out, name):
    fig.savefig(os.path.join(out, name), bbox_inches="tight")
    plt.close(fig)


def regressions(W, out):
    """Weekly scatter with the fitted Treynor-Mazuy curve and Henriksson-Merton kinked line."""
    fig, axes = plt.subplots(1, len(FUNDS), figsize=(22, 5.2))
    crash = pd.Timestamp(CRASH_WEEK)
    for ax, f in zip(axes, FUNDS):
        r = W[f]
        t, rt = treynor_mazuy(r)
        h, rh = henriksson_merton(r)
        pt, ph = rt.params, rh.params
        ax.axhline(0, color=INK2, lw=0.8)
        ax.axvline(0, color=INK2, lw=0.8)
        lim = max(r.x.abs().max(), r.y.abs().max()) * 1.1
        xs = np.linspace(-lim, lim, 300)
        ax.plot(xs, xs, color=GRID, lw=1.5, ls=(0, (4, 3)), zorder=1)
        ax.scatter(r.x, r.y, s=34, color=PALETTE[f], alpha=0.75, edgecolor="white", linewidth=0.8, zorder=3)
        ax.plot(xs, pt["const"] + pt["x"] * xs + pt["x2"] * xs ** 2, color=INK, lw=2, zorder=4)
        ax.plot(xs, ph["const"] + ph["x"] * xs + ph["xp"] * np.maximum(xs, 0), color=INK, lw=2,
                ls=(0, (2, 2)), zorder=4)
        if crash in r.index:
            xc, yc = r.x[crash], r.y[crash]
            ax.scatter([xc], [yc], s=150, facecolor="none", edgecolor=INK, lw=1.6, zorder=5)
            ax.annotate("week to 9 Apr 25", (xc, yc), xytext=(12, 2), textcoords="offset points",
                        fontsize=10.5, color=INK2, va="center")
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        step = 0.02 if lim < 0.08 else 0.05
        ax.xaxis.set_major_locator(MultipleLocator(step))
        ax.yaxis.set_major_locator(MultipleLocator(step))
        _pct(ax)
        ax.set_title(f"{SHORT[f]}\nγ = {t['gamma']:.2f} (t = {t['t_gamma']:.2f})   "
                     f"β₂ = {h['beta2']:.2f} (t = {h['t_beta2']:.2f})", fontsize=12.5, color=INK, loc="left")
        ax.set_xlabel("Rm − Rf (weekly)")
    axes[0].set_ylabel("Rp − Rf (weekly)")
    leg = [Line2D([0], [0], color=INK, lw=2, label="Treynor-Mazuy (quadratic)"),
           Line2D([0], [0], color=INK, lw=2, ls=(0, (2, 2)), label="Henriksson-Merton (two betas)"),
           Line2D([0], [0], color=GRID, lw=1.5, ls=(0, (4, 3)), label="45° line (β = 1)")]
    fig.legend(handles=leg, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _save(fig, out, "fig1_regressions_weekly.png")


def coefficients(res, out):
    """Timing coefficients with 95% Newey-West CI, plus the same estimate for the other anchor days."""
    anch = res["anchor_day"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2))
    specs = [("gamma", "se_gamma", "Treynor-Mazuy γ", res["treynor_mazuy"]),
             ("beta2", "se_beta2", "Henriksson-Merton β₂", res["henriksson_merton"])]
    for ax, (coef, se, title, src) in zip(axes, specs):
        ax.axvline(0, color=INK2, lw=1)
        for i, f in enumerate(FUNDS[::-1]):
            est, s = src.loc[f, coef], src.loc[f, se]
            ax.plot([est - 1.96 * s, est + 1.96 * s], [i, i], color=PALETTE[f], lw=2.5, solid_capstyle="round")
            ax.scatter([est], [i], s=90, color=PALETTE[f], edgecolor="white", lw=2, zorder=4)
            other = anch[(anch.fund == f) & (anch.anchor != "Wed")][coef]
            ax.scatter(other, [i + 0.28] * len(other), s=34, facecolor="white", edgecolor=PALETTE[f], lw=1.4, zorder=3)
        ax.set_yticks(range(len(FUNDS)))
        ax.set_yticklabels([SHORT[f] for f in FUNDS[::-1]])
        ax.set_title(title, loc="left", fontsize=14, color=INK)
        ax.grid(axis="y", visible=False)
        ax.tick_params(axis="y", length=0)
    leg = [Line2D([0], [0], marker="o", color=INK2, lw=2.5, markersize=9, markeredgecolor="white",
                  label="Weekly Wed–Wed estimate, 95% CI (Newey-West)"),
           Line2D([0], [0], marker="o", ls="", markerfacecolor="white", markeredgecolor=INK2, markersize=7,
                  label="Same model, weeks ending Mon / Tue / Thu / Fri")]
    fig.legend(handles=leg, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, out, "fig2_timing_coefficients.png")


def _dumbbell(ax, lo, hi, lab_lo, lab_hi, title):
    ax.axvline(1, color=GRID, lw=1.5, ls=(0, (4, 3)))
    for i, f in enumerate(FUNDS[::-1]):
        a, b = lo[f], hi[f]
        ax.plot([a, b], [i, i], color=PALETTE[f], lw=2.5, alpha=0.6)
        ax.scatter([a], [i], s=110, marker="v", color=PALETTE[f], edgecolor="white", lw=1.5, zorder=4)
        ax.scatter([b], [i], s=110, marker="^", color=PALETTE[f], edgecolor="white", lw=1.5, zorder=4)
        ax.annotate(f"{a:.2f}", (a, i), xytext=(0, -17), textcoords="offset points", ha="center", fontsize=10.5, color=INK2)
        ax.annotate(f"{b:.2f}", (b, i), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=10.5, color=INK2)
    ax.set_yticks(range(len(FUNDS)))
    ax.set_yticklabels([SHORT[f] for f in FUNDS[::-1]])
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", visible=False)
    ax.set_title(title, loc="left", fontsize=14, color=INK)
    ax.set_ylim(-0.6, len(FUNDS) - 0.4)
    return [Line2D([0], [0], marker="v", ls="", color=INK2, markersize=9, label=lab_lo),
            Line2D([0], [0], marker="^", ls="", color=INK2, markersize=9, label=lab_hi)]


def up_down_betas(res, out):
    hm, mon = res["henriksson_merton"], res["monthly"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), sharex=True)
    h = _dumbbell(axes[0], hm.beta_down, hm.beta_up, "β in down markets", "β in up markets",
                  f"Henriksson-Merton, weekly ({int(hm.n.iloc[0])} weeks)")
    _dumbbell(axes[1], mon.beta_down, mon.beta_up, "", "", f"Henriksson-Merton, monthly ({int(mon.n.iloc[0])} months)")
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.04))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, out, "fig3_up_down_betas.png")


def april_2025(res, out):
    e = res["april_2025"]
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    h = _dumbbell(ax, e.beta_crash, e.beta_rebound, "Crash: 2 Apr → trough (8–9 Apr)", "Rebound: trough → 23 Apr",
                  "April 2025: implied beta (fund return / index return)")
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.05))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    _save(fig, out, "fig4_april_2025.png")


def _stacked(ax, df, comps, labels, colors, title):
    x = np.arange(len(FUNDS))
    w = 0.58
    pos, neg = np.zeros(len(FUNDS)), np.zeros(len(FUNDS))
    for c in comps:
        v = df.loc[FUNDS, c].values.astype(float)
        base = np.where(v >= 0, pos, neg)
        ax.bar(x, v, w, bottom=base, color=colors[c], edgecolor="white", linewidth=2, label=labels[c], zorder=3)
        for xi, vi, bi in zip(x, v, base):
            if abs(vi) >= 0.012:
                ax.text(xi, bi + vi / 2, f"{100 * vi:+.1f}", ha="center", va="center", fontsize=10.5, color=INK, zorder=5)
        pos, neg = np.where(v >= 0, pos + v, pos), np.where(v < 0, neg + v, neg)
    tot = df.loc[FUNDS, "excess_return"].values.astype(float)
    xt = x + w / 2 + 0.07
    ax.scatter(xt, tot, marker="D", s=80, color=INK, edgecolor="white", lw=1.5, zorder=6,
               label="Total excess return (sum)", clip_on=False)
    for xi, t in zip(xt, tot):
        ax.plot([xi - 0.07, xi], [t, t], color=INK, lw=1.5, zorder=5)
        ax.annotate(f"{100 * t:+.1f}%", (xi, t), xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=11.5, color=INK, weight="bold")
    ax.axhline(0, color=INK2, lw=1, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels([SHORT[f] for f in FUNDS])
    ax.tick_params(axis="x", length=0)
    for xi, f in zip(x, FUNDS):
        ax.add_patch(plt.Rectangle((xi - 0.15, -0.075), 0.3, 0.012, transform=ax.get_xaxis_transform(),
                                   color=PALETTE[f], clip_on=False))
    ax.grid(axis="x", visible=False)
    _pct(ax, "y")
    ax.set_ylabel("Annualised contribution")
    ax.set_title(title, loc="left", fontsize=14, color=INK)
    ax.set_xlim(-0.6, len(FUNDS) - 0.05)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False, fontsize=11.5)


def fama(res, out):
    order = ["investor_risk", "manager_risk", "diversification", "net_selectivity"]
    fig, ax = plt.subplots(figsize=(12, 6.2))
    labels = {"net_selectivity": "Net selectivity", "diversification": "Diversification (required return on specific risk)",
              "manager_risk": "Manager's risk (β − 1)", "investor_risk": "Investor's risk (target β = 1)"}
    _stacked(ax, res["fama"], order, labels, COMPONENTS, "Fama (1972) decomposition, weekly, annualised")
    _save(fig, out, "fig5_fama.png")

    b = res["bridge_hm"].rename(columns={"pure_alpha": "net_selectivity", "static_manager_risk": "manager_risk",
                                         "timing": "diversification"})
    labels = {"net_selectivity": "Pure selectivity (Henriksson-Merton α)",
              "diversification": "Timing (β₂ · E[max(0, Rm − Rf)])",
              "manager_risk": "Static manager's risk (β down − 1)", "investor_risk": "Investor's risk (target β = 1)"}
    fig, ax = plt.subplots(figsize=(12, 6.2))
    _stacked(ax, b, order, labels, COMPONENTS, "Fama with time-varying beta: timing isolated by Henriksson-Merton")
    _save(fig, out, "fig6_fama_timing_bridge.png")


def all_figures(res, out):
    os.makedirs(out, exist_ok=True)
    regressions(res["_weekly"], out)
    coefficients(res, out)
    up_down_betas(res, out)
    april_2025(res, out)
    fama(res, out)
