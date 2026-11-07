# v76: v75 + B201, fuel fixes for big maps

**Change (`src/bot.cpp`, `src/bot.h`):**
- `place_ward`: after a failed placement (out of charges or an ally ward there) wait 50 rounds before trying again (`ward_retry_round`). Out of charges the ward cooldown stays 0, so every turn scanned the bushes and threw: ~7k fuel a turn.
- `fight_enemies`: return before reading every visible ally's stats when no enemy champion is visible (~8k fuel a turn).

- `place_ward` (B203): with no bush in reach, wait 5 rounds before scanning again (the scan built blocked-tile and bush boards every turn, ~6k fuel; profiled on 02tangle).

No targeting or fighting decision changes.

**Why:** 77 of 470 ranked games since v67 had 50+ fuel-exhausted turns (40-37), worst on big maps: 04orchard 250-395 a game (0-3), 02tangle 155-245 (0-4), 04wilds ~100 (0-4). In the 04orchard summaries about 185 of our turns ran out of fuel in rounds 0-250, the opponent's about 1: we banked nothing until r300-r500. A fuel profile of v75 (scope timers, `bots/_var/fp75`) found the ward and fight costs on top of 28k (41k peak) for work and 42k peaks for choose_target.

**Results:**
- Fuel-exhausted turns, ours, vs prof-aynir on 04orchard: rounds 0-250 186 → 35, whole game 382 → 126 (v75 → v76). The full B201 measured 02tangle 58 → 52 and 04wilds 32 → 20.
- Against prof-aynir on the 44 maps over 3,000 tiles, same setups: v75 128/176 = 73%, B201 with a slower target-field refresh 128/176 = 73%, **v76 136/176 = 77%**.
- nonreg vs v75, all maps: PASS (gems −6 ± 20; a mirror hides a fuel fix because both sides stall the same way).
- The full B201 (also refreshing the target field every 6 tiles/20 rounds on big maps) failed the gain gate vs v75 (52% over 1,792, gems −4 ± 10): slower retargeting cancels the gain. Not included.
- B203 on top (no-bush back-off): fuel-exhausted turns vs prof-aynir, v76-without → v76: 02tangle 171 → 134, 04orchard 126 → 104.
