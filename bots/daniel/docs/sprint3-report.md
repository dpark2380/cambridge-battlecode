# Sprint 3 report (deadline 2026-11-01 00:00Z)

**Live at the deadline: v41 = v38 + B100 fuel cache, team bot version 54**, chosen as the best proven bot:
198-177 over 375 ranked games since 2026-10-31 10:56Z (23:49Z), ladder **#182 of 814, rating 1749**.

## Ladder path (UTC)

| Time | Rank | Rating | Live bot |
|---|---|---|---|
| 30 Oct 13:00 | #265 | 1651 | v38 (version 47) |
| 30 Oct 19:15 | #213 | 1715 | v39 (version 49) |
| 30 Oct 21:15 | #241 | 1677 | v38 again, after v39's revert |
| 31 Oct 02:30 | #187 | 1745 | v38 → v40 (version 50) |
| 31 Oct 10:40 | #261 | 1660 | v42 (version 53), reverted |
| 31 Oct 14:14 | #222 | 1707 | v41 (version 54), 100 games |
| 31 Oct 18:04 | #199 | 1730 | v41, freeze |
| 31 Oct 23:01 | #208 | 1714 | v41 |
| 31 Oct 23:49 | **#182** | **1749** | v41 (final check) |

Rank ≤180 (≈1750) was missed by two places: #182 at 1749 at the final check, the sprint's best.

## Versions tried

| Version | Change (backlog) | Local evidence | Ranked | Outcome |
|---|---|---|---|---|
| v38 | v34 + B109 (02guardians gate) | map gate 62%, nonreg 50% | 55-45 first 100; 83-62 over 145; later windows 33-47, 22-28 | benchmark |
| v39 | v38 + B111 Willow on six maps | top-60 scout (65-79% with Willow); map gate 52% | 63-67 over 130, Willow maps 2-9 | reverted |
| v40 | v38 + B112a lone Vesper/HoR fall back | 19 loss replays; panel 27-63 (-3 deaths/game) | 22-28 over 50 (= v38's 22-28 later) | reverted; indistinguishable |
| v41 | v38 + B100 fuel cache (retry) | gain on fuel maps 54% (inconclusive), nonreg 49% | 22-28 over 50, then **198-177 over 375**; fuel-exhausted turns 6.3/game vs 17.5-18.5; fuel maps 4-3 vs 8-14 | **deadline bot** |
| v42 | v41 + B113b early gold weight 0.5 | race 59%, **gain gate PASS 55%** | 11-19 over 30 | reverted |

## Findings (backlog B110-B116)

- **B110**: scrim-panel opponents changed between versions, so panels compare only when run close together.
- **Near our equilibrium (~1680-1745) every bot wins about half**: v38 and v40 both went 22-28 over 50 at the same
  rating. Short ranked windows cannot separate close bots; opponents' gold is not a field-strength measure (it rises with
  our own deaths through kill gold).
- **B114**: 260-team scout (5,784 games): we die 12 times a game vs 6-7 in every rank band, but in losses top teams die
  12.9 times too. Deaths follow losing. Against ranks 150-260 we have the same game shape and win 41% vs 49%.
- **B115**: we bank 30 small bags a game (median 17) vs 20-24 bags of 22-26 everywhere else; bigger bags lose locally
  (44-47%), so this suits our bot.
- **B116**: 02fields (0-5) has no single target-choice fix.
- Local gains (v40 panel, v42 gain gate 55%) did not carry over to ranked; real-opponent evidence is the only reliable
  test.

## Next sprint

(Updated 2026-11-01 21:30Z after the process review, `docs/research/process-review-2026-11-01.md`.)

1. Judge every change on the paired panel v2 (`tools/panelcmp.py`), never on short ranked windows; the panel is deterministic within the hour, so one run per candidate is exact on its 90 setups.
2. Economy: the gap is gems per capture (746 vs 866 a game with equal captures). Next targets from `tools/captures.py`: 00vault's cluster, gem-only clusters on 02the_pond/00galaxy, elk groups on 01big_world/01islands, and B130 (the contested elk group on 00eight).
3. Build the review's #8 (handicapped-candidate local test) and #9 (profile bots from panel opponents' summaries) so local gates can see fight changes.
4. Base: v51 (v48 + B128a + B129).

## Tournament result (read from the platform's bracket, 2026-11-03)

Sprint 3: single elimination, 713 teams, 15 games per pairing, played on unseen maps (not the ladder pool). Our entry was
team bot version 54 (v41). Seed **#186**. Round 1: bye. Round 2: beat #327 Give me a job **9-6**. Round 3 (last 256): lost
to #71 dromedaries **1-14**. Out in round 3 of 10, i.e. placed 129th-256th.

The international qualifier locks **Tue 3 Nov, 23:59 GMT** (the platform's schedule: "All dates and lock deadlines are in
UK time"); tournaments use only unseen maps.
