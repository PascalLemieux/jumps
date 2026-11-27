# Post 1 draft

Most "jumps" in Bitcoin are not jumps.

I took the six largest 15-minute moves in BTC's history on Binance, 2017 to 2026, and looked inside each one at 1-minute resolution.

- 13 Mar 2020: +28% in 15 minutes. Biggest single minute: 26% of the move.
- 12 Mar 2020: -23%. Biggest minute: 32%.
- 16 Jan 2018: +19%. Biggest minute: 27%.
- 12 Nov 2017: +15%. Biggest minute: 15%.
- 10 May 2020: -14%. Biggest minute: 34%.
- 19 May 2021: -14%. Biggest minute: 22%.

Not one is a discontinuity. They are slides that take 5 to 14 minutes to cover half the distance. Across the 50 largest moves, the biggest minute carries 28% of the move at the median.

Thinner markets tell the same story. For ETH, XRP and SOL the median is 28% to 31%, and half the move takes 10 to 12 minutes. XRP's crash of 10 October 2025 took 45% off the price in 15 minutes. Its worst single minute carried 42% of that.

On a 15-minute chart each of these is one candle. To a jump test that only sees candles, one candle is a jump.

So the test's verdict depends on the clock. Bipower-variation jump share of BTC variance, same 3,307 days:

- 1-hour bars: 15%
- 5-minute bars: 7%
- 1-minute bars: 7%

And at 1 minute the Barndorff-Nielsen-Shephard test still flags a jump on 34% of days. Nominal size: 1%.

Why: bipower variation removes jumps only if volatility is roughly constant across adjacent returns. A move that unfolds over ten minutes inside one bar breaks that, and the whole move is booked as a jump.

A small simulation shows which way the curve should bend. For a continuous path with volatility bursts, the jump share falls as sampling gets finer. For a pure-jump variance gamma process, it rises towards 100%. From 1 hour down to 5 minutes, BTC bends like the continuous path. The small uptick at 1 minute is where the next two posts start.

On equity and FX tick data, Christensen, Oomen and Podolskij (JFE 2014) put the jump share at about 1%, an order of magnitude below bar-based estimates. https://arxiv.org/abs/2602.10925

Notebook, code and data loaders: https://github.com/PascalLemieux/jumps

Next: intraday seasonality, or why the test cries jump at the same hours every day.

#quant #volatility #crypto #marketmicrostructure

---

Images to attach, in order: figures/01_event_panel.png (hero), figures/01_jump_share_by_sampling.png, figures/01_three_worlds.png. Equation images in figures/01_eq_*.png if a carousel is used.
