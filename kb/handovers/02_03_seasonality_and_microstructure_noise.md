# Jumps series: handover for posts 2 and 3

## Series numbering (updated)
The jump-test post was split in two. The series now has seven posts.

1. Jumps versus volatility bursts
2. Intraday seasonality and false jumps
3. Bid-ask bounce and microstructure noise (tick data)
4. Finite or infinite activity
5. Jumps versus rough volatility
6. The jump risk premium
7. Hedging with self-exciting jumps, plus the cross-sectional work (jump share across coins, co-jumps)

Working rule: Pascal reviews the plan for each post before anything is built. Empirical evidence leads; simulation is at most a small sanity check.

---

## Post 2: intraday seasonality and false jumps

### Claim
- Jump tests assume volatility is flat within the day. It is not. Ordinary moves at busy hours get flagged as jumps.
- "Periodicity" in the literature means intraday seasonality of volatility. Use "intraday seasonality" in the post.

### Method
- Lee-Mykland (2008) test: each return is scaled by a local volatility estimate built from bipower variation over a trailing window of K returns.
  - L_i = r_i / sigma_hat_i
  - sigma_hat_i^2 = (1 / (K - 2)) * sum over the window of |r_j| * |r_{j-1}|
  - A return is flagged when |L_i| exceeds a threshold derived from the Gumbel distribution of the maximum.
  - Take the exact constants and the recommended K from the paper. To verify.
- The key property: every detection has a timestamp, so detections can be counted by time of day.
- Seasonality correction, Boudt, Croux and Laurent (2011): estimate a jump-robust seasonality factor f for each time-of-week slot, normalised so that the mean of f^2 is one, then test r_i / f_i in place of r_i.
- Crypto trades around the clock, so estimate an intraweek pattern (day of week by minute of day), not only an intraday one.

### Deliverables
- Chart 1 (candidate hero): detected BTC jumps by hour of day in UTC, before and after the correction.
- Chart 2: the estimated seasonality curve itself across the week.
- Table: number of detections before and after, share removed, breakdown by hour.
- Equation images: the test statistic and the seasonality-adjusted return.

### Data
- Binance public 1-minute klines for BTCUSDT, full available history. ETH optional.
- No simulation.

### Hypotheses to test (not results)
- Detections cluster around the US cash open, scheduled macro releases and funding timestamps (00:00, 08:00, 16:00 UTC).
- Weekends show a different pattern from weekdays.

### Caveats
- Scheduled news produces genuine jumps at the same hours, so a time-of-day cluster is not all artefact. The post should say so.
- US events move by one hour in UTC with daylight saving. Align US-driven effects on New York time.
- The seasonality estimator must itself be robust to jumps, otherwise jumps inflate the factor and hide themselves.
- Many returns are tested, so state the significance level and the expected number of false positives.

---

## Post 3: bid-ask bounce and microstructure noise

### Claim
- At trade level the observed price is the efficient price plus noise, mostly the bid-ask bounce. This inflates realized variance and distorts jump tests: it can hide real jumps and create false ones.
- The fix is to average the noise out, not to remove it trade by trade.

### Method
- Noise model: Y_i = X_i + eps_i, with eps_i roughly plus or minus half the spread.
- Bounce shows up as negative first-order autocorrelation of trade-to-trade returns.
- Roll implied spread: spread = 2 * sqrt(-Cov(dp_t, dp_{t-1})), defined when the covariance is negative.
- Realized variance bias: E[RV] is approximately integrated variance + 2 * n * E[eps^2], so it grows with the number of observations.
- Pre-averaging (Jacod, Li, Mykland, Podolskij and Vetter, 2009):
  - Replace each price by a weighted local average over a window of k_n trades, with k_n proportional to sqrt(n), and weight function g(x) = min(x, 1 - x).
  - Compute realized variance, bipower variation and the jump test on returns between those averages, with a bias correction for the residual noise.
  - Bounce flips sign at random and cancels. A real jump shifts the level and survives.
- Noise-robust jump test: Lee and Mykland (2012). Pre-averaged bipower: Podolskij and Vetter (2009).
- Take exact formulas and constants from the papers. To verify.

### Deliverables
- Chart 1 (candidate hero): volatility signature plot per coin, realized variance against sampling interval, showing the blow-up at high frequency.
- Chart 2: jump detections per coin, raw versus pre-averaged.
- Table per coin: Roll implied spread, noise variance, detections before and after, share that changes.
- Equation images: the noise model, the Roll spread, the pre-averaged return.

### Data
- Pascal's purchased tick data: trades only, six or seven coins, limited history, possibly illiquid names. Location, symbols, dates and file format to be confirmed by Pascal.
- Illiquid coins are useful here: the bounce is larger and the effect is easier to see.
- For reproducibility, check whether the Binance public archive trade files (trades, aggTrades) can serve as a no-credentials substitute for at least one symbol.

### Caveats
- Trades only: no mid-quote benchmark. The noise-robust estimator plays that role.
- Trades are irregularly spaced. Decide between trade time and previous-tick sampling on a clock grid, and state the choice.
- Illiquid coins produce many zero returns and visible tick-size discreteness. Zeros push bipower variation down and can create spurious jump detections. Report the share of zero returns.
- Several trades can share a timestamp. Decide on aggregation.
- Results depend on the pre-averaging window. Show sensitivity to it.

### Link to post 1
- The tick-level part of the jump-share curve in post 1 uses the same pre-averaged estimators. Build them once in src/ and reuse. Post 1 points forward to post 3 for the explanation.

---

## References (dates and titles to verify before publishing)
- Lee and Mykland (2008), original jump test.
- Lee and Mykland (2012), jump test under microstructure noise.
- Boudt, Croux and Laurent (2011), robust intraweek periodicity and jump detection.
- Jacod, Li, Mykland, Podolskij and Vetter (2009), pre-averaging.
- Podolskij and Vetter (2009), bipower variation under noise.
- Roll (1984), implied spread.
- Christensen, Oomen and Podolskij (2014), jumps at ultra high frequency.
