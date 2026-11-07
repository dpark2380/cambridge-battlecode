# v75: v74 + B198, gold saturation

**Change (`src/bot.cpp`, `choose_target`):** a body carrying more than 150 unspent gold weights gold at 0.3× in every group's value (`gw`), so it prefers gems over gold groups until it next shops.

**Why:** v74's ranked games broken down by map family (220 games, 7 Nov 02:20Z): the 42 new 04* maps went 30-43, every other family 55-70%. Since v67, 04orchard 0-3 (gems 310 vs 1003) and 04wheel 0-4. In the ranked replays we submitted 0 gems by r300-r500 on both while opponents banked from r100-200. On 04orchard we earned 9-17k gold with 2-11 banks a game: bodies kept farming gold they could not spend.

**Gates:**
- arena vs v74 on all 42 04* maps, 1 seed: 92/168 = 55% (CI 47-62%). Weight 0 above 100 gold (b198b): 48%.
- gain vs v74 on all 128 maps: **PASS** 276/512 = 54%; submitted gems +23 ± 21, captured +19 ± 18, gold −78 ± 121.

**Rejected alongside (B199):** a lone Monolith's value ×1.5 (ranked opponents take it 2.2 a game on 04yin_yang and 04duel_ring, we never): arena on the 23 lone-Monolith maps 36/92 = 39%.
