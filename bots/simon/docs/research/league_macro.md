# League of Legends macro → CAMBC strategy notes

Research note, October 2026. It translates League of Legends (LoL) macro ideas into strategy for our CAMBC
bot. Everything about CAMBC comes from `docs/GameRules.md`, `maps/ascii/*.txt`, the v3/v4 summaries
and the decoded v3 replays against the +200 bot (`replays/v3/analysis/*.stats.json`). LoL ideas are
cited in [Sources](#6-sources).

Confidence tags used throughout:

- **[rules]**: follows directly from GameRules.md or the map dumps.
- **[replay]**: seen in our replays or summaries.
- **[calc]**: back-of-envelope arithmetic from base stats. No items, no walking, ideal targeting.
- **[spec]**: speculation. Plausible but untested in the engine. Verify before building on it.

---

## 1. The CAMBC ↔ LoL mapping

| CAMBC | Closest LoL equivalent | How well it maps |
|---|---|---|
| Camp group (cardinally connected monsters) | A jungle camp (Wolves, Krugs, Raptors) | Good. Multi-monster groups reward AoE clear, as in LoL. |
| Wolf (1350 HP, 20 dmg, 22 gems, 90 g, 40 r respawn) | Small camp (Murk Wolves, Raptors) | Good. Cheap, safe, fast respawn. |
| Elk (2400 HP, 60 dmg, 36 gems, 160 g, 60 r) | Big camp (Krugs/Gromp) | Good. Hurts melee solo farmers. |
| Gem / gold cluster (500 HP, 0 dmg) | Scuttle crab / plants: free value with no fight | Good, and *more* important than scuttle, since they cost no HP. |
| Monolith (20,000 HP, 200 dmg, 200 gems + 300 g; groups on `monolith`/`rows` give 392/448 gems) | Baron / Dragon: epic, team-sized, contested | Good. One capture is ~40% of the win target. |
| 5-round capture on a spawn tile after the kill | The vulnerable window around securing an objective (the Smite fight) | Partial. Anyone stepping on the region resets it, so a capture can be *stolen or denied* without damage. |
| Gems (win at 1000 tributed) | Victory points. No direct LoL equivalent; closest is "structures taken" | Weak. Score is gathered, not sieged. |
| Carried gems lost to the killer on death | Shutdown bounty | Strong. Bigger bag means bigger bounty, and the swing is double: we lose it *and* they gain it. |
| Tribute at altar (`ceil(gems/10)` turns, stun or lock cancels) | Recall to spend: turning unbanked value into permanent value at a fixed place, through a vulnerable channel | Good. Altars are also chokepoints the enemy must visit (like Baron pit). |
| Altar lock (10 g, blocks enemy tribute) | Zoning an objective / a control ward denying a play | Partial. |
| Gold → shards (30 g) → emblem (5 shards, passive) | Components → completed item (stat lump, then passive) | Good. Item spikes are discrete, as in LoL. |
| Power emblem (6 shards' stats, no passive) | Stat-efficient item with no passive | Good. |
| Home emblem (recall 5 → 3 turns) | Homeguard / Baron-buffed recall | Good. |
| Spawn tiles (heal, shop, enemies can't enter) | Fountain | Good. There are no towers, so there is no "under tower" between fountain and the field. |
| Recall (5 turns, damage cancels) | Recall (8 s, damage cancels) | Very good. |
| Death: 60 rounds out | Death timer | Good. No levels, so death costs only time, the bag and 50 g. |
| Ward (one each, permanent, relocatable within 2 tiles each round) | Trinket ward | Partial. Wards never expire, but **vision is not shared**. |
| 8 bytes of shared memory | Pings | Weak. 64 bits total, per team, all match. |
| 1024 bytes of draft memory | Pre-game plan / shot-calling | Unique. A full-map plan computed with 10× fuel. |
| Simultaneous one-by-one draft, picks revealed, no bans | Blind-ish draft with counter-pick on later picks | Partial. Both teams may pick the same champion. |
| Teleport crystal (3-tile hop over terrain, 3-turn channel that damage does not stop) | Flash over a wall, but slow | Partial. A wall-hop escape or shortcut. |
| Tavi buys shards anywhere | Ornn's in-field item crafting | Loose. Gives power spikes with no recall tempo cost. |
| Vesper Vale +20% gold (40% with Treasure) | Gold-generation passives (Twisted Fate, Gangplank) | Loose. |

### Where the analogy breaks

1. **No lanes, minions or towers [rules].** There's no wave state, no lane priority and no siege. All income is "jungle" income, so every LoL lane concept (freeze, slow push, cheater recall) maps only loosely onto camp timers and banking trips.
2. **Gems are lost on death and given to the killer [rules].** A kill is a *score* swing, not only a tempo swing. LoL's nearest analogue is a shutdown bounty, and in CAMBC every carrier always carries one.
3. **Every champion walks 1 tile per turn [rules].** There are no movement-speed items, so you can't outrun anyone. A melee chaser keeps contact and hits every turn, and ranged champions can't move and shoot in the same turn. Disengage, LoL's most important survival tool, comes only from dashes (Issac, Vesper, Vendetta, Ren), stuns, recall (broken by damage) or a slow crystal. **[rules]** This is why v3/v4 died while "retreating" **[replay]**.
4. **No levels or XP.** Power comes only from gold. No passive experience scaling and no level-6 spike: the only spikes are emblem completions and Focus/Strength shard thresholds.
5. **Monsters attack the nearest champion of either team, never chase, never heal, and sleep after 2 rounds out of range [rules].** No leashing or resetting. Partially cleared camps stay damaged, so another team can finish and steal them. An awake camp is a hazard for whoever stands nearest.
6. **Fixed 2000-round cap; the game usually ends far sooner** (our 5 losses ended at r375–490) **[replay]**. It's a race, more like a speedrun than a 35-minute LoL game.
7. **No shared vision, and 8 bytes of comms [rules].** LoL macro assumes five players who see the same minimap and talk. Our bots each see 8 tiles plus their own ward. Any "team call" must fit in a few bits.
8. **Capture rewards are split among the allies present [rules].** In LoL, two people on one camp waste tempo. In CAMBC, two bodies on one group literally halve the reward per body. The opponent's solo farming is the LoL "don't double-jungle" rule.

---

## 2. Roster archetypes

Draft enum: 0 Ryth, 1 Vesper, 2 Vendetta, 3 Cassi & Issac, 4 Stellar, 5 Prism, 6 Marcella, 7 Willow,
8 Ren, 9 Varg, 10 Tavi.

**Solo-clear sheet [calc].** Sustained camp damage per turn is `Str + Str/8 if it has an attack reset + Σ damage spells / 8`
(8-turn cooldowns, one cast per turn). "Range-4 safe" is the part from range-4 spells. Monsters hit at range 3 **[rules]**,
so a caster standing at Chebyshev distance 4 deals this damage while taking none **[spec: verify that range is
Chebyshev for monsters too and that a waking camp does not retarget]**.

| Champion | HP | Camp dmg/turn | Range-4 safe | Notes |
|---|---|---|---|---|
| Cassi | 700 | 47.5 | 17.5 | Stun 4 |
| Issac | 900 | 45 | 0 | Dash, reset |
| Ryth | 1200 | 69 (AoE r1 spell) | 12.5 | +1 Str per 100 bonus HP |
| Vesper Vale | 900 | 51 | 0 | +20% gold, dash |
| Prism | 700 | 60 (AoE r1 spell) | 25 | +0.2 Focus/carried gem |
| Stellar | 750 | 77.5 (AoE r1 spell) | 42.5 | Highest spell damage |
| Vendetta | 800 | 79 | 0 | Kills (incl. monsters) reset cooldowns |
| Marcella | 1200 | 63 | 12.5 | Stun immune |
| Tavi | 750 | 67 | 27.5 | 220 burst + stun, shops anywhere |
| Willow | 700 | 51 | 0 | Heals ally 315 / 8 turns |
| Ren | 900 | 56 + 20 per hit taken | 15.6 | Retaliation also triggers on camps **[spec]** |
| Varg | 1000 | 56 per target; splash ≈ 2× on 2-wolf, ≈ 3× on 3-wolf columns | 0 | Shield 250 every 8 turns |

Worked examples **[calc]**:

- **Varg on a 2-wolf group** (packs, monolith, expanse): ~112/turn, so ~24 turns. He takes 40/turn, ~960 in total, minus ~750 of shields, so ~200 HP lost. That fits the opponent's Varg taking 44 gems every ~45 rounds alone on packs **[replay]**.
- **Varg on an elk** (2400 HP, 60 dmg): ~43 turns. He takes ~2580 minus ~1250 of shields, more than his 1000 HP, so he can't solo it at base. With a Jungle emblem (−30% camp damage) and health shards it becomes plausible.
- **Stellar, spells only, from range 4**: a wolf takes ~32 turns and an elk ~56, with **zero damage taken**.

### Archetype table

| Pick | LoL role | Justification |
|---|---|---|
| **Varg** | AoE clear jungler / juggernaut | Splash basic attacks (radius 1) and a 250 shield every 8 turns make him the best multi-monster farmer. 1000 HP, Str growth 5. The opponent picks him on every wolf-pack map **[replay]**. |
| **Cassi & Issac** | Two-body "duo lane"; parallel farming | **Two bodies for one pick**, so a solo-farm comp gets +1 capture stream. Downsides: linked death (killing Cassi at 700 HP kills both and pays both bags), and both are fragile. The opponent picks them in all 5 games **[replay]**. |
| **Vendetta** | Assassin / skirmisher, fast clear | Highest base Str (70). Camp kills reset dash and reset, so she chain-clears multi-monster groups, and an enemy kill resets everything for the next target (a Katarina-like reset). 800 HP is low. Picked by the opponent on packs and expanse **[replay]**. |
| **Stellar** | Burst / poke mage (Syndra, Xerath) | 200 single target + 140 AoE at range 4. The opponent's Stellar went 5/0 on collision and 3/0 on interlock **[replay]**. Also the best zero-damage camp poker. Squishy. |
| **Tavi** | Pick mage + item flexibility | 220 burst + stun at range 4 is the strongest single spell in the roster. He shops anywhere, so he never pays recall tempo for a spike, and he can sell at spawn to rebuild for the situation. |
| **Ren** | Tank / warden, anti-dive | 900 HP, stun at range 4, dash, and retaliation that punishes whoever focuses him. Good at holding a capture region or an altar. Picked by the opponent on collision, interlock and monolith **[replay]**. |
| **Ryth** | Engage tank (Amumu / Sejuani) | 1200 HP, ground AoE stun radius 1 at range 4: the only multi-target stun. Health shards also add Str. A slow farmer. |
| **Marcella** | Juggernaut, anti-CC frontline (Olaf-ult-style) | 1200 HP and **immune to stuns**, with a stunning enhanced attack. Hard counter to stun-heavy comps (Cassi, Tavi, Prism, Ren, Ryth). Low Focus (50). |
| **Prism** | Control mage / battle mage | Stun spell (1.5×) + AoE (1×), both range 4. Gets Focus from carried gems, which rewards hoarding, i.e. carrying a bigger bounty. A weak trade: 100 gems give only +20 Focus. |
| **Vesper Vale** | Marksman / economy carry | Strong ranged basic attack (45 Str), a reset that lets her move *and* attack in one turn, a dash, and +20–40% gold. Gold only converts to stats and the tiebreak, so her value is indirect **[spec]**. |
| **Willow** | Enchanter support | 315 heal per 8 turns, the lowest growth in the roster. In a solo-farm meta a healer who must stay near an ally is a weak pick **[spec]**. Her best case is babysitting a fragile carrier (Cassi). |

Draft notes:

- Every champion has the same vision (8) and the same walk speed (1), and every ability has an 8-turn cooldown **[rules]**. The roster differentiates on HP, damage profile, stuns and mobility only.
- Stun sources: Cassi, Ryth (AoE), Prism, Tavi, Ren, Marcella (enhanced attack). Stuns cancel tributes, recalls and crystals **[rules]**, so they are also anti-banking tools.

---

## 3. Candidate metas

Map facts **[rules]**:

| Map | Size / picks | Altars | Key camps |
|---|---|---|---|
| packs | 31², 3 | 6, on the side columns | 6 × 2-wolf (44 g), 2 central free gem+gold 4-clusters (48 gems, 0 dmg) |
| collision | 41², 3 | **2**, both central-east (27,20), (39,20) | Single wolves/elks; 108-gem elk+3 gem group in each team's far corner |
| expanse | 80², 3 | 10, spread out | 6 free gem pairs (48), 4 × 108-gem elk+3g, 2-wolf groups |
| interlock | 40², 4 | 4 | 2 × 72-gem free gem triples near the centre |
| rows | 50², 4 | **2** | 6 × 3-wolf columns (66 gems, a Varg dream), central double monolith (448 gems) |
| corners | 71², 5 | 5, incl. centre (35,34) | **4 × 48-gem free gem pairs next to the centre altar (192 free gems per 50 rounds)**; 96-gem 2-elk+gem groups |
| elkring | 30², 5 | **2** | 10 × elk+gold (36 gems, 195 g); no wolves |
| lanes | 90×30, 5 | 18 | Mirrored single camps; banking is cheap everywhere |
| monolith | 50², 5 | 6 | Monolith+8 gem groups (392 gems) in the two *neutral* corners, each next to an altar |

### Meta A: "Five junglers" (parallel solo farm). Baseline; this is what beat us.

- **Comp:** Cassi & Issac (2 bodies), Varg, plus Vendetta on 3-pick maps. Add Ren and Stellar on 4–5 picks. This is the opponent's packs/expanse draft **[replay]**.
- **Plan.** *Early:* each body takes the nearest group it can survive alone. Squishy bodies take zero-damage clusters (the opponent's Cassi took 240 gems and 0 gold on expanse: clusters only **[replay]**). *Mid:* Monster or Power emblem on the main damage stat, then Power. *Late:* keep farming and bank on the way.
- **Win condition:** capture rate. ~1000 gems by r375–430 **[replay]**.
- **Spikes:** first emblem (150 g) on Varg/Vendetta. Varg reached 7 Power shards on packs **[replay]**.
- **Beats:** grouped or duo comps (our v3: about half their capture rate).
- **Loses to:** teams that punish isolated bodies (Meta B), and capture-denial. LoL equivalent: the farming jungler gets invaded by a stronger 2v1 (dodge.gg: invade when you can fight or escape).
- **Maps:** expanse, packs, lanes, rows. Large or symmetric maps with many groups and few contested chokepoints.

### Meta B: "Pick and invade" (hunt the solo farmers)

- **Comp:** Stellar + Tavi + Cassi & Issac (3 picks); add Ren on 4, and Varg or Vendetta on 5. That is three range-4 stuns or nukes plus a cleaner. The opponent's collision draft, Stellar + C&I + Ren, is a lighter version **[replay]**.
- **Plan.** *Early:* farm your own side, ward the approaches between the two halves. *Mid:* when a lone enemy body is seen near our farmers, especially one standing on a capture region or walking to an altar with a bag, collapse with whoever is within ~6 tiles. *Late:* camp the altars the enemy must use.
- **Burst [calc]:** Stellar 200 + Tavi 220 + Cassi 140 = 560 in one round at range 4, plus two stuns. That nearly kills Cassi (700) or Stellar (750) from out of their basic-attack range.
- **Win condition:** take their bags (score swing ×2) and their time (60 rounds per death plus the walk back).
- **Spikes:** Focus shards on the casters. +10 Focus is +20 on Stellar's nuke and +22 on Tavi's.
- **Beats:** Meta A, especially C&I-heavy drafts. One Cassi kill pays both bags.
- **Loses to:** tanky stun-immune frontlines (Marcella, Varg with shields) and grouped teams. Also loses to its own idle time: hunting without kills is lost farm (LoL: a gank that forces nothing is wasted time, dodge.gg).
- **Maps:** collision, interlock, packs. Small maps with central altars and frequent contact.

### Meta C: "Altar control" (siege the chokepoint)

- **Comp:** Ren or Marcella (anchor) + Ryth (AoE stun) + Stellar or Tavi (burst), with C&I as a farmer. 3–5 picks.
- **Plan.** On maps with **2 altars** (collision, rows, elkring), both teams must bank at the same two tiles. Ward both altars. Keep a tanky body farming camps near the altar we don't use. Stun or lock enemy tributes (a stun cancels the tribute and the gems are still carried **[rules]**) and kill carriers who have to stand still for `ceil(gems/10)` turns.
- **Win condition:** the enemy can't bank, so their bags grow, so the payoff of each kill grows. LoL equivalent: vision setup around an objective before it spawns (wecoach, Guild Order).
- **Beats:** solo farmers who bank late with large bags.
- **Loses to:** teams that bank early and often with small bags. Also loses on maps with many altars (expanse, lanes: 10 and 18).
- **Maps:** collision (both altars east-central, 24–36 tiles from each spawn), elkring, rows. **[spec]** for how far to commit.

### Meta D: "Objective team" (monolith siege)

- **Comp:** Stellar, Tavi, Prism, Cassi & Issac, plus Varg for the clear afterwards. Maximise range-4 spell damage.
- **Idea [spec]:** monsters hit at range 3 and don't chase **[rules]**. Casters at range 4 cast only spells and take nothing. Range-4 damage: Stellar 42.5 + Tavi 27.5 + Prism 25 + Cassi 17.5 = **~113/turn at base [calc]**, so ~180 turns for 20,000 HP. That's too slow at base. Ten Focus shards spread across them (300 g in total) add only ~0.3 damage/turn per Focus point, so roughly 145/turn and ~140 turns, for 392 gems + 300 gold. That's ~2.8 gems/turn for 4 bodies, about the same as solo farming (~0.6–0.7 gems/turn/body **[replay]**). And it can be stolen at the end (LoL: secure Baron only with vision and the enemy elsewhere, dodge.gg).
- **When:** mid-game, after Focus spikes, when enemy bodies are seen far away or dead. LoL equivalent: Baron after a won fight.
- **Beats:** pure farm comps on monolith/rows, if the monolith isn't contested.
- **Loses to:** any team that walks in and contests the 5-round capture, or that farms faster meanwhile.
- **Maps:** monolith (groups in neutral corners beside altars), rows (448 gems in the centre).
- **Status:** the most speculative meta. Test the range-4 claim on a local match first. It's cheap to test (`cambc run` on monolith with a caster-only bot).

### Meta E: "1-3-1": side farmers plus a centre group

- **Comp (5 picks):** Varg on one side's wolves; C&I split as two side farmers or one per side; Stellar + Ren + Tavi as the centre trio.
- **Plan:** the trio holds the free central gem clusters and the central altar. They farm zero-damage gems and bank instantly, while side farmers take wolves and elks. The trio's job is to win any 3v1/3v2 that walks into the centre. LoL equivalent: "1-2 champions with strong 1v1 plus a team that can 4v4"; a split works when the enemy must send more than one to answer (Dignitas, mobalytics).
- **Win condition:** take the richest zero-risk income (on corners, 192 gems per 50 rounds at the centre) while keeping side parallelism.
- **Beats:** Meta A teams that send lone farmers to the centre, and teams that cede the centre (our v3 on corners lost 454–1000 by ceding it **[replay]**).
- **Loses to:** a full 5-man collapse on the trio (rare for bots), or a faster pure farm if the centre is uncontested anyway.
- **Maps:** corners (prime), interlock (2 × 72-gem free triples), packs (3-pick version: one centre body).

### Meta F: "Economy scaling" (Vesper + Treasure). Listed for completeness.

Gold only buys stats and decides the tiebreak; games are decided by gems long before r2000 **[replay]**. A Vesper Treasure build (+40% gold) buys roughly 2 extra shards per 5. That is unlikely to beat parallel farming **[spec]**. Skip it unless games start reaching r2000.

### Meta matchup sketch [spec]

| | A: Five junglers | B: Pick | C: Altar control | E: 1-3-1 |
|---|---|---|---|---|
| **A** | Farming race | Loses if B finds isolated bodies | Wins if it banks small and often | Loses the centre, wins the sides |
| **B** | Wins | Coinflip; vision decides | Even | Loses to the trio |
| **C** | Wins only on 2-altar maps | Even | | Even |
| **E** | Wins on corners/interlock | Wins | Even | |

---

## 4. Transferable principles

Each line gives: the rule, the LoL concept, the CAMBC mechanic. **SM** means it needs shared memory (and how many
bits). **local** means each body decides alone. **draft** means it can be precomputed into the 1024-byte draft memory.

### Farming and pathing

1. **One body per group unless the group demands more.** *(Jungle tempo, don't double-jungle.)* Rewards split among capturers **[rules]**. v4 already does this with claims. **SM** (claims, 36 bits).
2. **Squishy bodies take zero-damage clusters; tanky splash bodies take wolf packs; elks go to Jungle-emblem or Varg bodies.** *(Champion-appropriate clear routes: Graves/Udyr full clear vs gank junglers.)* Matches the opponent's split **[replay]**. **draft** (assign per role).
3. **Clear on the way, not at the destination.** Pick the next group by `gems / (travel + max(travel, respawn) + kill + capture)`, as v4 does, and treat an altar on the path as a free bank. *(Pathing by camp timers to minimise downtime, dodge.gg.)* **local**.
4. **Track every group's respawn from the moment you saw it captured or saw its tiles empty.** Respawn = the longest member cooldown after capture **[rules]**. Arrive at `respawn − travel`; never stand on a spawn tile, which delays the respawn **[rules]**. *(Camp timers, counting enemy CS.)* **local**, and cheap with world.cpp's cache.
5. **Open on the camp with range-4 spells before stepping into range 3.** A free ~1–2 spells of damage per engagement **[spec]**. *(Smite/ability poke before committing.)* **local**.
6. **Never finish a camp at low HP when a visible enemy is near.** The capture needs 5 uncontested rounds, and the enemy can walk on and reset it, or kill you and take the capture. *(Don't start Baron with enemies alive nearby, dodge.gg.)* **local**.

### Banking (tribute) and recall

7. **Bag-size cap by risk.** Bank when `carried ≥ G_max`, with roughly G_max = 60–80 when no enemy has been seen recently and 25–40 when one has, or when an altar is within ~6 walking tiles of the path. Tribute time is linear in the bag (1 turn per 10 gems **[rules]**), so batching only saves walking, and a big bag is a big bounty. *(Recall at real breakpoints rather than reflexively; a shutdown bounty grows.)* **local**, tunable per map. **[spec]** on the exact numbers. Measure from replays.
8. **Bank before fighting when you can.** If an enemy is seen and an altar is within reach before contact, tribute first: damage doesn't interrupt a tribute, only stun, death or a lock does **[rules]**. *(Back before the fight with gold you'd otherwise lose.)* **local**.
9. **Recall only out of contact.** Damage cancels a recall **[rules]**, so it isn't an escape. *(Don't recall when spotted, mobalytics.)* Start recalling when no enemy has been visible for 2+ turns and no camp is in range 3. **local**.
10. **Shop at breakpoints.** Recall to shop only when gold ≥ the next meaningful purchase: the 5th shard of an emblem, i.e. the passive. Partial shards help less. *(Unspent gold is wasted, but don't back without a breakpoint, metabot.)* **local**. Home emblem on the bodies that recall most.

### Fighting

11. **Decide at vision range, not at contact.** Walk speed is equal and there's no kiting **[rules]**, so once a melee enemy is adjacent, walking away means taking a hit every turn while dealing nothing. The v3/v4 deaths happened exactly this way **[replay]**. Rule: on first sight (≤ 8 tiles), compare local strength. If weaker, leave *then*, away from their approach, or bank or recall if no damage is incoming. If already in contact with a melee enemy, **fight back** unless a dash, stun or an ally ≤ 3 tiles away changes the outcome. *(Vision lets you choose fights; turning your back gets you killed.)* **local**.
12. **Count allies in a wider radius and move toward them, not toward spawn.** Our collision deaths had 3,600 HP of allies 12 tiles away vs 2,120 enemy HP **[replay]**. *(Forcing a fight with a numbers advantage, mobatrainer; fight where your team is.)* Needs ally positions, which vision doesn't give **[rules]**, so **SM**: e.g. each body publishes a coarse position (2 bits quadrant + 1 bit "in fight") = 3 bits × 5 bodies = 15 bits. Doesn't fit next to v4's 36 claim bits + 22 danger bits; see section 5.
13. **Focus order: Cassi or Issac first, then the biggest bag, then the lowest effective HP, then stunners.** Linked death pays both bags and removes two farmers **[rules]**. *(Focus the squishiest high-value target, hotspawn/metabot.)* **local**.
14. **Stun the tributer or recaller; lock the altar if you can't.** A stun cancels both channels and the bag stays killable **[rules]**. *(Interrupt the back / zone the objective.)* **local**.
15. **Spend cooldowns before fighting, not after.** All abilities run on 8-turn cooldowns **[rules]**. A body with both slots on cooldown should avoid contact for those turns. *(Fight on cooldown advantage.)* **local** (own cooldowns); enemy cooldowns are probably not observable **[spec]**.
16. **Fight beside our spawn or an awake enemy-nearest camp.** Spawn heals us and enemies can't enter it **[rules]**. An awake camp hits whichever champion is nearest **[rules]**, so luring a chaser into one is free damage **[spec]**. *(Fight under your tower.)* **local**.

### Counter-jungling and objectives

17. **Contest enemy captures.** An enemy standing alone on a cleared region for 5 rounds, probably damaged from the clear, is the best gank target in the game. Stepping onto the region resets their capture without a fight **[rules]**. *(Invade right after the enemy jungler shows on a ward or finishes a camp; Smite-steal, dodge.gg.)* **local** plus a **SM** "enemy capturing at group X" flag (6 bits group + 1 bit).
18. **Invade only with local superiority and a known enemy position.** Steal their groups when the nearest enemy body was last seen far away or dead. *(Invade when the jungler is on the other side, dodge.gg.)* **SM**: last enemy sighting (x, y, round), which v4's danger marker already almost is.
19. **Trade objectives across the map.** If the enemy commits to a monolith or the centre, take their side groups instead of walking into a losing fight. *(Objective trading, cross-mapping; Guild Order, mobatrainer.)* **SM** (needs a sighting).
20. **Never cede free central income.** Zero-damage gem clusters at the centre (corners, interlock, packs) are the cheapest gems in the game. *(Scuttle and river control.)* v3 lost corners partly by ceding them **[replay]**. **draft** (mark them as contested priority targets).

### Vision

21. **Drop the ward on the enemy-side approach to the group you're farming**, within 2 tiles, each time you arrive. Wards are permanent and replaced by the next one **[rules]**, so each body keeps one live "tripwire". It turns rule 11 from "contact" into "6+ tiles of warning". *(Defensive vision vs invades; ward the river before objectives, mobatrainer, dodge.gg.)* **local**. v4 uses no wards at all.
22. **When banking at a contested altar, ward it first.** With 2-altar maps, a ward left on each altar's approach gives that body the enemy's banking pattern. **local**. Broadcast it as a sighting via **SM**.

### Draft

23. **Always take Cassi & Issac early** on solo-farm maps. It's the only pick that gives 2 bodies; the opponent took it in 5/5 **[replay]**. Since picks are revealed one by one and duplicates are allowed **[rules]**, taking it never denies it, but missing it costs a body. **draft**.
24. **Counter-pick on later picks.** Enemy has 2+ stunners → Marcella. Enemy has C&I → Stellar or Tavi (burst through 700 HP). Enemy has Varg on wolves → a range-4 caster to contest. *(Counter-pick.)* **draft**.
25. **Precompute the map plan in draft memory:** per group, which side owns it (walking distance from each spawn), its nearest altar, its role tag (cluster / pack / elk / monolith), its ward spot, and whether it's "contested centre". That uses ~4–6 bytes per group, under 200 bytes for 30 groups. *(Pre-game plan, win-condition by comp.)* **draft**.

### Shared-memory budget (64 bits)

v4 uses 36 bits of claims (6 × 6) and 22 bits of danger marker **[replay: v4 summary]**. Rules 12, 17 and 18 compete
for the same space. Two layouts that fit **[spec]**:

- **Sighting-centric:** claims 30 bits (5 bodies × 6) + one *enemy sighting* word: x 7, y 7, round mod 64 6, "carrying ≥ 30 gems" 1, "capturing" 1 = 22 bits. That leaves 12 bits for a **rally/fight call** (group or tile index 7 bits + round 5 bits).
- **Fight-centric:** claims 30 bits + 5 × 6-bit "body status" (quadrant 2, HP bucket 2, in-fight 1, carrying-big-bag 1) = 60 bits. The sighting is dropped.

---

## 5. Recommendations for our bot

Ranked by expected impact against a solo-farming +200 opponent vs implementation effort. The farm gap is already
narrowed by v4. The remaining losses are fights (collision, interlock: 12 deaths each **[replay]**).

| # | Idea | Impact | Effort | Principles |
|---|---|---|---|---|
| 1 | **Fight-or-flee decided at sight, never at contact.** On first sight, compare local HP+damage including allies seen recently. If weaker, disengage then. Once a melee enemy is adjacent, hit back with everything (spells, resets, stuns), using a dash or stun only to break contact. Ranged bodies with no escape stand and shoot rather than walk away. | **High.** Directly targets the 20/24 deaths that happened while retreating. | Low–Med: changes `retreat()` / fight logic. | 11, 13, 15 |
| 2 | **Wards as tripwires** at each target on the enemy-side approach, plus at contested altars. Makes #1 work by giving warning beyond 8 tiles. | Med–High | **Low**: one call per arrival, needs a chosen tile. | 21, 22 |
| 3 | **Bag cap tied to threat.** Bank at ~30 gems when any enemy was seen in the last ~30 rounds, otherwise ~70. Prefer banking before contact; stun or lock enemy tributers we see. Cuts the bounty we hand over and keeps our score safe. | Med | Low: thresholds in the banking commit. | 7, 8, 14 |
| 4 | **Punish captures.** When a body sees an enemy standing alone on a cleared region (or walking to an altar with a bag) and local strength ≥ 1.2× theirs, engage or just step onto the region to reset it. Publish "enemy capturing at G" in shared memory so nearby claimants can join. This is the only idea that *takes away* the opponent's farm rather than racing it. | **High** vs a solo farmer **[spec]** | Med: target selection plus a shared-memory slot (see the sighting layout). | 6, 17, 18 |
| 5 | **Draft like the opponent, then counter.** C&I always. Varg on packs, rows, expanse, monolith. Stellar + Ren on collision and interlock (their 3/3 kill-heavy comps). Marcella vs 2+ stunners. Explicit "contested centre" tags for corners, interlock and packs (Meta E). | Med | Low: draft scoring tweaks. | 2, 20, 23–25 |

Worth a quick experiment, not a priority: **range-4 spell opening on camps** (rule 5) and **monolith siege** (Meta D).
Both rest on one engine fact: a caster at Chebyshev 4 isn't hit. One local match tests it. If it holds, rule 5 is a
free clear-speed gain for every caster, and Meta D opens 392/448-gem objectives that v4 skips today.

Not recommended now: Meta F (economy), Willow, and Prism's gem-hoarding passive.

---

## 6. Sources

LoL macro (community coaching guides; patch-specific numbers are not relied on here):

- dodge.gg, *Jungle Guide for League of Legends (2026): clear routes, gank timing, objective priority, tracking*: <https://www.dodge.gg/en-US/lol/news/jungle-guide-2026>. Full clear vs 3-camp; gank checklist ("fewer than two conditions → farm"); invade when the jungler is shown elsewhere; don't start Baron with enemies near; CS-count tracking.
- wecoach.gg, *How to Play Jungle in League of Legends*: <https://wecoach.gg/blog/article/how-to-play-jungle-in-league-of-legends>. Camp timers and path efficiency.
- wecoach.gg, *League of Legends Objectives Guide*: <https://wecoach.gg/blog/article/league-of-legends-objectives-guide>. Set up vision before objectives; trading objectives.
- tapin.gg, *Beginner's guide to jungle (2026)*: <https://tapin.gg/blogs/beginners-guide-jungle-league-of-legends-2026>.
- metabot.gg, *When to Recall: Back Timing and Gold Economy*: <https://metabot.gg/en/league/guides/when-to-recall-back-timing-economy>. Back at buyable breakpoints; tempo cost of recall; unspent gold.
- mobalytics.gg, *5 Best Recall Timers*: <https://mobalytics.gg/blog/lol-5-best-recall-timers/>. Don't recall when spotted or before an objective fight.
- MOBA Trainer, *LoL Macro Patterns Map*: <https://www.mobatrainer.com/patterns>. Crossmap, forcing fights on numbers advantage, objective setups, defensive vision.
- MOBA Trainer, *Teamfighting*: <https://www.mobatrainer.com/guides/teamfighting>. Front line / peel / backline / dive jobs.
- Dignitas, *Split Pushing 101*: <https://dignitas.gg/articles/blogs/League-of-Legends/14349/split-pushing-101-an-in-depth-league-of-legends-guide>. Who splits, when to group, punishing the answer.
- mobalytics.gg, *How to Play the 1-3-1*: <https://mobalytics.gg/blog/lol-how-to-play-1-3-1/> (403 when fetched; summarised from search results).
- Guild Order, *Objectives reference*: <https://guildorder.com/games/league/wiki/objectives-reference>. Vision before objectives; trade Baron for Dragon.
- procomps.gg, *The Engage Comp*: <https://procomps.gg/blog/engage-gamestyle.html>; mobalytics, *How to play the engage comp*: <https://mobalytics.gg/blog/lol-how-to-play-the-engage-team-comp/>; EarlyGame, *Team-comp archetypes*: <https://earlygame.com/de/lol/lol-guide-team-comps>. Engage / pick / poke / protect / split archetypes.
- LoLTheory, *Engage & Disengage*: <https://blog.loltheory.gg/engage-disengage-lol/>; hotspawn, *How to Teamfight*: <https://www.hotspawn.com/league-of-legends/guide/how-to-team-fight-in-league-of-legends>. Focus fire, peel, disengage.
- LoLTheory, *How to Play From Behind*: <https://blog.loltheory.gg/how-to-play-from-behind-in-league-of-legends/>; mobalytics, *7 ways to play from behind as a jungler*: <https://mobalytics.gg/blog/7-ways-to-play-from-behind-as-a-jungler/>. Deaths cost more when behind; don't gank losing lanes.

CAMBC (local):

- `docs/GameRules.md`: camps, capture, tribute, items, vision, death and the roster.
- `maps/ascii/*.txt`: map grids and camp-group rewards.
- `bots/simon/docs/v3/summary.md`, `bots/simon/docs/v4/summary.md`.
- `replays/v3/analysis/*.stats.json`: opponent drafts and per-champion stats. Draft ids decoded via `sdk/rust/src/types.rs`.
