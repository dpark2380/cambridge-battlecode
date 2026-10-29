# v34: v33 + B86 (01boss_battle: bank only a siege-sized bag)

On 01boss_battle the only altar sits behind a Monolith (B34). `tribute_detour` sent carriers with 9-19 gems to the
breach, where they died striking the Monolith: 21-31% of body-rounds within 4 of it, and gold 6.1k against top teams'
17.3k (`docs/research/worst-maps-2026-10-29.md`).

## Change
`init` notes when the walled-altar corridor cuts a Monolith. In `should_tribute`, until the corridor has been seen with
no camp on it, a carrier banks only with 100+ gems.

## Results (`data/b86-gates.txt`)
- Map gate on 01boss-battle vs v33: **97% (58/60), PASS**.
- Nonreg vs v33: 51% (144/280), PASS.
- Local vs v12: 646-0 with 6 deaths (v33 494-0, 25 deaths).
- Nonreg PASS vs v12 80%, Jame v3 92% (`data/v34-gates.txt`).

## Ranked
Submitted 2026-10-29 07:49Z as team bot version 30 (user-approved), replacing v33 at 54-51. Scrim panel queued.
- tune.py on v34 (08:20Z; tribute_gems, tribute_detour, spawn_leave_health, gold_weight, max_damage_share,
  carrier_recall_health; 6 iterations x 3 candidates): no candidate beat the incumbent (best step 53%, not confirmed).
- Scrim panel: 30-60, identical game for game to v33's (no panel map is 01boss_battle and games are deterministic). A panel only tells versions apart when the change plays on panel maps.

## Scrim A/B round (2026-10-29 10:42-12:21Z, user-approved)
Scrims are deterministic per (opponent, map, side), so each candidate was submitted for its 90-game panel and compared
game by game with v34's panel (30-60). Candidates are v34 plus one change each (backlog rows).

| Candidate | Live (team bot version) | Panel | L→W | W→L | Net | Identical games | Deaths/game | Verdict |
|---|---|---|---|---|---|---|---|---|
| b89c: Vesper Treasure > Durability > Power of strength, 25% health (B89) | 10:42 (31) | 25-65 | 3 | 8 | -5 | 25 | ~0 | rejected |
| b87b: join a fight an ally within 4 is in (B87) | 11:00 (32) | 29-61 | 8 | 9 | -1 | 4 | -0.50 | neutral |
| b91a: opening pack before r60 on 4-5 body maps (B91) | 11:45 (33) | 31-59 | 12 | 11 | +1 | 20 | -1.26 | neutral |
| b88d: wait for 2 allies near a recent lost fight (B88) | 12:04 (34) | 20-70 | 5 | 15 | -10 | 7 | +0.36 | rejected |
| b92: b87b + b91a (B92) | 14:06 (36) | 28-62 | 8 | 10 | -2 | 2 | -0.90 | neutral |

A change that touches every game makes almost every game diverge, so flips have a spread of about sqrt(flips) (±4
for ~20 flips): only b88d's -10 is clearly real. Ranked over the A/B period (mixed candidates): 22-18. v34
resubmitted 12:21Z as team bot version 35.

Second round (user: "Can you try the A/B again"): b92 passed the local gain gate vs v34 (234/420 = 56%, race 57%) but
the panel is neutral (net -2, deaths -0.9/game). Local and scrim disagree again, as with every candidate since v27.
v34 resubmitted 14:23Z as team bot version 37.

v35 (b92) then had a full ranked run from 14:28Z: 64-71 over 135, which met the auto-revert rule. v34 resubmitted
2026-10-29 19:01Z as team bot version 39, the live bot.

Since the 19:01Z resubmission: 58-55 over 115 ranked games by 22:55Z (ladder #236, 1677). That is about level, close to v34's first run (v33 54-51 before it) and better than v35's 64-71.
