# v69: v68 + B167, Vendetta in four-pick drafts and Varg in five-pick drafts

**Change (`src/profile.h`):** four picks are Heart of Ruin, Ryth, Marcella, Vendetta (v68: Vesper instead of Vendetta). Five picks are Marcella, Heart of Ruin, Vesper, Ryth, Varg (v68: Vendetta instead of Varg). Varg has no profile build, so it uses v66's `build_order` for its stat.

**Why:** B164 showed the draft per team size matters more than our build. Rosters tried on v68 (arena on that size's maps):
- 3 picks: HoR/Marcella/Vesper 38%, HoR/Ryth/Vesper 24%, HoR/Ryth/Vendetta 38% over 126 games. v68's HoR/Ryth/Marcella stays.
- 4 picks with Vendetta for Vesper: 196/364 = 54% (CI 49-59%).
- 5 picks, swaps from the top 10's picks: Willow for Ryth 36%, Prism for Ryth 40%, Varg for Vendetta 172/324 = 53% (CI 48-58%).

**Gates vs v68:**
- profgate (180): +11 ± 32 (b165d alone −9 ± 23, b166c alone +20 ± 22).
- nonreg, all 128 maps: PASS 270/512 = 53%.
- gain (55%): inconclusive after 3,328 games, 53%. Submitted gems +47.8 ± 7.4, gems captured +56.6 ± 6.8, gold +204 ± 52, deaths −0.5 ± 0.2.
