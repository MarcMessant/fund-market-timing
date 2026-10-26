"""The Fama decomposition and the Fama-to-timing bridges add up exactly."""
import numpy as np
import pandas as pd
import pytest

from market_timing.fama import bridge_hm, bridge_tm, fama


@pytest.fixture
def sample():
    rng = np.random.default_rng(7)
    n = 104
    rf = np.full(n, 0.0006)
    x = 0.002 + 0.02 * rng.standard_normal(n)
    y = 0.0005 + np.where(x > 0, 0.9, 0.7) * x + 0.01 * rng.standard_normal(n)
    return pd.DataFrame({"Rp": y + rf, "Rm": x + rf, "Rf": rf, "y": y, "x": x})


@pytest.mark.parametrize("beta_target", [1.0, 0.8])
def test_fama_adds_up(sample, beta_target):
    out = fama(sample, beta_target)
    assert abs(out["check"]) < 1e-14
    assert out["selectivity"] == pytest.approx(out["net_selectivity"] + out["diversification"])
    assert out["manager_risk"] + out["investor_risk"] == pytest.approx(out["beta"] * out["market_premium"])


def test_fama_on_the_index_itself(sample):
    r = sample.assign(Rp=sample.Rm, y=sample.x)
    out = fama(r)
    assert out["beta"] == pytest.approx(1)
    for k in ("selectivity", "diversification", "manager_risk"):
        assert out[k] == pytest.approx(0, abs=1e-12)


@pytest.mark.parametrize("bridge", [bridge_hm, bridge_tm])
def test_bridges_are_exact_ols_identities(sample, bridge):
    assert abs(bridge(sample)["check"]) < 1e-14
