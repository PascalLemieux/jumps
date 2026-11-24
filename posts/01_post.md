# Post 1 draft

Most "jumps" in your data are not jumps.

I simulated a market with zero jumps. Continuous paths only, plus short volatility bursts: vol spikes for a minute or two, then decays.

Then I ran the standard bipower-variation jump test on it.

- Sampled every 5 seconds: 0.7% of variance attributed to jumps
- Sampled every 1 minute: 3.7%
- Sampled every 5 minutes: 8.7%

A second simulation with genuine jumps worth 10% of variance also reads 8.7% at 5 minutes. From 5 minutes upward the two worlds cannot be told apart.

Worse, at 5 minutes the test flags a jump on 13% of days in the no-jump world. Nominal size: 1%.

Why: bipower variation removes jumps only if volatility is roughly constant across adjacent returns. A burst shorter than your bar breaks that, and the whole move lands in one return.

BTC and ETH, Binance 1-minute bars, 2023-2024: the estimated jump share is 3.5-3.8% at 1 minute, 6-8% at 5 minutes and 13-14% at 1 hour. Same shape as the no-jump simulation. And at 1 minute the test still flags a jump on 28-29% of days, so nobody should read the 1-minute number as the floor.

Christensen, Oomen and Podolskij documented this on tick data in 2014. It matters for anyone calibrating jump intensities from bars, or sizing gap risk off them.

Notebook and code: https://github.com/PascalLemieux/jumps

Next: why the test over-rejects even on a fine grid.

#quant #volatility #crypto #marketmicrostructure
