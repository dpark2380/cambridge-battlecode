# v70: v69 + B170, five-pick drafts without Vesper

**Change (`src/profile.h`):** five picks are Marcella, Heart of Ruin, Vendetta, Ryth, Varg (v69: Vesper instead of Vendetta). No draft at any team size takes Vesper now: three picks HoR/Ryth/Marcella, four HoR/Ryth/Marcella/Varg (B171c, folded in before submission).

**Also (`src/bot.cpp`, B175):** for 30 rounds after seeing an enemy, a carrier banks from 20 gems instead of the 36-gem bag (`threat_tribute_gems`).

**Why:** dropping Vesper from four-pick drafts was already marginally positive (B165d, 54% over 364). The top 10 draft her 65% of the time but win 52% with her on engine 3 (scout 6 Nov), and our Vesper has needed special fight rules since v27 (B73, B99). Five-pick swaps on v69 (arena on the 81 five-pick maps, 1 seed): Vendetta for Vesper 184/324 = 57% (CI 51-62%); Vendetta for Marcella 126/324 = 39%.

**Gates vs v69:**
- nonreg, all 128 maps: PASS 278/512 = 54%.
- gain (55%): PASS after 768 games, 417/768 = 54%; submitted gems +29.5 ± 14.9, deaths −0.7 ± 0.4, gems captured +18.4 ± 13.7.
- B171c, four picks with Varg for Vendetta (on v70): arena on the 26 four-pick maps, 4 seeds, 155/260 = 60% (CI 54-65%); nonreg PASS 266/512 = 52%, gems +34 ± 20; gain FAIL (pair score ~0.50: only a fifth of the maps change). Folded in like v68's targeted change.
- Also tried on v70: five picks Ren for Varg 51%, Tavi for Varg 46% (B171a/b, rejected).
- B175, threat bag 20 (on v70): gain gate inconclusive after 3,328 games, 52%; submitted gems +22.5 ± 8.2, deaths −0.0 ± 0.2, captured +3.2 ± 7.2. Folded in before submission.
- Also rejected on v70: B173 Ryth swaps (50%, 40%), B174 HoR half-health soak (49%).
- Final v70 (with B171c and B175) vs v69, nonreg on all 128 maps: PASS 276/512 = 54%; submitted gems +48.2 ± 19.8, deaths −0.7 ± 0.5.

**Live (version 88, live 13:41:54Z 6 Nov).** Panel v70p1 52-38: vs v69p1 (90 paired) 53 → 52 wins, margin −24 ± 56, neutral; vs v64p3 44 → 52, better. Kept; replaced by v71.
