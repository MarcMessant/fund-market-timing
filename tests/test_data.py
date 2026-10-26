"""Return construction: calendar, compounding, distributions; full pipeline on synthetic data."""
import numpy as np
import pandas as pd
import pytest

from market_timing import FundData, Settings
from market_timing.analysis import check_passive_control, run
from market_timing.data import returns_on, weekly_dates


def test_weekly_dates_fall_back_on_holidays():
    idx = pd.bdate_range("2024-12-16", "2025-01-10").drop(pd.to_datetime(["2024-12-25", "2025-01-01"]))
    dates = weekly_dates(idx, "2024-12-18", "2025-01-08")
    # Wednesdays 25/12 and 01/01 are closed: the previous business day is used
    assert list(dates.strftime("%Y-%m-%d")) == ["2024-12-18", "2024-12-24", "2024-12-31", "2025-01-08"]


def test_weekly_returns_compound_daily_returns():
    idx = pd.bdate_range("2025-01-01", periods=30)
    rng = np.random.default_rng(0)
    d = pd.DataFrame({"TR": np.cumprod(1 + 0.01 * rng.standard_normal(30)),
                      "B": np.cumprod(1 + 0.01 * rng.standard_normal(30)),
                      "RF_IDX": np.cumprod(np.full(30, 1.0001))}, index=idx)
    w = returns_on(d, idx[::5])
    daily = d.TR.pct_change()
    assert w.Rp.iloc[0] == pytest.approx(np.prod(1 + daily.iloc[1:6]) - 1)
    assert np.allclose(w.y, w.Rp - w.Rf) and np.allclose(w.x, w.Rm - w.Rf)


def test_distribution_is_reinvested(synthetic_path):
    raw = FundData(synthetic_path, Settings.raw()).load("VICEX")
    dt = raw.index[100]
    adj = FundData(synthetic_path, Settings(distributions={"VICEX": {str(dt.date()): 1.0}})).load("VICEX")
    r_raw = raw.TR.loc[dt] / raw.TR.shift(1).loc[dt] - 1
    r_adj = adj.TR.loc[dt] / adj.TR.shift(1).loc[dt] - 1
    assert r_adj - r_raw == pytest.approx(1.0 / raw.NAV.shift(1).loc[dt])


def test_full_pipeline_on_synthetic_data(synthetic_path):
    res = run(FundData(synthetic_path, Settings.raw()))
    check_passive_control(res)
    assert res["treynor_mazuy"].shape[0] == 5
    assert (res["descriptive"].n == 104).all()
