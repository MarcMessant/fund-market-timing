"""Run the whole study: estimates, robustness checks, figures and result tables.

    python scripts/run_analysis.py --data data/fund_data.xlsx --out results
    python scripts/run_analysis.py --data data/synthetic_fund_data.xlsx --out results_synthetic --raw
"""
import argparse
import warnings

from market_timing import FundData, Settings
from market_timing.analysis import check_passive_control, run
from market_timing.plots import all_figures
from market_timing.report import export

warnings.filterwarnings("ignore", category=FutureWarning)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", required=True, help="Excel workbook, one sheet per fund")
    p.add_argument("--out", default="results", help="output folder")
    p.add_argument("--raw", action="store_true",
                   help="no data adjustment (no reinvested distributions, no NAV lag); use with synthetic data")
    a = p.parse_args()

    data = FundData(a.data, Settings.raw() if a.raw else Settings())
    res = run(data)
    check_passive_control(res)
    print("Passive control OK: beta ~ 1, timing value ~ 0.")

    cols = ["gamma", "t_gamma", "timing_ann"]
    print("\nTreynor-Mazuy (weekly)\n", res["treynor_mazuy"][cols].round(3).to_string())
    cols = ["beta_down", "beta_up", "beta2", "t_beta2", "timing_ann"]
    print("\nHenriksson-Merton (weekly)\n", res["henriksson_merton"][cols].round(3).to_string())

    export(res, a.out)
    all_figures(res, f"{a.out}/figures")
    print(f"\nTables and figures written to {a.out}/")


if __name__ == "__main__":
    main()
