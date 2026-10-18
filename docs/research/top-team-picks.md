# Top teams' popular picks: starting draft candidates

Recorded 2026-10-18 from the user's screenshots: [champion names](assets/champion-list-2026-10-18.png) and [top teams' popular picks](assets/top-team-popular-picks-2026-10-18.png). Portraits were checked against the named artwork shipped in the locally cached official visualizer. The masked silver-haired portrait is **Ren**; the blond hooded portrait is **Tavi**, not Ryth.

These are each team's displayed popular picks, **not necessarily a roster they field together on any particular map**. The screenshot has no team names, match counts, win rates, map breakdown, or patch information. Counts below describe only the 16 visible rows. Display order is not evidence of draft order. Cassi & Issac counts as one champion pick despite its two portraits/bodies.

## What is visible

| Champion | Rows appearing in | Share of visible rows |
| --- | --- | --- |
| Stellar | 16 / 16 | 100% |
| Cassi & Issac | 15 / 16 | 93.75% |
| Ren | 9 / 16 | 56.25% |
| Varg | 4 / 16 | 25% |
| Tavi | 3 / 16 | 18.75% |
| Willow | 1 / 16 | 6.25% |

The displayed triples, ignoring order:

| Popular-pick triple | Visible rows |
| --- | --- |
| Cassi & Issac, Stellar, Ren | 8 |
| Cassi & Issac, Stellar, Varg | 4 |
| Cassi & Issac, Stellar, Tavi | 2 |
| Stellar, Tavi, Ren | 1 |
| Cassi & Issac, Stellar, Willow | 1 |

This suggests starting with **Cassi & Issac + Stellar**, then testing **Ren** as the first third-pick candidate and **Varg** as the first substitution. It is a useful prior for allocating implementation and testing effort, not a measured ranking of champions for our controller. Absence from this cropped screenshot is not evidence that another champion is weak.

## Candidate experiments

1. Three picks: Cassi & Issac, Stellar, Ren. This matches the most common displayed triple; establish competent kit use and compare with the existing baseline.
2. Hold the core and gameplay fixed, substituting Varg, then Tavi, then Willow for Ren. Record camp throughput, banked gems, deaths/lost bags, faults, and match wins on both sides.
3. Test Stellar, Tavi, Ren as an alternative without Cassi & Issac. This checks whether our linked-body handling justifies drafting the duo.
4. For four picks, test the core plus Ren and either Varg or Tavi. For five picks, the core plus Ren, Varg, and Tavi is a small initial candidate pool. These larger rosters are **extrapolations**, not compositions demonstrated by this screenshot. Retain the separately observed Swirl four-pick roster (Ren, Stellar, Cassi & Issac, Ryth) as another control.
5. Keep composition and action-order experiments separate. Validate across map types and different opponents before fitting a map-dependent draft table.

Do not change frozen Jame v1 to match the screenshot. Its controller does not yet use abilities or equipment, so importing popular picks alone may underperform. Implement any new draft in a later version and compare identical gameplay with different rosters. No teammate implementation is needed or copied.

See [draft selection and champion behavior](../../bots/jame/docs/draft-selection.md) and the v3/v4/v6 plans in the project's `TODO.md` for kit support, team coordination, and draft evaluation prerequisites.
