"""The estimators recover known parameters on simulated weekly data."""
import numpy as np
import pandas as pd
import pytest

from market_timing.models import (capm, dimson, henriksson_merton, nw_lags, treynor_mazuy,
                                  treynor_mazuy_asym)

N = 5000


def weekly_sample(seed, y_of_x, noise=0.01):
    rng = np.random.default_rng(seed)
    x = 0.002 + 0.025 * rng.standard_normal(N)
    rf = np.full(N, 0.0007)
    y = y_of_x(x) + noise * rng.standard_normal(N)
    return pd.DataFrame({"x": x, "y": y, "Rm": x + rf, "Rp": y + rf, "Rf": rf})


def test_newey_west_lags():
    assert nw_lags(104) == 4 and nw_lags(24) == 2 and nw_lags(464) == 5


def test_capm_recovers_alpha_and_beta():
    r = weekly_sample(0, lambda x: 0.001 + 0.8 * x)
    out = capm(r)[0]
    assert out["beta"] == pytest.approx(0.8, abs=0.01)
    assert out["alpha_ann"] == pytest.approx(0.052, abs=0.01)


def test_treynor_mazuy_recovers_gamma():
    r = weekly_sample(1, lambda x: 0.9 * x + 3.0 * x ** 2)
    out = treynor_mazuy(r)[0]
    assert abs(out["gamma"] - 3.0) < 3 * out["se_gamma"]
    assert out["t_gamma"] > 5


def test_henriksson_merton_recovers_two_betas():
    r = weekly_sample(2, lambda x: np.where(x > 0, 1.2, 0.7) * x)
    out = henriksson_merton(r)[0]
    assert out["beta_down"] == pytest.approx(0.7, abs=0.03)
    assert out["beta_up"] == pytest.approx(1.2, abs=0.03)
    assert out["beta2"] == pytest.approx(0.5, abs=0.05)
    # value of timing = beta2 * E[max(0, x)] * 52
    assert out["timing_ann"] == pytest.approx(out["beta2"] * np.maximum(r.x, 0).mean() * 52)


def test_asymmetric_tm_signs():
    # convex in up markets, concave in down markets
    r = weekly_sample(3, lambda x: x + np.where(x > 0, 4.0, -4.0) * x ** 2)
    out = treynor_mazuy_asym(r)[0]
    assert out["gamma_up"] > 0 > out["gamma_down"]
    assert out["p_equal"] < 0.001


def test_no_timing_gives_no_signal():
    r = weekly_sample(4, lambda x: x)
    assert abs(treynor_mazuy(r)[0]["t_gamma"]) < 3
    assert abs(henriksson_merton(r)[0]["t_beta2"]) < 3


def test_dimson_sums_lagged_betas():
    rng = np.random.default_rng(5)
    x = pd.Series(0.01 * rng.standard_normal(N))
    y = 0.5 * x + 0.3 * x.shift(1).fillna(0) + 0.002 * rng.standard_normal(N)
    r = pd.DataFrame({"x": x, "y": y})
    assert dimson(r, K=1, model="tm")[0]["beta_sum"] == pytest.approx(0.8, abs=0.02)
    assert dimson(r, K=0, model="tm")[0]["beta_sum"] == pytest.approx(0.5, abs=0.02)
