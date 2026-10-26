"""Full study: main estimates, robustness checks, April 2025 event study and Fama decomposition.

`run(data)` returns a dict of DataFrames (one row per fund, or per fund x specification).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CRASH_WEEK, EPISODE, FUNDS, PASSIVE_CONTROL, PRE_WINDOW, BENCH, CCY
from .data import FundData, returns_on, weekly_dates
from .fama import bridge_hm, bridge_tm, fama
from .models import (capm, capture, dimson, henriksson_merton, nw_lags, treynor_mazuy,
                     treynor_mazuy_asym)

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]


def _frame(rows: dict) -> pd.DataFrame:
    df = pd.DataFrame(rows).T
    df.index.name = "fund"
    return df.infer_objects()


def descriptive(data: FundData, W: dict) -> pd.DataFrame:
    rows = {}
    for f in FUNDS:
        r = W[f]
        c = capm(r)[0]
        rows[f] = dict(currency=CCY[f], benchmark=BENCH[f], n=len(r), n_up=int((r.x > 0).sum()),
                       cum_fund=(1 + r.Rp).prod() - 1, cum_bench=(1 + r.Rm).prod() - 1,
                       vol_fund=r.Rp.std() * np.sqrt(52), vol_bench=r.Rm.std() * np.sqrt(52),
                       beta=c["beta"], R2=c["R2"], alpha_ann=c["alpha_ann"], t_alpha=c["t_alpha"],
                       **capture(r))
    return _frame(rows)


def anchor_sensitivity(data: FundData) -> pd.DataFrame:
    """Same weekly models, with weeks ending Monday ... Friday."""
    rows = []
    for f in FUNDS:
        d = data.load(f)
        for wd, name in enumerate(WEEKDAYS):
            r = returns_on(d, weekly_dates(d.index, weekday=wd))
            t, a, h = treynor_mazuy(r)[0], treynor_mazuy_asym(r)[0], henriksson_merton(r)[0]
            rows.append(dict(fund=f, anchor=name, n=len(r), gamma=t["gamma"], t_gamma=t["t_gamma"],
                             beta2=h["beta2"], t_beta2=h["t_beta2"],
                             beta_down=h["beta_down"], beta_up=h["beta_up"],
                             gamma_up=a["gamma_up"], t_gamma_up=a["t_gamma_up"],
                             gamma_down=a["gamma_down"], t_gamma_down=a["t_gamma_down"]))
    return pd.DataFrame(rows)


def influence(W: dict) -> pd.DataFrame:
    """Most influential week for gamma (DFBETAS) and estimates without the April 2025 crash weeks."""
    drop = pd.to_datetime([CRASH_WEEK, (pd.Timestamp(CRASH_WEEK) + pd.Timedelta(days=7)).strftime("%Y-%m-%d")])
    rows = []
    for f in FUNDS:
        r = W[f]
        dfb = pd.Series(treynor_mazuy(r)[1].get_influence().dfbetas[:, 2], index=r.index)
        k = dfb.abs().idxmax()
        rr = r.drop(drop, errors="ignore")
        t, a, h = treynor_mazuy(rr)[0], treynor_mazuy_asym(rr)[0], henriksson_merton(rr)[0]
        rows.append(dict(fund=f, max_dfbetas_week=k.date(), max_dfbetas=dfb[k], n_ex_crash=len(rr),
                         gamma_ex_crash=t["gamma"], t_gamma_ex_crash=t["t_gamma"],
                         gamma_up_ex_crash=a["gamma_up"], t_gamma_up_ex_crash=a["t_gamma_up"],
                         gamma_down_ex_crash=a["gamma_down"], t_gamma_down_ex_crash=a["t_gamma_down"],
                         beta2_ex_crash=h["beta2"], t_beta2_ex_crash=h["t_beta2"]))
    return pd.DataFrame(rows).set_index("fund")


def dimson_table(data: FundData, W: dict) -> pd.DataFrame:
    rows = []
    for f in FUNDS:
        rd = data.daily(f)
        for spec, r, K, ann in [("weekly, K=1", W[f], 1, 52), ("daily, K=0", rd, 0, 252),
                                ("daily, K=1", rd, 1, 252), ("daily, K=2", rd, 2, 252)]:
            t = dimson(r, K, ann, model="tm")[0]
            h = dimson(r, K, ann, model="hm")[0]
            rows.append(dict(fund=f, spec=spec, n=t["n"], nw_lags=nw_lags(t["n"]), beta_sum=t["beta_sum"],
                             gamma_sum=t["timing_coef_sum"], t_gamma_sum=t["t_timing_sum"],
                             timing_TM_ann=t["timing_ann"], beta2_sum=h["timing_coef_sum"],
                             t_beta2_sum=h["t_timing_sum"], timing_HM_ann=h["timing_ann"]))
    return pd.DataFrame(rows)


def monthly_table(data: FundData) -> pd.DataFrame:
    rows = {}
    for f in FUNDS:
        r = data.monthly(f)
        t, h = treynor_mazuy(r, ann=12)[0], henriksson_merton(r, ann=12)[0]
        rows[f] = dict(n=len(r), beta=t["beta"], gamma=t["gamma"], t_gamma=t["t_gamma"], p_gamma=t["p_gamma"],
                       beta_down=h["beta_down"], beta_up=h["beta_up"], beta2=h["beta2"], t_beta2=h["t_beta2"],
                       p_beta2=h["p_beta2"], timing_HM_ann=h["timing_ann"], R2=t["R2"], **capture(r))
    return _frame(rows)


def april_2025(data: FundData) -> pd.DataFrame:
    """Implied beta (fund return / index return) during the crash and during the rebound."""
    rows = {}
    s, e = pd.Timestamp(EPISODE["start"]), pd.Timestamp(EPISODE["end"])
    for f in FUNDS:
        d = data.load(f)
        trough = d.B.loc[s - pd.Timedelta(days=18): s + pd.Timedelta(days=28)].idxmin()
        lag = data.settings.nav_lag.get(f, 0)
        loc = d.index.get_loc

        def ret(series, a, b, l=0):
            return series.iloc[loc(b) + l] / series.iloc[loc(a) + l] - 1

        peak = d.B.loc[s - pd.Timedelta(days=91): s + pd.Timedelta(days=13)].max()
        rows[f] = dict(trough=trough.date(), bench_drawdown=d.B[trough] / peak - 1,
                       bench_crash=ret(d.B, s, trough), fund_crash=ret(d.TR, s, trough, lag),
                       bench_rebound=ret(d.B, trough, e), fund_rebound=ret(d.TR, trough, e, lag))
    t = _frame(rows)
    t["beta_crash"] = t.fund_crash / t.bench_crash
    t["beta_rebound"] = t.fund_rebound / t.bench_rebound
    return t


def pre_window_beta(data: FundData, fund: str) -> float:
    return capm(data.weekly(fund, start=PRE_WINDOW[0], end=PRE_WINDOW[1]))[0]["beta"]


def run(data: FundData) -> dict:
    W = {f: data.weekly(f) for f in FUNDS}
    out = dict(
        descriptive=descriptive(data, W),
        treynor_mazuy=_frame({f: treynor_mazuy(W[f])[0] for f in FUNDS}),
        treynor_mazuy_asym=_frame({f: treynor_mazuy_asym(W[f])[0] for f in FUNDS}),
        henriksson_merton=_frame({f: henriksson_merton(W[f])[0] for f in FUNDS}),
        april_2025=april_2025(data),
        anchor_day=anchor_sensitivity(data),
        influence=influence(W),
        dimson=dimson_table(data, W),
        monthly=monthly_table(data),
        fama=_frame({f: fama(W[f]) for f in FUNDS}),
        fama_monthly=_frame({f: fama(data.monthly(f), ann=12) for f in FUNDS}),
        fama_pre_window_beta=_frame({f: fama(W[f], pre_window_beta(data, f)) for f in FUNDS}),
        bridge_hm=_frame({f: bridge_hm(W[f]) for f in FUNDS}),
        bridge_tm=_frame({f: bridge_tm(W[f]) for f in FUNDS}),
    )
    for k in ("fama", "fama_monthly", "fama_pre_window_beta", "bridge_hm", "bridge_tm"):
        assert out[k]["check"].astype(float).abs().max() < 1e-12, f"{k}: decomposition does not add up"
    out["_weekly"] = W
    return out


def check_passive_control(res: dict, fund: str = PASSIVE_CONTROL, tol_beta=0.02, tol_timing=0.005) -> None:
    """The passive ETF must show beta ~ 1 and no economically meaningful timing.

    The test is economic, not statistical: with R2 ~ 1 the standard errors are tiny and a timing
    coefficient worth 0.01% a year can still have |t| > 2.
    """
    tm, hm = res["treynor_mazuy"].loc[fund], res["henriksson_merton"].loc[fund]
    assert abs(tm.beta - 1) < tol_beta, f"control beta = {tm.beta:.3f}"
    assert abs(tm.timing_ann) < tol_timing, f"control TM timing = {tm.timing_ann:.4f} per year"
    assert abs(hm.timing_ann) < tol_timing, f"control HM timing = {hm.timing_ann:.4f} per year"
