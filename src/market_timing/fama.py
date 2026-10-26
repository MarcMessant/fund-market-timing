"""Fama (1972) performance decomposition and its bridge to the timing models.

Annualised arithmetic means (weekly mean x 52). With prem = Rm - Rf, beta from the CAPM,
beta_T the target beta and beta_total = sigma_p / sigma_m:

    excess return  = selectivity + risk
    selectivity    = (Rp - Rf) - beta * prem                (Jensen's alpha)
                   = net selectivity + diversification
    diversification = (beta_total - beta) * prem            (return required for specific risk)
    risk           = beta * prem = manager risk + investor risk
    manager risk   = (beta - beta_T) * prem
    investor risk  = beta_T * prem

Fama assumes a constant beta, so it cannot see timing. Re-estimating the mean excess return with
Henriksson-Merton (or Treynor-Mazuy) gives an exact OLS identity (residuals have zero mean):

    mean(y) = alpha_HM + beta_T * mean(x) + (beta_down - beta_T) * mean(x) + beta2 * mean(max(0, x))
"""
from __future__ import annotations

import numpy as np

from .models import capm, henriksson_merton, treynor_mazuy


def fama(r, beta_target=1.0, ann=52):
    Rp, Rm, Rf = r.Rp.mean() * ann, r.Rm.mean() * ann, r.Rf.mean() * ann
    beta = capm(r, ann)[0]["beta"]
    prem = Rm - Rf
    total = Rp - Rf
    selectivity = total - beta * prem
    beta_total = r.Rp.std() / r.Rm.std()
    diversification = (beta_total - beta) * prem
    out = dict(beta=beta, beta_total=beta_total, beta_target=beta_target, market_premium=prem,
               excess_return=total, selectivity=selectivity,
               net_selectivity=selectivity - diversification, diversification=diversification,
               manager_risk=(beta - beta_target) * prem, investor_risk=beta_target * prem)
    out["check"] = total - (out["net_selectivity"] + diversification + out["manager_risk"] + out["investor_risk"])
    return out


def bridge_hm(r, beta_target=1.0, ann=52):
    _, res = henriksson_merton(r, ann)
    a, b1, b2 = res.params["const"] * ann, res.params["x"], res.params["xp"]
    xbar = r.x.mean() * ann
    out = dict(excess_return=r.y.mean() * ann, pure_alpha=a, investor_risk=beta_target * xbar,
               static_manager_risk=(b1 - beta_target) * xbar,
               timing=b2 * np.maximum(r.x, 0).mean() * ann)
    out["check"] = out["excess_return"] - (a + out["investor_risk"] + out["static_manager_risk"] + out["timing"])
    return out


def bridge_tm(r, beta_target=1.0, ann=52):
    _, res = treynor_mazuy(r, ann)
    a, b, g = res.params["const"] * ann, res.params["x"], res.params["x2"]
    xbar = r.x.mean() * ann
    out = dict(excess_return=r.y.mean() * ann, pure_alpha=a, investor_risk=beta_target * xbar,
               static_manager_risk=(b - beta_target) * xbar, timing=g * (r.x ** 2).mean() * ann)
    out["check"] = out["excess_return"] - (a + out["investor_risk"] + out["static_manager_risk"] + out["timing"])
    return out
