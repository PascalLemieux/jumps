# Post 6 draft

Is volatility rough? I ran the test both camps argue about, on Bitcoin. Both are partly right.

The claim (Gatheral, Jaisson, Rosenbaum): take log-volatility, measure how big its changes are at lags of 1 to 30 days, and you get a straight line on a log-log plot. The slope gives a Hurst exponent near 0.1. A Brownian-driven volatility would give 0.5. Volatility is far more jagged than Heston allows.

The reply (Cont, Das): you never observe volatility. You estimate it, and the estimation error alone makes a smooth volatility look rough.

Nine years of BTC, daily realized volatility from 5-minute returns:

H = 0.14, with an R-squared of 0.98. The same value the original paper reports for the S&P 500.

Now the measurement.

1. The weekend. Saturday runs at half the weekday volatility. Leave that calendar effect in and H reads 0.11, with a ragged fit.
2. The sampling. Build each day's volatility from fewer returns and H falls: 0.16 with 1-minute returns, 0.10 with hourly, 0.06 with 4-hour. With hourly returns, two thirds of the variance of a one-day change in log-volatility is estimation error.
3. The placebo. I simulated a volatility that is smooth by construction, true H of 0.5, and measured it the same way. With 4-hour returns it reads 0.14. As rough as Bitcoin. The sceptics' mechanism is real.

But the size of the estimation error is known, so it can be removed.

- The smooth simulation goes back to 0.45, at every sampling frequency.
- Bitcoin stays at 0.15.

And on hourly volatility one power law, H = 0.09, runs from one hour to one month. For a Brownian-driven volatility the variance of the change would grow 24-fold between an hour and a day. For Bitcoin it doubles.

So: rough volatility is a fact about Bitcoin between an hour and a month. Measurement makes it look rougher than it is. It does not make it rough when it is not.

What the regression cannot tell you: what happens below an hour, where the estimation error swamps everything, and whether "rough" means a fractional kernel or simply a volatility with no single time scale.

Notebook, code and data loaders: https://github.com/PascalLemieux/jumps

References:
Gatheral, Jaisson and Rosenbaum, Volatility is rough. https://arxiv.org/abs/1410.3394
Cont and Das, Rough volatility: fact or artefact? https://arxiv.org/abs/2203.13820

#quant #volatility #crypto #derivatives

---

Images to attach, in order: figures/06_scaling.png (hero), figures/06_measurement.png, figures/06_hour_to_month.png. Equation images in figures/06_eq_*.png if a carousel is used.
