# Jumps series: handover for post 1

## Context
- LinkedIn series of six posts on jumps in financial time series, aimed at a quant audience.
- One repo for the series, one notebook per post, helpers to download Binance 1-minute data with no credentials so that anyone can reproduce the results.
- Each post needs: a few clean equations (exported as images), one strong chart from the notebook, short analysis, empirical results on crypto and/or stocks.
- Post voice: direct, slightly punchy.

## Status of the existing scaffold (jumps-series-repo.zip)
- Treat it as a rough draft. Pascal has not reviewed or run it.
- Notebook 1 has only been executed on simulated data. The Binance download has never run against the real archive; the parser was tested on mock files only.
- Working rule: Pascal reviews the plan for each post before anything is built. Posts 2 to 6 are not yet reviewed.

## Post 1: decisions so far

### Claim
- Large isolated price discontinuities are rare. Most moves that bar-based tests label as jumps unfold over several minutes.
- "Volatility burst or jump" is a model-dependent question, so the post should make the narrower model-free claim above.

### Empirical first, simulation second
- Pascal prefers empirical evidence to simulation.
- Shrink the simulation to a small sanity check. BTC and ETH results lead the notebook and the post.

### Deliverable 1: event panel (candidate hero chart)
- Scan the full BTCUSDT 1-minute history for the largest absolute 15-minute moves.
- Select the top six or so by rule, on distinct days, to avoid cherry-picking.
- One small chart per event: the 15-minute bar as a single move, and the 1-minute path inside it.
- One number per event: share of the total move carried by the largest single 1-minute return.
- Pascal recalls an episode where BTC moved 12% in 12 minutes and looked like a smooth drop at 1-minute resolution. It should surface in the scan.

### Deliverable 2: jump share against sampling frequency
- Relative jump measure RJ = (RV - BV) / RV, with RV realized variance and BV bipower variation, computed at intervals from the finest available up to 1 hour.
- Report the share of days flagged by the Barndorff-Nielsen and Shephard test at each interval.

### Deliverable 3: variance gamma contrast (Pascal wants this kept)
- Variance gamma is Brownian motion on a gamma clock: purely discontinuous, infinite activity, no diffusion component.
- Testable contrast as sampling gets finer:
  - Diffusion with volatility bursts: the jump share falls towards the true jump share, possibly zero.
  - Pure-jump process: the jump share rises towards 100%, because bipower variation has no continuous part to converge to.
- The direction of the empirical curve is therefore evidence about which description fits BTC.
- Technical note: plain variance gamma has independent increments, so it cannot produce clustering of activity on its own. A stochastic time change is needed for that. Worth one sentence in the notebook.
- This is also the bridge to post 3 (finite or infinite activity).

## Data
- Default: Binance public archive, 1-minute klines, no API key.
- Pascal believes he owns one to two gigabytes of tick data. He needs to locate it and confirm symbols, dates and format.
- If tick data is available: use it as a deep dive on one or two symbols. The contrast in deliverable 3 is cleanest at tick frequency.

## Caveats to state in the notebook and the post
- A smooth path at 1 minute does not rule out small jumps at tick level. It rules out one large discontinuity.
- Microstructure noise distorts RV and BV at the finest frequencies. Tick-level work needs noise-robust estimators such as pre-averaging.
- With 1-minute bars only part of the sampling curve is visible.
- The figures quoted from Christensen, Oomen and Podolskij (2014), about 10% jump share at 5 minutes and about 1% at tick frequency, were written from memory. Verify against the paper before publishing.

## Simulation in the current draft, for reference
- Driftless log price on a 5-second grid, 50% annualised volatility.
- Volatility = persistent daily level (AR(1) in logs) times a smooth intraday cycle.
- Bursts world: volatility spikes of 10 to 25 times, about one every two days, 60-second half-life. Continuous path, no jumps.
- Jumps world: compound Poisson jumps with Gaussian sizes carrying 10% of total variance.
- Not geometric Brownian motion, and not a full model: no leverage effect, no microstructure noise, burst parameters chosen by hand.

## Parked
- Cross-sectional analysis (jump share across many coins, co-jumps) is deferred to post 6.

## Open questions for Pascal
- Include ETH in the event panel, or BTC only?
- Bars only, or tick data for the sampling curve?
- Which chart is the hero: the event panel or the sampling curve?

## First tasks for Claude Code
1. Unzip the scaffold and read README.md.
2. Run the Binance downloader against the real archive and fix anything that breaks.
3. Do not extend notebook 1 until Pascal confirms the plan above.

---

## Status notes (added 2026-11-24, after the handover)
- Tasks 1 and 2 done. The downloader ran clean against the real archive: 24 months each of BTCUSDT and ETHUSDT, 729 complete days per symbol, no parser fixes needed.
- The committed notebook and post draft still follow the scaffold's ordering (simulation first). Restructure to empirical-first once Pascal confirms the plan.
- Claude's recommendations on the open questions: BTC only for the event panel; bars now, tick data later as a deep dive; event panel as the hero chart. Awaiting Pascal's call.

## Build notes (2026-11-24)
- Pascal gave the go-ahead to build. Open questions resolved as recommended: BTC only in the event panel, 1-minute bars for the sampling curve (tick data later), event panel as the hero chart.
- Data: full BTCUSDT and ETHUSDT history, Aug 2017 to Oct 2026, 3,315 complete days each after dropping days with gaps over five minutes.
- Event panel: rolling 15-minute windows over every minute, one per UTC day, top six. Biggest minute carries 15-34% of the move; median 29% over the top 50; four of fifty above 50%. Pascal's "12% in 12 minutes" is most likely 19 May 2021 (-14.3% in 15 min) or 4 Dec 2021 (-14.0%).
- Sampling curve is not monotone: jump share 15% at 1h, 7% at 5m, 9% at 1m. The 1m uptick is stated as the open question for posts 2 and 3, not hidden.
- Variance gamma world added to the simulator. Three-world chart overlays BTC.
- COP 2014 figures verified against arXiv:2602.10925: "about 1% of total price variability", "an order of magnitude" below lower-frequency estimates. The "10% at 5 minutes" recollection is not the paper's own estimate and is not quoted.
- Notebook header carries a short bio and the LinkedIn link; this header format is to be reused on every post. Bio drafted from the CV; Pascal to edit.
