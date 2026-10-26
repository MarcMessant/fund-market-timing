"""Data loading and return construction.

Input: one Excel workbook, one sheet per fund, daily rows, nine columns in this order
(headers are ignored):

    Date | fund NAV | fund simple return | fund log return | benchmark level |
    benchmark simple return | benchmark log return | annualised risk-free rate |
    risk-free return over the interval

Only the date, NAV, benchmark level and interval risk-free return are used: every return is
rebuilt from levels so that weekly and monthly returns are exact compounded returns.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import END, START, Settings

COLUMNS = ["Date", "NAV", "rp", "lp", "B", "rm", "lm", "rf_ann", "rf"]


class FundData:
    """Daily total-return index of the fund, benchmark level and risk-free index."""

    def __init__(self, path: str, settings: Settings | None = None):
        self.path = path
        self.settings = settings or Settings()
        self._cache: dict[str, pd.DataFrame] = {}

    def load(self, fund: str) -> pd.DataFrame:
        if fund not in self._cache:
            self._cache[fund] = self._load(fund)
        return self._cache[fund]

    def _load(self, fund: str) -> pd.DataFrame:
        d = pd.read_excel(self.path, sheet_name=fund)
        if d.shape[1] != len(COLUMNS):
            raise ValueError(f"Sheet {fund!r}: expected {len(COLUMNS)} columns, got {d.shape[1]}")
        d.columns = COLUMNS
        d = d.set_index("Date").sort_index()
        tr = d.NAV.pct_change()
        # Reinvest cash distributions at the ex-date: r = (NAV_t + D) / NAV_{t-1} - 1
        for dt, amount in self.settings.distributions.get(fund, {}).items():
            dt = pd.Timestamp(dt)
            if dt in d.index:
                tr.loc[dt] = (d.NAV.loc[dt] + amount) / d.NAV.shift(1).loc[dt] - 1
        d["TR"] = (1 + tr.fillna(0)).cumprod()
        d["RF_IDX"] = (1 + d.rf.fillna(0)).cumprod()
        return d[["NAV", "TR", "B", "RF_IDX", "rf_ann"]]

    # ------------------------------------------------------------------ return series
    def weekly(self, fund, start=START, end=END, weekday=2, fund_shift=0):
        d = self.load(fund)
        dates = weekly_dates(d.index, start, end, weekday)
        return returns_on(d, dates, fund_shift)

    def daily(self, fund, start=START, end=END):
        d = self.load(fund)
        dd = d.loc[:end]
        first = dd.index[dd.index <= pd.Timestamp(start)].max()
        return returns_on(d, dd.loc[first:].index)

    def monthly(self, fund, start=START, end=END, day=22):
        """Monthly returns anchored on the given day of the month (last available date on or before it)."""
        d = self.load(fund)
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        anchors = pd.date_range(s, e, freq="MS") + pd.Timedelta(days=day - 1)
        anchors = [s] + [a for a in anchors if s < a <= e]
        idx = d.index
        dates = pd.DatetimeIndex([idx[idx <= a].max() for a in anchors])
        return returns_on(d, dates)


def weekly_dates(idx: pd.DatetimeIndex, start=START, end=END, weekday=2) -> pd.DatetimeIndex:
    """Last available date on or before each anchor weekday (0 = Monday, 2 = Wednesday).

    Handles holidays: if the Wednesday is closed, the previous business day is used.
    """
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    w0 = s - pd.Timedelta(days=(s.weekday() - weekday) % 7)
    w1 = e - pd.Timedelta(days=(e.weekday() - weekday) % 7)
    anchors = pd.date_range(w0, w1, freq="7D")
    return pd.DatetimeIndex([idx[idx <= a].max() for a in anchors])


def returns_on(d: pd.DataFrame, dates: pd.DatetimeIndex, fund_shift: int = 0) -> pd.DataFrame:
    """Compounded simple returns between consecutive dates.

    Columns: Rp, Rm, Rf, y = Rp - Rf, x = Rm - Rf.
    fund_shift=1 reads the fund NAV one business day after each date (asynchronous NAV).
    """
    pos = d.index.get_indexer(dates)
    nav = d.TR.iloc[pos + fund_shift].values
    b = d.B.iloc[pos].values
    rfi = d.RF_IDX.iloc[pos].values
    r = pd.DataFrame({"Rp": nav[1:] / nav[:-1] - 1,
                      "Rm": b[1:] / b[:-1] - 1,
                      "Rf": rfi[1:] / rfi[:-1] - 1}, index=dates[1:])
    r["y"] = r.Rp - r.Rf
    r["x"] = r.Rm - r.Rf
    return r
