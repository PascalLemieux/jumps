# Post 3 draft

"Sample every 5 minutes to avoid microstructure noise." I tested that rule on 53 million crypto trades. It fails in both directions.

The textbook: a trade price is the efficient price plus noise, mostly the bounce between bid and ask. Sample faster and the noise piles up in your realized variance. So you use 5-minute bars.

I took every trade of seven coins on Binance in October 2026, from Bitcoin to two football fan tokens that trade once every 20 seconds, and compared realized variance at each clock with a noise-robust estimate (pre-averaging).

The fan tokens are the textbook, on steroids.
- Trade-to-trade return autocorrelation: -0.48. Pure bounce is -0.50.
- Tick-level variance: 19 to 24 times too high.
- 5-minute variance: still 2.3 to 2.9 times too high. PSG reads 90% vol on 5-minute bars. The right number is 53%.

Bitcoin is the textbook, backwards.
- Return autocorrelation at lag 1: zero. No bounce.
- Tick-level variance: one third of the true figure. 18.6% vol on every trade, 33.1% on 5-minute bars, 33.1% pre-averaged.
- Trade signs have an autocorrelation of 0.65. Orders come in runs and the price trends from trade to trade. Looking closer removes variance instead of adding it.

Either way, raw ticks wreck jump measures.
- Bipower variation puts 21% to 56% of variance in jumps. More than half of tick returns are exactly zero, and one zero kills two bipower products.
- The Lee-Mykland test flags 8,800 jumps a day in BTC and fewer than one in the fan tokens. Noise creates jumps in one coin and hides them in the other.

Average the noise out and both problems go away. The pre-averaged jump share for BTC, ETH, SOL and DOGE: between -2% and 0%. That is zero, to within the error of the method.

This also closes post 1. The jump share of BTC against bar size is a U: coarse bars turn slides into jumps, fine sampling starves bipower of non-zero returns. The noise-robust answer sits below the bottom of the U.

Caveats: one month, trades only, and counts of tick-level jumps move with the averaging window. Their share of variance does not: under 3.5% for the five liquid coins at every setting.

Notebook, code and data loaders: https://github.com/PascalLemieux/jumps

References:
Jacod, Li, Mykland, Podolskij and Vetter (2009), the pre-averaging approach. https://doi.org/10.1016/j.spa.2008.11.004
Christensen, Oomen and Podolskij (2014), Fact or friction. https://arxiv.org/abs/2602.10925

Next: if there are jumps, what kind? A few large ones, or an endless stream of small ones.

#quant #volatility #crypto #marketmicrostructure

---

Images to attach, in order: figures/03_signature.png (hero), figures/03_jump_share.png, figures/03_btc_jump_share_curve.png. Equation images in figures/03_eq_*.png if a carousel is used.
