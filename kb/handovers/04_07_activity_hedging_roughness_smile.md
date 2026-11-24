# Jumps series: handover for posts 4 to 7

## Series numbering (updated, nine posts)
1. Jumps versus volatility bursts
2. Intraday seasonality and false jumps
3. Bid-ask bounce and microstructure noise
4. Finite or infinite activity
5. What jump activity does to your hedge (pencilled, pending options data check)
6. Is volatility rough?
7. Jumps or roughness in the smile?
8. The jump risk premium (not yet reviewed)
9. Hedging with self-exciting jumps, plus the cross-section (not yet reviewed)

## Rules for every post
- Pascal reviews the plan before anything is built.
- Empirical evidence leads. Simulation is at most a small sanity check or placebo.
- End each post with one or two references at most, each with an arXiv or SSRN link where one exists. Check every link and citation against the actual page before publishing. Nothing goes out from memory.
- Recurring theme of the series: is the effect real, or is it the measurement?

---

## Post 4: finite or infinite activity

### Claim
- The useful question is not "are there jumps" but "what kind": rare and large (Merton, compound Poisson) or an endless stream of small ones (variance gamma, CGMY, tempered stable). And is a Brownian component needed at all?
- This is the formal version of the variance gamma contrast in post 1.

### Method
- Jump activity index (Blumenthal-Getoor), beta in [0, 2]: the smallest power p for which the sum of |jump sizes|^p is finite. Near 0 means few small jumps, near 2 means almost diffusion-like.
- Reference values: compound Poisson 0, variance gamma 0, CGMY equal to Y, alpha-stable equal to alpha.
- Note: variance gamma has infinite activity but index 0, so the index alone does not separate finite from infinite activity. Aït-Sahalia and Jacod have a separate test for that.
- Counting estimator: let U(u) be the number of returns with absolute value above a threshold u. For small sampling intervals U(u) scales like u^(-beta). So beta_hat = log(U(u) / U(g*u)) / log(g) for a factor g > 1.
- Exact estimators, thresholds and standard errors from Aït-Sahalia and Jacod. To verify.

### Deliverables
- Chart (candidate hero): log of the count of large returns against log of the threshold, one line per coin. The slope is minus the activity index.
- Table: estimated index per coin with a confidence interval.
- Equation images: definition of the index, the counting estimator.

### Data
- Pascal's tick trades (six or seven coins, trades only), plus Binance 1-minute bars for BTC as the reproducible version.

### Caveats
- Microstructure noise looks like infinite activity and pushes the index up. Use the pre-averaging tools from post 3.
- Standardise returns for intraday seasonality first (post 2).
- Thresholds must sit above the diffusive scale, several times sigma * sqrt(dt), otherwise the count picks up Brownian moves.
- Results are sensitive to threshold choice. Show a range.

### Relevance, to be developed (Pascal's request)
- The post must not end on "the index is 1.5". It must say what that changes in practice: which model family is admissible for short-dated options, and what it does to hedging. Post 5 delivers the hedging part.

### References to verify
- Aït-Sahalia and Jacod (2009), estimating the degree of activity of jumps.
- Aït-Sahalia and Jacod (2010), is Brownian motion necessary to model high-frequency data.
- Aït-Sahalia and Jacod (2011), testing whether jumps have finite or infinite activity.
- Their equity estimates of the index (recalled as around 1.5 for large caps) need checking.

---

## Post 5: what jump activity does to your hedge (pencilled)

### Status
- Pascal's idea. Pencilled in after post 4. Options data question parked until he checks what he has.

### Claim
- The type of jumps determines how much risk delta hedging can remove, and how fast extra rebalancing helps.

### Experiment
- Sell a short-dated BTC option (ATM, one day to two weeks), delta-hedge it along real price paths, and vary the rebalancing frequency from one minute to daily.
- The model enters only through the delta. The paths are real.

### Deliverables
- Chart 1 (candidate hero): dispersion of hedging error against rebalancing frequency, log-log. Pure diffusion benchmark: error shrinks like one over the square root of the number of rebalances. Large rare jumps: a floor. Many small jumps: in between, with the decay governed by the activity index.
- Chart 2: P&L distribution of the hedged short option under a Black-Scholes delta versus a jump-aware delta. Report skew, kurtosis and tail quantiles.
- Table: hedging error by frequency, gross and net of transaction costs.

### Data
- Spot: Binance 1-minute BTC.
- Options, in order of preference:
  - Minimum: an ATM implied volatility series (for example DVOL), with the option priced synthetically.
  - Better: Deribit quotes for short-dated options with mark price or bid and ask, mark implied volatility, strike, expiry, index price.
  - Best: the full surface. Pascal believes he has the whole surface at hourly or finer frequency for about the past six months. To be checked.
