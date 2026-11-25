# Post 2 draft

Your jump test keeps New York hours.

I ran the standard intraday jump test (Lee-Mykland) on nine years of Bitcoin at 5 minutes. It flags 6,461 jumps. Then I looked at the clock.

29% of them fall in the four hours around the US open. Four hours out of 24 should get 17%.

The test compares each return with the volatility of the previous 22.5 hours. Bitcoin's volatility is not flat inside that window. In 2024-2026 the 09:30 New York slot runs at 2.3 times the daily level. Early Saturday runs at a third of it. An ordinary move at the open looks like a 4-sigma event. A real jump on Saturday morning looks like nothing.

So I estimated the weekly rhythm with a jump-robust estimator (Boudt, Croux, Laurent) and tested again.

- 1,752 jumps disappear. That is 27% of the original detections.
- 1,632 new ones appear, in the quiet hours.
- Busiest hour against quietest: 5.5 to 1 before, 1.5 to 1 after.
- The US open hump is gone. The 09:30 slot drops from 65 detections to 10.
- The funding timestamps at 00:00 and 16:00 UTC stop looking special.

One slot survives: 08:30 in New York, the time of US data releases. It keeps 47 detections, three times any ordinary slot. Real news at a fixed time looks like seasonality. Only a robust estimator tells them apart: with a plain standard deviation, a third of those jumps hide behind themselves.

The number that did not move is the total. With no jumps the test should flag about 33 returns in nine years. It flags more than 6,000, before and after. Seasonality decides the hour. It does not decide the count.

Also worth knowing: the rhythm itself has sharpened. In 2017-2020 the open ran at 1.2 times the daily level. Bitcoin has become a US-hours asset.

Notebook, code and data loaders: https://github.com/PascalLemieux/jumps

References:
Lee and Mykland (2008), Review of Financial Studies. https://doi.org/10.1093/rfs/hhm056
Boudt, Croux and Laurent (2011), Journal of Empirical Finance. https://doi.org/10.1016/j.jempfin.2010.11.005

Next: what the price is made of at trade level, and what the bid-ask bounce does to all of the above.

#quant #volatility #crypto #marketmicrostructure

---

Images to attach, in order: figures/02_jumps_by_hour.png (hero), figures/02_weekly_seasonality.png, figures/02_new_york_slots.png. Equation images in figures/02_eq_*.png if a carousel is used.
