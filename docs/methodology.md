# Methodology

## 1. Sample and returns

| Choice | Value | Why |
|---|---|---|
| Window | 104 weeks, 18 Sep 2024 to 16 Sep 2026 (last Wednesday on or before 22 Sep 2026) | Two most recent years; contains a sharp bear phase (April 2025 tariff shock, benchmarks −13% to −17%) and a strong rally, so both regimes are observed |
| Frequency | Weekly, Wednesday to Wednesday; last available date if the Wednesday is a holiday | Daily data are distorted by asynchronous NAVs (Fundsmith); monthly data give only 24 points |
| Returns | Simple, compounded from levels | The models are written in simple excess returns |
| Risk-free | Compounded "risk-free return over the interval" (SOFR, €STR, SONIA) | Same currency as fund and benchmark |
| Variables | y = Rp − Rf, x = Rm − Rf | |
| Up / down market | Up week if x > 0 (59 to 62 up weeks out of 104, depending on the index) | Definition built into Henriksson-Merton: the manager chooses between the market and cash |
| Standard errors | Newey-West, lags = floor(4 (T/100)^(2/9)): 4 weekly, 2 monthly, 5 daily | |

## 2. Models

**CAPM.** y = α + β x + ε. Gives the static beta and Jensen's alpha.

**Treynor-Mazuy (1966).** y = α + β x + γ x² + ε.
A manager who raises beta before up markets and cuts it before down markets produces a convex relation: γ > 0. Local slope: β + 2γx.

**Asymmetric Treynor-Mazuy.** y = α + β x + γ_up x² 1{x>0} + γ_down x² 1{x≤0} + ε, common β.
Good timing in up markets: γ_up > 0 (beta rises as the market rises). Good timing in down markets: γ_down > 0 (since x < 0, the slope β + 2γ_down x falls as the market falls). H₀: γ_up = γ_down is tested with a Wald test.

**Henriksson-Merton (1981).** y = α + β₁ x + β₂ max(0, x) + ε.
β_down = β₁, β_up = β₁ + β₂. Timing if β₂ > 0. Equivalent to holding a free call option on the market.

**Economic value of timing** (average annual contribution of the timing term over the sample):
- TM: γ · mean(x²) · 52
- HM: β₂ · mean(max(0, x)) · 52

**Dimson (1979).** The same models with K lags of x (and of x² or max(0, x)); contemporaneous and lagged coefficients are summed. Corrects for stale prices and asynchronous NAVs in daily data.

## 3. Fama (1972) decomposition

Annualised arithmetic means (weekly mean × 52), market premium prem = mean(Rm − Rf), target beta β_T:

```
excess return  = net selectivity + diversification + manager's risk + investor's risk

selectivity    = (Rp − Rf) − β · prem                    Jensen's alpha
diversification = (σp/σm − β) · prem                     return required for the specific risk taken
net selectivity = selectivity − diversification
manager's risk = (β − β_T) · prem                        deviation from the target beta
investor's risk = β_T · prem
```

**Target beta.** β_T = 1, the benchmark's beta. Two alternatives were considered:
- the fund's average beta over the window: sets the manager's risk to zero by construction;
- the fund's beta before the window (Jan to Sep 2024, 38 weeks): discarded, because it equals −0.05 for Fundsmith (calm period and asynchronous NAV), which has no economic meaning. Results are in `results/tables/fama_pre_window_beta.csv`.

## 4. Bridge from Fama to timing

Fama's manager's risk assumes a constant beta, so it cannot see timing. Re-estimating with Henriksson-Merton and averaging the fitted equation (OLS residuals have zero mean) gives an exact identity:

```
mean(y) = α_HM  +  β_T · mean(x)  +  (β_down − β_T) · mean(x)  +  β₂ · mean(max(0, x))
          pure     investor's risk    static manager's risk         timing
          selectivity
```

The same identity holds with Treynor-Mazuy (timing term γ · mean(x²)). Jensen's alpha thus splits into pure selectivity, timing and a static beta gap. Caveat: α̂ and β̂₂ are strongly negatively correlated (−0.60 to −0.87), so the sum is well measured but the split is not.