- Possible no-credentials fallback: Deribit public trade history, where each trade carries implied volatility and index price. To verify.

### Caveats
- One history, overlapping option lives: use non-overlapping windows or a block bootstrap, and say so.
- The gap between implied and realised volatility creates a mean P&L. Separate the mean (risk premium, post 8) from the dispersion (hedging error).
- Transaction costs rise with frequency. Report both gross and net.

---

## Post 6: is volatility rough?

### Background (Pascal was new to rough volatility, keep a short primer in the notebook)
- Rough volatility is a statement about how jagged the volatility path is. Prices stay continuous. There are no jumps.
- Heston: variance = starting value + sum of all past increments (mean reversion plus vol-of-vol shocks), each with weight one.
- Rough Heston: same increments, each weighted by a kernel (t - s)^(H - 1/2), scaled by 1 / Gamma(H + 1/2). With H = 1/2 the kernel is one and the model is Heston.
- Rough Bergomi: v_t = xi_0(t) * exp(eta * W^H_t - 0.5 * eta^2 * t^(2H)), with W^H a fractional Brownian motion (Volterra form) correlated with the price.
- Discrete-time intuition: today's volatility is a weighted sum of all past shocks with power-law weights. A shock hits hard at once, much of it fades quickly, a small part lingers. Changes in log-volatility are negatively autocorrelated, like an ARFIMA process with negative d (d = H - 1/2).
- Empirical claim of Gatheral, Jaisson and Rosenbaum: H is about 0.1, against 0.5 for Brownian motion.

### Method
- Build a realized variance series from intraday returns, take logs.
- m(q, lag) = mean of |log sigma_(t+lag) - log sigma_t|^q. Under roughness m(q, lag) scales like lag^(q*H).
- Linear regression of log m on log lag. Slope = q*H. Intercept gives the vol of vol.
- Simple check: variance of the 4-period change over variance of the 1-period change is 4^(2H). That is 4 for a random walk and about 1.3 for H = 0.1.

### The contested part (the angle Pascal likes)
- In the original paper the regression is strikingly clean, R-squared near one.
- Two reasons for caution:
  - It is a regression on averages over thousands of days with a few dozen lags, so a tight fit is nearly built in.
  - Cont and Das: a smooth, Brownian-driven volatility measured with estimation noise produces the same clean line and an apparent H near 0.1.
- The post should show the clean line on BTC, then show how much of it survives once measurement noise is accounted for.

### Deliverables
- Chart 1 (candidate hero): log m against log lag for BTC, several values of q, with the fitted H.
- Chart 2: how the estimated H moves with the way realized variance is measured (sampling frequency, noise-robust estimator from post 3).
- Table: H per coin and per measurement choice.
- Optional placebo, kept small: simulate a Brownian-driven volatility (H = 0.5), measure it the same way, and report the H the regression returns.
- Equation images: the kernel form of rough Heston, the scaling law.

### Simulation notes (Pascal asked if this can be built in Python: yes)
- NumPy is enough. Exact Cholesky method for a few hundred time steps. Hybrid scheme (Bennedsen, Lunde and Pakkanen) for long paths. About fifty lines for rough Bergomi.
- Ports to PyTorch if rough-volatility paths are wanted for hedging agents.
- Historical estimation gives real-world parameters. Calibrating to option prices is a separate exercise (post 7).

### Data
- Binance 1-minute BTC for realized variance, daily and hourly. Tick trades for the noise-robust version.

### References to verify
- Gatheral, Jaisson and Rosenbaum, "Volatility is rough".
- Cont and Das, "Rough volatility: fact or artefact?".
- Bayer, Friz and Gatheral, "Pricing under rough volatility".
- El Euch and Rosenbaum, rough Heston.

---

## Post 7: jumps or roughness in the smile? (only partly discussed)

### Agreed so far
- Puzzle: short-dated smiles are far steeper than classic stochastic volatility models produce.
- Two rival explanations: jumps, or rough volatility, where the ATM skew grows as a power of maturity, T^(H - 1/2), as maturity shrinks.
- Empirical chart: ATM skew against time to expiry on a log-log scale, from Deribit BTC options down to the dailies, using Pascal's surface data.

### Notes not yet discussed with Pascal
- The BTC smile is often close to symmetric and the skew changes sign. Consider the term structure of curvature (butterfly) alongside skew.
- There is published work questioning whether the equity skew really follows a power law at the shortest maturities. Worth checking before fixing the angle.
- Different jump models imply different short-maturity behaviour of the skew. The exact asymptotics need to be taken from the literature, not from memory.

### Next step
- Review the angle with Pascal before building.
