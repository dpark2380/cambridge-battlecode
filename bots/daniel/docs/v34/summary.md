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
