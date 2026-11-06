# v65: v64 + B152, Heart of Ruin engages only with a large edge

**Change (`src/bot.cpp`, `fight_enemies`):** Heart of Ruin engages a fight only with a 1.5x power edge (allied health × damage against the enemies'). Other bodies keep 1.2x, and Vesper keeps 1.3x.

**Why (ranked v62-v64, 1,460 games, per 1000 rounds):**

| | Our Heart of Ruin | Opponents' Heart of Ruin |
|---|---|---|
| Champion damage | 6.0k | 4.3k |
| Camp damage | 8.6k | 12.7k |
| Camp damage taken | 3.7k | 5.8k |
| Deaths | 2.5 | 1.6 |

Every other champion is within 17% of its counterpart's camp damage. Ours fights where theirs farms. Two alternatives were rejected first:
- B151, buying strength instead of focus: profgate −134 ± 24.
- B150, bigger bags: −17 / −56.

**Local results:**
- profgate vs v64: margin −8 ± 23. The profile bots share our fight code, so this test cannot see the change.
- nonreg vs v64: PASS, 172/344 = 50%.

**Decision metrics:** panel `v65p2` vs `v64p2` (`panelcmp.py`): margin, deaths, and Heart of Ruin camp damage from the summaries.

**Result:** Fair test on engine 3.0.0 (v65p2 vs v64p3, paired 90): wins 44 → 39, margin −50 ± 33, gems −42 ± 22 (z −2.0), deaths −0.3 ± 0.5; the first comparison against v64p2 (engine 2.0.0) was invalid. **Rejected**; v64 re-uploaded 07:23Z (version 83). v64 itself fell from 51 wins (v64p2, engine 2.0.0) to 44 (v64p3, engine 3.0.0).
