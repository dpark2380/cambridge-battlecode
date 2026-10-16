# v2: gem duo + gold squad

Code: `bots/simon/v2` (C++). The draft is the map-aware scorer from v1, plus duo selection. Gameplay is new in this version.

## Strategy

- **Gem duo**: Cassi & Issac if drafted, otherwise the two highest `fight_score` picks. Greedily captures the best gems-per-turn group it can survive. Fights enemies within 5 tiles when not outnumbered; backs off when hurt.
- **Gold squad**: everyone else. Monsters first, gold clusters second (soft priority: mining valued at 50%). Only hits enemies already in range.
- **Both**: one shared target per squad in shared memory (byte 0 = duo, byte 1 = squad, as group index + 1). Tribute when carrying 30+ gems or within 8 tiles of an altar. Shop at spawn: duo buys Power shards, squad buys Jungle. Recall below 35% HP; leave spawn at 90%.

## Results vs `starter-cpp`

18/18 wins (9 maps × both sides), all by reaching 1000 gems, rounds 330–850. No errors, crashes or fuel overruns, and few deaths.

PvP almost never happened against the starter, so the fight logic is **untested**.

## Errors encountered → fixes

| Symptom | Cause | Fix |
|---|---|---|
| ~165 `bot error` lines per suite; turns silently cut short | Targets died or left vision mid-turn (engine errors 97/98); `vision::champions()` throws on allies outside our own vision | `live_position()` checks before every target query; `visible_champions()` snapshot skips unreadable tiles; moves wrapped in try/catch |
| Duo died repeatedly on expanse; camp kills destroy carried gems | No risk check for the duo; recall started inside monster range (damage cancels it) | `survivable()` risk gate for both squads; step out of reach (`threatened()`) before recalling |
| Over-correction: whole squads idle (collision B: 22 gems) | Risk model assumed every camp hits for the whole fight; waited forever for squad-mates | Sequential damage model (`exposure`, best kill order); threshold 1.5× the present bodies' health; give up after 20 turns of waiting |
| Gold squad frozen for 500+ rounds | Waited *on* spawn tiles, and an occupied spawn tile blocks respawn; also waited when only a dead member's tile was visible | Wait beside the tiles, never on them; only wait when the group is known to be respawning |
| Turns hitting 0 fuel (no error, the turn just stops) | SDK `vision::camp_at` reloads every camp group per call (~30k fuel) | Cached `world::camp_at`. No turn now drops below 30k fuel left |
| Draft's first turn used 560k of 1M fuel on 80×80 | Per-tile SDK calls in the map profile | Flat arrays; now ~210k. Profile skipped below 500k fuel; fallback pick order |

## Known weaknesses

1. **The "gold squad" is our main gem source**: monsters drop gems with their gold. It out-delivered the duo on 5/9 maps (collision 808 vs 196). The roles are really "free clusters + fights" vs "monster farming".
2. **Monoliths are skipped**, though they hold 63% of gems on monolith and 53% on rows.
3. **A duo cannot promise to win fights**: 2 of 3–6 bodies, and vision isn't shared.
4. **Interlock anomaly**: the 3-body gold squad earned only 66 gems / 540 gold.
5. **Duo cohesion**: members drift apart (one recalls, one keeps going), so it often waits on a partner.
6. **Mechanics still assumed, not tested**: camps don't heal while asleep; stuns land on monoliths; how camps pick between equally near champions.

## Results vs a +200 elo opponent (5 platform games, analysed with `tools/replay/analyze.mjs`)

**0/5, mostly blowouts.** We were team A in every game.

| Map | Score | Round | Our deaths (camps) | Their deaths |
|---|---|---|---|---|
| corners | 72–1022 | 311 | 11 (2) | 0 |
| interlock | 166–1028 | 403 | 12 (3) | 1 |
| collision | 80–1014 | 557 | 12 (4) | 3 |
| elkring | 144–1008 | 476 | 2 (0) | 2 |
| packs | 396–1000 | 392 | 9 (1) | 1 |

1. **The gem duo is fed to them.** Cassi & Issac died 4–5 times per game (linked, so each death is two bodies) and scored ~0 gems in every game. They die at the contested central gem spots to 3+ enemies. Likely cause (not yet verified frame by frame): the "fight if not outnumbered" check counts only enemies in our own vision, so it undercounts.
2. **Altar locks deadlock us.** Every enemy champion buys 1–3 altar locks. v2 skips locked altars instead of breaking them (3 basic attacks; tributing at a locked altar auto-attacks the lock). On elkring (2 altars) both were locked, and the whole team stood still from round 150 to 476 holding ~180 gems.
3. **They never die to camps and rarely to us.** 0–3 deaths per game against our 9–12.
4. **Their builds collect passives.** One Monster and one Durability emblem (plus Bruiser on casters), then Power stacks. We stack one family: Varg ended with 12 Jungle emblems, whose passive doesn't stack.
5. **Their draft is consistent**: Stellar + Cassi & Issac + Ren every game, plus Varg/Tavi/Ryth/Vendetta. Ren was their top scorer in 3/5 games.
6. **Our gold squad is competitive.** Packs: our Varg 308 gems vs their Varg 378. The gap is the duo and the deaths.

## Next steps

1. **Break altar locks**: walk to a locked altar and attack the lock (or just call `submit_gems`, which converts into lock attacks). Consider buying and placing locks ourselves on the enemy's nearest altar.
2. **Stop feeding the duo**: don't contest central gems against superior numbers; retreat on first sight of 2+ enemies unless clearly ahead; keep the duo with the squad on small maps.
3. **Build for passives**: one emblem each of Monster / Durability, then Power, as the opponent does.
4. **Keep `bots/simon/v2` frozen as a baseline opponent**: start v3 in its own folder.
5. Older items: the interlock gold squad, monoliths, untested mechanics.

## Tunables

`bots/simon/v2/src/bot.cpp`, top of file: `body_damage`, `body_health`, `max_damage_share`, `mining_weight`, `recall_health`, `spawn_leave_health`, `tribute_gems`, `tribute_detour`, `engage_radius`, `max_wait_turns`, `give_up_rounds`. Shop thresholds (150 squad / 300 duo) are in `Bot::shop_trip`.
