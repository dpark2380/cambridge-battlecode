# v79: v78 + B224, a body that keeps dying needs a bigger edge

**Change (`src/bot.cpp`, `src/bot.h`):** each body counts its own deaths (no SDK counter: alive → dead transitions). Once it has died 3 times this game, it engages only with a 1.5x power edge instead of 1.2x (Vesper's 1.3x becomes 1.5x too).

**Why:** ranked losses with 15+ deaths on 04comb/04horseshoes/04sunburst/04wheel (12 games, v73-v77), `tools/fights.py`: deaths 3.42 per 1000 champion-rounds vs 1.53 in an average game, contact 216 vs 116, and we died in 18.8% of fights started ahead in numbers (8.2% normally), 23.8% at even numbers (11.8%), 33.7% outnumbered (19.8%). Those opponents are stronger per body than our power estimate says. Local opponents do not reproduce it (v78 wins those maps vs pe3 21/24 and 15/24, vs hunter-v0 16/16), so only a body that is already losing changes behaviour.

**Gates vs v78:** profgate on pe3 margin +12 ± 14, deaths −0.3 ± 0.1 **; nonreg PASS after 2,048 games at 48% (gems −10 ± 10). A panel and ranked deaths decide.
