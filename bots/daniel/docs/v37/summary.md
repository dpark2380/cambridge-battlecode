# v37: v34 + B99c (Vesper keeps her dash for escapes, leaves earlier, runs)

## Problem
On the scrim panels our Vesper dealt 8.1k champion damage a game, took 9.3k and died 5.0 times; opponents' Vesper dealt
12.8k, took 7.0k and died 1.7 times (B98 panel table). Before r300 she dies 0.72 times a ranked game against an opposing
Vesper's 0.34, mostly mid-map to champions. `move_towards_closest` spent her plain movement dash on every walk, so it was
on cooldown when she needed to leave, and a leaving Vesper with an enemy in range shot back (B62) instead of running.

## Change (backlog B99, variant c)
- While an enemy was seen in the last `threat_memory` rounds, plain movement dashes are kept for escapes.
- Vesper leaves at 50% health when an enemy champion is in sight.
- A leaving Vesper runs (escape dash) unless her target is below 25% health.

## Results
| Test | Result |
|---|---|
| Local race vs v34 (140) | 53% (b99b 49%, b99a 47%) |
| Local gain gate vs v34 | FAIL 354/700 = 51% (self-play does not test this: every local opponent has our Vesper) |
| **Scrim panel** (team bot version 43, 09:17Z) | **32-58** (v34 30-60, v36 26-64): paired vs v34 L→W 11, W→L 9, net +2; vs v36's newer panel net **+6** |
| Panel deaths | **14.2 a game** (v34 17.7); opponents' deaths 11.6 (9.7); gems 558/766 (511/819); gold 5,348 (5,057) |
| Ranked while live (09:17-10:08Z) | **16-9**; ladder #242 1674 → #219 1700 |

Not yet submitted for a full ranked run: v34 resubmitted 10:08Z as team bot version 44 at the end of the A/B round.
