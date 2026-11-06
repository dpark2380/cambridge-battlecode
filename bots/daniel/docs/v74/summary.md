# v74: v73 + B193, eight constants tuned together

**Change (`src/bot.cpp`):** `tools/tune.py --bot v73 --iterations 8 --seeds 1` (evolution strategy, 3 candidates an iteration, each played against the incumbent on every map and side) over eight constants. It accepted one step at iteration 2 (59% vs v73, again 59% on fresh seeds), and no later candidate beat it (38-54%):

| constant | v73 | v74 |
|---|---|---|
| max_damage_share | 4.035 | 4.895 |
| help_wait_turns | 50 | 40 |
| gold_weight | 0.30 | 0.233 |
| recall_health | 0.40 | 0.422 |
| carrier_recall_health | 0.50 | 0.517 |
| spawn_leave_health | 0.95 | 0.940 |
| extra_body_value | 1.00 | 1.117 |
| threat_tribute_gems | 20 | 19 |

The largest move is `max_damage_share` (+21%): a group is "survivable" when its exposure per damage is at most this many health bars, so bodies take on bigger groups alone or in smaller teams. The one-at-a-time sweeps (B176-B191) could not find this: it works together with the other shifts.

**Gate:** gain vs v73 PASS 300/512 = 59%; submitted gems +63.5 ± 19.8, gems captured +69.4 ± 16.8, deaths −0.9 ± 0.5, gold −91 ± 137.

**Live (version 91, live 18:32:38Z 6 Nov).** Panel v74p1 57-33, the best panel on engine 3: vs v73p1 (90 paired) 56 → 57 wins, margin +16 ± 50, gems +9 ± 27, deaths −0.6 ± 0.7 (neutral); vs v71p1 56 → 57, margin +36, panelcmp BETTER. Kept. Ranked 11-14 by 19:29Z, 46-54 at 100 games (22:00Z), **80-70 = 53% at 150 games (23:36Z)**: passes the user's 48% rule, kept. Ladder 1746 (#217) at 23:36Z, the high since engine 3.0.0.
