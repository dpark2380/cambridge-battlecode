# Draft selection: champion kit versus controller

Planning note, 2026-10-17. This records a selection approach; it does not change Jame v1's draft or gameplay.

## What is hard-coded?

The engine fixes each champion's stats, growth, attack class/range, passive, and two abilities. For example, Varg's basic attacks splash, Vesper gains bonus gold, and Cassi/Issac share a death. These differences apply even when our controller does not explicitly branch on champion identity.

The engine does **not** supply each champion with an intelligent playstyle. Every champion runs its own instance of our program. Our code must choose targets, movement, spells, purchases, banking, and cooperation. We may share general logic and dispatch a small amount of kit-specific behavior; eleven completely separate bots are not required.

Jame v1 currently uses the same basic policy for all champions and never casts spells or buys equipment. Ranged/melee differences and passives still happen through the engine, but it cannot reproduce a top team's spellcaster or support behavior simply by drafting the same character.

Rules reference: [champion roster](../../../docs/GameRules.md#champion-roster). SDK metadata lives in `sdk/cpp/cambc.h`.

## Can we copy a strong team's roster initially?

The user's later [top-team popular-pick screenshots](../../../docs/research/top-team-picks.md) provide a broader starting point: Cassi & Issac + Stellar appears in 15 of 16 visible rows, most often alongside Ren (8 rows), followed by Varg (4), Tavi (2), and Willow (1). The remaining row shows Stellar + Tavi + Ren. These are displayed popular picks, not verified per-map teams or draft order. Start experiments with Cassi & Issac, Stellar, Ren and vary the third pick while holding gameplay fixed. The hooded blond portrait is Tavi, not Ryth.

We can copy picks as an independently implemented fixed **experimental control**. Separately, the winning roster in the previously inspected Swirl match was Ren, Stellar, Cassi & Issac, and Ryth. It is a plausible four-pick candidate to test once our controller uses the kits. It is one observed game, not a current leaderboard-wide optimum or evidence that its first three picks are the best three-pick team.

Risks of copying only the picks:

- Focus-scaling spellcasters lose much of their value if our code never casts.
- Sustain, resets, crowd control, and upgrades change camp-clear and fight outcomes.
- Cassi/Issac add a body but can lose two farmers and both bags when either dies.
- The same roster may need different assignments on different maps.
- Published/replayed drafts reflect another team's implementation, which we are not copying.

Keep v1 unchanged and compare the reference roster against our existing SDK-order draft with identical gameplay. Do not simultaneously change abilities, builds, and picks and then attribute the gain to drafting.

## What would optimal selection mean?

Maximize the probability of winning with **our actual controller**, given the map, roster size, previously selected allies, previous revealed enemy picks, and the opponent population we expect. There is no demonstrated universal best roster. Current-round opposing picks remain hidden, and both teams can choose the same champion, so this is not a denial/bans problem.

Composition search is tractable offline: 11 choices yield 165 unordered three-pick teams, 330 four-pick teams, or 462 five-pick teams. Cassi/Issac is one choice in those counts. Those counts exclude pick order; default gameplay priority uses draft order as a tie-break, so execution order is an additional variable that must be controlled or tested.

A practical progression:

1. Implement and verify a small set of useful champion actions.
2. Pick a few fixed rosters, including the observed reference and our baseline.
3. Evaluate complete rosters on both sides and representative maps against varied opponents, holding gameplay and action-order assumptions constant.
4. Identify marginal substitutions, then recheck the complete team: individual champion rankings do not capture synergy or duplication.
5. Use results to choose by map features (camp mix, distances, chokepoints, altar access), not only by a specific named map.
6. Only then add counter-picking from previously revealed picks if it improves held-out results.
7. Refit after substantial controller changes. Retain a simple fixed draft as a regression control.

Most of this computation belongs offline. The draft bot can ship a small tested table or scoring rule and write an opening plan into 1,024 bytes of draft memory. Its extra first-turn fuel is useful for static map analysis, not an invitation to run a large tournament inside the live draft.

The immediate priority is using the characters we draft competently. Fixed picks are reasonable initially; copying a roster alone cannot establish optimality.