## 5. Robustness checks

| Check | What it shows |
|---|---|
| Passive control (iShares ACWI) | β = 1.00, γ and β₂ ≈ 0, timing value 0.00%: the pipeline does not create timing |
| Anchor day (weeks ending Mon to Fri) | Sign changes for VICEX and Comgest; ODDO becomes significant on some days; only Fundsmith keeps β₂ < 0 on all five days |
| Influence (DFBETAS, threshold 2/√n ≈ 0.20) | The week to 9 Apr 2025 has DFBETAS −7.4 for ODDO and −2.5 for Fundsmith; dropping 2 weeks out of 104 removes all asymmetric significance |
| Dimson, daily K = 0, 1, 2 | Fundsmith's daily γ (t = −2.97) vanishes once lags are added (t = −0.70): it was an asynchrony artefact |
| Monthly (24 obs., anchored on the 22nd) | Reference for Fundsmith: β_down 1.43, β_up 0.71, β₂ = −0.72 (t = −2.40) |
| Power simulation | With 104 weekly observations, a true β₂ of 0.30 is detected less than half the time and 80% power needs β₂ ≈ 0.55. With 24 monthly observations the one-sided 5% test rejects about 13% of the time when there is no timing: the monthly Fundsmith t of −2.40 must be read with that over-rejection in mind |
| Multiple testing | Dozens of specifications: a few |t| > 2 are expected by chance; only results stable across specifications are retained |

## 6. Limits

- **Spurious timing (Jagannathan and Korajczyk, 1986).** Holding convex assets (options, leveraged stocks) creates γ > 0 without any decision; defensive, low-convexity holdings create γ < 0. A holdings-based measure would be needed to separate style from decision.
- **α–γ collinearity.** x² is always positive and therefore correlated with the constant: selectivity and timing offset each other in estimation.
- **Low power.** Two years of weekly data: wide confidence intervals, strong sensitivity to the calendar.
- **NAVs net of fees.** Fixed fees lower α, not γ. A performance fee acts like an option sold by the investor and adds concavity.
- **Benchmark fit.** The MSCI ACWI explains VICEX poorly (R² = 0.23). Funds and indices share the same currency, so there is no FX bias.
- **Fund flows (Edelen, 1999).** Inflows in rallies hold cash and can create negative measured timing. Flows are not observed here.
- **Conditional models (Ferson and Schadt, 1996)** and multi-factor benchmarks would reduce style effects; the study is restricted to the three classical models.

## References

- Dimson, E. (1979). Risk measurement when shares are subject to infrequent trading. *Journal of Financial Economics*, 7(2), 197–226.
- Edelen, R. (1999). Investor flows and the assessed performance of open-end mutual funds. *Journal of Financial Economics*, 53(3), 439–466.
- Fama, E. F. (1972). Components of investment performance. *Journal of Finance*, 27(3), 551–567.
- Ferson, W. and Schadt, R. (1996). Measuring fund strategy and performance in changing economic conditions. *Journal of Finance*, 51(2), 425–461.
- Goetzmann, W., Ingersoll, J. and Ivković, Z. (2000). Monthly measurement of daily timers. *Journal of Financial and Quantitative Analysis*, 35(3), 257–290.
- Henriksson, R. D. (1984). Market timing and mutual fund performance: an empirical investigation. *Journal of Business*, 57(1), 73–96.
- Henriksson, R. D. and Merton, R. C. (1981). On market timing and investment performance II: statistical procedures for evaluating forecasting skills. *Journal of Business*, 54(4), 513–533.
- Jagannathan, R. and Korajczyk, R. (1986). Assessing the market timing performance of managed portfolios. *Journal of Business*, 59(2), 217–235.
- Newey, W. and West, K. (1987). A simple, positive semi-definite, heteroskedasticity and autocorrelation consistent covariance matrix. *Econometrica*, 55(3), 703–708.
- Treynor, J. and Mazuy, K. (1966). Can mutual funds outguess the market? *Harvard Business Review*, 44, 131–136.
