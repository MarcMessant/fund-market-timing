"""Generate a synthetic workbook with the same layout as the real data set.

The real data (Bloomberg) cannot be redistributed. This file lets anyone run the full pipeline.
Each synthetic fund has a known timing profile, so the output can be checked against the truth:

    VICEX               defensive, no timing          beta 0.5
    iShares ACWI        passive control               beta 1, tracking error ~0.15% a year
    ODDO High Dividend  no timing                     beta 0.85
    Fundsmith           negative timing (HM)          beta_down 0.95, beta_up 0.85
    Comgest             positive timing (HM)          beta_down 0.80, beta_up 0.90

Timing is generated at the daily frequency, so even a 0.10 gap between the two betas is worth
several points of return per year.

    python scripts/make_synthetic_data.py --out data/synthetic_fund_data.xlsx
"""
import argparse

import numpy as np
import pandas as pd

TRUTH = {  # (alpha per year, beta_down, beta_up, idiosyncratic daily vol)
    "VICEX": (0.00, 0.50, 0.50, 0.009),
    "iShares ACWI": (0.00, 1.00, 1.00, 0.0001),
    "ODDO High Dividend": (0.00, 0.85, 0.85, 0.004),
    "Fundsmith": (0.00, 0.95, 0.85, 0.006),
    "Comgest": (0.00, 0.80, 0.90, 0.006),
}
COLUMNS = ["Date", "Fund NAV", "Fund simple return", "Fund log return", "Benchmark level",
           "Benchmark simple return", "Benchmark log return", "Risk-free rate (annualised)",
           "Risk-free return over the interval"]


def simulate(seed=42, start="2024-01-02", end="2026-09-22"):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, end)
    n = len(dates)
    rf_ann = np.full(n, 0.035)
    rf = np.r_[np.nan, rf_ann[1:] * np.diff(dates).astype("timedelta64[D]").astype(int) / 360]

    # Benchmark: Student-t shocks, plus a stylised crash and rebound in April 2025.
    rm = 0.0004 + 0.009 * rng.standard_t(5, n) / np.sqrt(5 / 3)
    crash = (dates >= "2025-04-03") & (dates <= "2025-04-08")
    rebound = (dates >= "2025-04-09") & (dates <= "2025-04-16")
    rm[crash] = -0.03
    rm[rebound] = 0.018
    rm[0] = np.nan

    sheets = {}
    for fund, (alpha, b_dn, b_up, vol) in TRUTH.items():
        x = rm - np.nan_to_num(rf)
        beta = np.where(x > 0, b_up, b_dn)
        rp = np.nan_to_num(rf) + alpha / 252 + beta * x + vol * rng.standard_normal(n)
        rp[0] = np.nan
        nav = 100 * np.cumprod(1 + np.nan_to_num(rp))
        lvl = 1000 * np.cumprod(1 + np.nan_to_num(rm))
        sheets[fund] = pd.DataFrame({
            COLUMNS[0]: dates, COLUMNS[1]: nav, COLUMNS[2]: rp, COLUMNS[3]: np.log1p(rp),
            COLUMNS[4]: lvl, COLUMNS[5]: rm, COLUMNS[6]: np.log1p(rm),
            COLUMNS[7]: rf_ann, COLUMNS[8]: rf})
    return sheets


def write(path, seed=42):
    import os
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, df in simulate(seed).items():
            df.to_excel(xw, sheet_name=name, index=False)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/synthetic_fund_data.xlsx")
    p.add_argument("--seed", type=int, default=42)
    a = p.parse_args()
    write(a.out, a.seed)
    print(f"Synthetic data written to {a.out}")
