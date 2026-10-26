"""Market-timing regressions with Newey-West (HAC) standard errors.

Notation: y = Rp - Rf (fund excess return), x = Rm - Rf (benchmark excess return).

- CAPM               y = a + b x
- Treynor-Mazuy      y = a + b x + g x^2                         timing if g > 0
- TM, asymmetric     y = a + b x + g_up x^2 1{x>0} + g_dn x^2 1{x<=0}
- Henriksson-Merton  y = a + b1 x + b2 max(0, x)                 timing if b2 > 0
                     beta in down markets = b1, beta in up markets = b1 + b2
- Dimson              same models with K lags of x; contemporaneous and lagged coefficients are summed

Economic value of timing (annualised average contribution of the timing term):
    TM: g * mean(x^2) * ann        HM: b2 * mean(max(0, x)) * ann
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def nw_lags(T: int) -> int:
    """Newey-West rule of thumb: floor(4 (T/100)^(2/9)). 104 weeks -> 4, 24 months -> 2."""
    return int(np.floor(4 * (T / 100) ** (2 / 9)))


def ols_hac(y, X, lags=None):
    lags = nw_lags(len(y)) if lags is None else lags
    return sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})


def _corr(res, a, b):
    c = res.cov_params()
    return c.loc[a, b] / np.sqrt(c.loc[a, a] * c.loc[b, b])


def capm(r, ann=52, lags=None):
    res = ols_hac(r.y, r[["x"]], lags)
    return dict(alpha_ann=res.params["const"] * ann, t_alpha=res.tvalues["const"],
                beta=res.params["x"], R2=res.rsquared), res


def treynor_mazuy(r, ann=52, lags=None):
    X = pd.DataFrame({"x": r.x, "x2": r.x ** 2})
    res = ols_hac(r.y, X, lags)
    a, g = res.params["const"], res.params["x2"]
    timing = g * (r.x ** 2).mean() * ann
    return dict(n=len(r), alpha_ann=a * ann, t_alpha=res.tvalues["const"],
                beta=res.params["x"], t_beta=res.tvalues["x"],
                gamma=g, se_gamma=res.bse["x2"], t_gamma=res.tvalues["x2"], p_gamma=res.pvalues["x2"],
                R2=res.rsquared, timing_ann=timing, corr_alpha_gamma=_corr(res, "const", "x2")), res


def treynor_mazuy_asym(r, ann=52, lags=None):
    """Separate convexity in up and down markets, common beta."""
    up = (r.x > 0).astype(float)
    X = pd.DataFrame({"x": r.x, "x2_up": r.x ** 2 * up, "x2_dn": r.x ** 2 * (1 - up)})
    res = ols_hac(r.y, X, lags)
    names = list(res.params.index)
    w = np.zeros(len(names))
    w[names.index("x2_up")], w[names.index("x2_dn")] = 1, -1
    gu, gd = res.params["x2_up"], res.params["x2_dn"]
    return dict(n=len(r), n_up=int(up.sum()), n_down=int((1 - up).sum()),
                alpha_ann=res.params["const"] * ann, t_alpha=res.tvalues["const"], beta=res.params["x"],
                gamma_up=gu, t_gamma_up=res.tvalues["x2_up"], p_gamma_up=res.pvalues["x2_up"],
                gamma_down=gd, t_gamma_down=res.tvalues["x2_dn"], p_gamma_down=res.pvalues["x2_dn"],
                p_equal=float(res.t_test(w).pvalue),
                timing_up_ann=gu * (r.x ** 2 * up).mean() * ann,
                timing_down_ann=gd * (r.x ** 2 * (1 - up)).mean() * ann,
                R2=res.rsquared), res


def henriksson_merton(r, ann=52, lags=None):
    X = pd.DataFrame({"x": r.x, "xp": np.maximum(r.x, 0)})
    res = ols_hac(r.y, X, lags)
    b1, b2 = res.params["x"], res.params["xp"]
    up = res.t_test(np.array([0, 1, 1.0]))
    timing = b2 * np.maximum(r.x, 0).mean() * ann
    return dict(n=len(r), alpha_ann=res.params["const"] * ann, t_alpha=res.tvalues["const"],
                beta_down=b1, t_beta_down=res.tvalues["x"],
                beta_up=float(np.squeeze(up.effect)), t_beta_up=float(np.squeeze(up.tvalue)),
                beta2=b2, se_beta2=res.bse["xp"], t_beta2=res.tvalues["xp"], p_beta2=res.pvalues["xp"],
                R2=res.rsquared, timing_ann=timing, corr_alpha_beta2=_corr(res, "const", "xp")), res


def capture(r):
    """Average fund return / average benchmark return, over up weeks and down weeks."""
    up, dn = r.x > 0, r.x <= 0
    return dict(capture_up=r.Rp[up].mean() / r.Rm[up].mean(),
                capture_down=r.Rp[dn].mean() / r.Rm[dn].mean())


def dimson(r, K=1, ann=252, lags=None, model="tm"):
    """Timing regression with K lags of the market (Dimson, 1979). Returns summed coefficients."""
    X = {}
    for k in range(K + 1):
        xk = r.x.shift(k)
        X[f"x_{k}"] = xk
        X[f"q_{k}"] = xk ** 2 if model == "tm" else np.maximum(xk, 0)
    X = pd.DataFrame(X).dropna()
    y = r.y.loc[X.index]
    res = ols_hac(y, X, lags)
    names = list(res.params.index)

    def summed(prefix):
        t = res.t_test(np.array([1.0 if n.startswith(prefix) else 0.0 for n in names]))
        return float(np.squeeze(t.effect)), float(np.squeeze(t.tvalue))

    beta_sum, t_beta = summed("x_")
    coef_sum, t_coef = summed("q_")
    xs = r.x.loc[X.index]
    f = (lambda v: v ** 2) if model == "tm" else (lambda v: np.maximum(v, 0))
    timing = sum(res.params[f"q_{k}"] * f(xs.shift(k)).mean() for k in range(K + 1)) * ann
    return dict(n=len(y), beta_sum=beta_sum, t_beta_sum=t_beta, timing_coef_sum=coef_sum,
                t_timing_sum=t_coef, timing_ann=timing, R2=res.rsquared), res


def stars(p: float) -> str:
    """Significance stars, R convention: *** 0.1 %, ** 1 %, * 5 %, . 10 %."""
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "." if p < 0.1 else ""
