# Post 4 draft

I measured the "jump activity index" of Bitcoin. The answer is 3. The maximum is 2.

The useful question about jumps is not whether they exist but what kind they are. Rare and large (Merton)? Or an endless stream of small ones, with no diffusion at all (variance gamma, CGMY)? The literature has a number for this: the Blumenthal-Getoor index, between 0 and 2. The classic estimate for large US stocks is about 1.5, read as "infinitely many small jumps".

The estimator counts returns above a threshold. The count falls like threshold^(-index). I ran it on nine years of 1-minute BTC bars and on every trade of four coins in October 2026.

- BTC, 1-minute bars: 2.98, with a standard error of 0.03.
- BTC, ETH, SOL, DOGE at 1, 5 and 15 seconds: between 2.6 and 3.9.
- Sanity check on a simulated process with index 1.5: it returns 1.55.
- Sanity check on a simulated path with no jumps, only volatility bursts: above 3.

An index above 2 is not an index. The estimator's authors say so themselves: it means the assumption fails, possibly because there are no jumps to measure. What the slope of 3 does describe is the cubic tail of returns, known since 1998. That is about how often returns are large, not about how small jumps pile up.

Could the cubic tail be rare, large jumps? One test settles it. A 20 bps jump is a 20 bps return at any clock.

- BTC one-minute returns above 20 bps in October: 231.
- BTC one-second returns above 20 bps: 12.

Inside those large one-minute moves, the biggest second carries a quarter of the move, and half the move takes 29 seconds. Same for ETH, SOL and DOGE. About one move a week looks like a real discontinuity.

What it changes:
- Pure-jump models (VG, CGMY) are out as descriptions of the path. They can still fit one option maturity.
- Jump diffusions have little left to explain. Jumps are a few percent of variance.
- The tail is in the volatility: a continuous price whose volatility can multiply within a minute.
- For a hedger this matters. A jump leaves risk no rebalancing can remove. A 30-second slide can be followed, at a price. That is the next post.

Notebook, code and data loaders: https://github.com/PascalLemieux/jumps

References:
Aït-Sahalia and Jacod (2009), Estimating the degree of activity of jumps in high frequency data. https://arxiv.org/abs/0908.3095
Gopikrishnan, Meyer, Amaral and Stanley (1998), Inverse cubic law for the probability distribution of stock price variations. https://arxiv.org/abs/cond-mat/9803374

#quant #volatility #crypto #derivatives

---

Images to attach, in order: figures/04_exceedances.png (hero), figures/04_clock_test.png. Equation images in figures/04_eq_*.png if a carousel is used.
