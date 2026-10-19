# Turn-based strategy research and experimental directions

Research date: 2026-10-16.

This note collects lessons from turn-based programming competitions and tactical games, and translates them into CAMBC experiments. External examples provide ideas, not evidence that those ideas win in CAMBC. Local results below are reported in existing experiment summaries; they were not rerun for this note.

## 1. Should team members explore different strategies?

Yes: give developers distinct hypotheses while sharing a baseline, SDK utilities, pathfinding, logging, and an evaluation harness. Avoid duplicating infrastructure across long-lived independent bots. Keep experimental changes separable so useful components can be combined.

Expect convergence on fundamentals—efficient actions, low idle time, distinct farming targets, safe banking—but do not assume one fixed strategy dominates every map and opponent. Economic, interception, and territory strategies may have different strengths or counter one another. Such matchup cycles are hypotheses until measured.

Within a match, champions should take complementary jobs under a coordinated plan. Separate developer experiments do not imply giving champions incompatible strategic agendas.

### Suggested exploration tracks

| Track | Hypothesis | Evidence to seek |
| --- | --- | --- |
| Economic optimizer | Better farming and banking cycles win without frequent combat | Faster scoring against passive opponents, maintained under pressure |
| Combat and interception | Short favorable engagements earn more than uninterrupted farming | Enemy downtime and stolen gems exceed our deaths and lost farming time |
| Territory and objectives | Central camps and altar approaches let us restrict enemy income | Sustained score advantage after charging for guarding, grouping, and travel |
| Learning and evaluation | Tuning or small learned evaluators improve strategic decisions | Gains on held-out maps, drafts, and different opponent styles |

For a smaller team, prioritize economy and combat, with shared evaluation work. Use short experimental milestones. Preserve unsuccessful strategies as test opponents when they expose useful weaknesses.

## 2. Comparisons with other games

### Halite III: optimize the complete resource cycle

The winning bot scored mining locations using a model of travel, collection, filling a ship, and depositing its cargo. Ships claimed targets to reduce duplication. Combat evaluation included cargo value and local control. The author reports that planning a subsequent mining location did not help because those predictions were unreliable.

**CAMBC experiments:**

- Score camps by expected banked gems per champion-turn, including walking, clearing, capturing, banking, and recovery.
- Prefer productive complete cycles over the nearest camp in isolation.
- Compare stable short-cycle plans with longer multi-camp routes.
- Keep target claims so independent farmers do not duplicate effort.
- Include carried gems and future farming downtime when valuing a fight.

**Limits of the analogy:** Halite has simultaneous movement and centralized fleet control. CAMBC alternates champion actions and restricts each champion's observation and communication.

Source: [teccles, Halite III winning bot and write-up](https://github.com/teccles-halite/halite3-bot).

### Battlecode 2024: simple candidate-square combat evaluation

Cout for Clout describes replacing complicated movement rules with a framework that scores candidate squares using ranges, cooldowns, support, and congestion. Their experiments also found that leaving three units as permanent defenders significantly weakened the main force.

**CAMBC experiments:**

- Evaluate legal movement destinations and action sequences with a small combat score.
- Estimate damage dealt and received before the champion's next opportunity to act.
- Count allies by whether they can actually contribute in time, rather than by proximity alone.
- Avoid blocking allied movement, attack positions, and escape routes.
- Compare temporary altar escorts with permanent guards, charging both for lost farming income.

The transferable idea is effective local positioning and explicit opportunity cost; the exact unit counts and combat rules do not transfer.

Source: [Cout for Clout, Battlecode 2024 postmortem](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf).

### Ants: reachable threat maps and updated commitments

Anthony VH's first-hand account describes a combat approximation based on where units could move and threaten next turn. Fixing a friendly unit's chosen move and updating the combat estimates reduced decisions that depended on unsupported assumptions about other units. Exhaustive combat calculation was too expensive for that implementation.

**CAMBC experiments:**

- Build small local threat maps from reachable walking, dash, attack, and spell positions.
- Evaluate a destination after plausible enemy responses, not just against current positions.
- Distinguish confirmed support from support that requires an ally to move or abandon a channel.
- Update local assessments after observed actions and communicated commitments.
- Compare cheap conservative threat bounds with a small tactical search.

**Limits of the analogy:** Ants used simultaneous turns and different combat resolution. CAMBC must model the actual alternating action sequence and changing starting team. An individual bot cannot centrally commit actions for its teammates.

Source: [Anthony VH, AI Challenge: Ants](https://www.anthonyvh.com/2013/03/27/ai_challenge-ants/).

### Lux AI Season 2: tune economic and aggressive decisions together

The third-place competitor describes C++ logic controlled by roughly 1,500 parameters, spanning target selection, combat, movement conflicts, and economic versus aggressive behavior. Outcomes and game statistics were used to test assumptions.

**CAMBC experiments:**

- Expose a manageable set of decision weights and thresholds rather than copying that parameter count.
- Tune grouping, contesting, banking, recall, and upgrade choices against diverse opponents.
- Record explanatory metrics alongside wins so improvements can be attributed to behavior.
- Validate tuned settings outside the games used to select them.

Source: [SiestaGuru, Lux AI Season 2: Final notes and parameter tweaking](https://www.kaggle.com/competitions/lux-ai-season-2/writeups/siestaguru-final-notes-and-parameter-tweaking).

### Wesnoth: allocate force according to geography

Wesnoth's advanced tactics guide distinguishes wide-map expansion from close-map formations, and discusses concentrating force on one front while holding another cheaply or drawing opponents away with threats.

**CAMBC experiments:**

- Spread farmers on open maps and temporarily concentrate at contested approaches.
- Compare travel times to objectives before sending reinforcements.
- Take income elsewhere when an enemy group commits to a distant objective.
- Test whether a credible threat can divert enemy farmers at a favorable cost.

**Limits of the analogy:** Wesnoth terrain defense bonuses, zones of control, recruitment, and retaliation rules are not CAMBC mechanics. Transfer the allocation principle, not the literal tactics or numerical force ratios.

Source: [Wesnoth advanced tactics](https://wiki.wesnoth.org/AdvancedTactics).

## 3. CAMBC strategy avenues, ranked for exploration

### A. Faster farming cycles

Break each champion's time into travel, clearing, capture, banking, recovery, combat, and idle/stalled turns. Improve the largest avoidable cost first.

- Assign distinct opening targets and maintain claims.
- Use walking distance and complete camp-to-altar cycles.
- Track respawn timing with uncertainty when a camp has not been observed recently.
- Avoid excessive waiting for help or repeated target switching.
- Join a camp only when the improvement in clearing, survival, or protection beats the alternative use of that champion.

**Measure:** captures per champion per 100 rounds, banked gems per champion-turn, rounds to 1,000, recovery time, and idle time.

### B. Better camp combat

- Optimize basic attack / reset / attack sequences where legal.
- Schedule spells for damage, stuns, and movement compatibility.
- Choose monster kill order to reduce incoming group damage.
- Position Varg to exploit splash against grouped monsters.
- Test range-four spells against range-three monsters, including full-cycle speed rather than damage avoidance alone.
- Compare builds by resulting clear time and recovery needs, not isolated stat efficiency.

Safe spell-only damage may be too slow because of cooldowns. Confirm behavior in the runner before building a strategy around it.

### C. Combat that understands escape

- Compare fighting, walking, stunning, and dashing over a short horizon.
- Estimate whether an escape actually reaches safety before lethal damage.
- Retreat toward reachable cover, allies, or spawn access instead of always toward spawn.
- Focus targets whose removal prevents the most future damage or secures valuable gems.
- Account for Cassi and Issac's linked death when selecting targets and managing their exposure.
- Model action order and round boundaries; priority changes affect the next round, not the current one.

**Measure:** deaths, gems lost and stolen, enemy downtime, damage efficiency, time spent chasing, and income forgone while fighting.

### D. Map-specific force allocation

- Compare independent farming with temporary pairs on congested maps.
- Precompute useful opening assignments and routes during the draft.
- Prioritize central zero-damage resource clusters when access is favorable.
- Reinforce only when arrival time changes the outcome.
- Trade objectives across the map when contesting would be unprofitable.

Avoid treating grouping as permanently good or bad: it improves local combat but sacrifices parallel work.

### E. Banking and altar control

- Choose banking trips using bag size, walking detour, threat, channel duration, and remaining score needed.
- Commit long enough to avoid work/bank oscillation, while allowing meaningful new threats to change the plan.
- Test escorts, altar locks, and tribute interruption against opponents that create those situations.
- Protect a winning bag instead of continuing unnecessary farming or shopping.

Tribute duration grows approximately linearly with bag size. Larger batches mainly save travel and rounding overhead; they do not eliminate most channel time and expose more carried value. Ordinary damage does not interrupt tribute; stuns, death, and opposing altar locks do.

### F. Objective and champion specialization

- Evaluate monolith strategies against the income obtainable from ordinary camps over the same period.
- Compare champion-specific builds and assignments: splash clearing, field shopping, sustain, mobility, burst, or stun immunity.
- Test whether Cassi and Issac's extra parallel worker outweighs their linked-death risk on each map.
- Refit draft preferences after gameplay changes: observed champion strength depends on how well the bot uses the kit.

### G. Offline learning and small runtime evaluators

- Tune strategic weights and thresholds through batch matches.
- Fit small fight/flee or camp-selection evaluators.
- Learn draft tables and map-conditioned preferences offline.
- Treat a small recurrent policy as an experimental track, with early inference-fuel and training-interface checks.

See [RL feasibility](rl-feasibility.md) for reported simulation and inference measurements. Large-model successes in other games do not establish that such models fit CAMBC's runtime budget; conversely, the budget does not prove small learned policies cannot work.

## 4. Existing local evidence

| Reported result | Implication | Source |
| --- | --- | --- |
| v4 reduced aggregate rounds to 1,000 against starter by about 22% compared with v3 | Independent farming with claims and stall fixes was a substantial improvement | [Simon v4](../../bots/simon/docs/v4/summary.md) |
| Daniel v5 beat its previous baseline 102/162 games with varied drafts | Tuned positioning and strategic decisions improved that matchup | [Daniel v5](../../bots/daniel/docs/v5/summary.md) |
| v5 did not materially improve raw farming pace against starter | Further economic gains likely require structural changes | [Daniel v5](../../bots/daniel/docs/v5/summary.md) |
| Adding capture contesting to Daniel v5 scored 78/162 against v5 | No measurable improvement in that local test; not an established winning feature | [Simon v6](../../bots/simon/docs/v6/summary.md) |
| Earlier ranked replays showed farming losses on open maps and repeated deaths on contested maps | Test economic throughput and aggressive combat separately | [Simon v4](../../bots/simon/docs/v4/summary.md) |

These results are specific to their versions, maps, drafts, and opponents. Local opponents largely share a code lineage and may underrepresent aggressive play. Earlier ranked weaknesses require fresh replays before being treated as current facts.

## 5. Evaluation and convergence

Maintain a matchup matrix across economic, aggressive, territory-focused, and frozen historical bots. Swap sides and vary drafts; repeated identical deterministic games are not independent evidence. Report results by map and opponent as well as in aggregate.

- Develop on one set of games; confirm on held-out configurations.
- Record score margin, scoring speed, deaths, gem transfers, and time allocation alongside wins.
- Preserve specialized opponents even when they are weaker overall.
- Promote changes for broad performance, not only for beating the current champion.
- Combine independently useful components, then retest the combination because interactions can reverse gains.
- Select map-dependent behavior only when there is enough evidence to justify the extra complexity.

Policy-population research provides a useful conceptual model: evaluate and improve against mixtures of strategies rather than a single training partner. We can apply this to hand-written bots without adopting its RL machinery. This does not prove CAMBC has a particular equilibrium or a rock-paper-scissors matchup structure.

Source: [Lanctot et al., A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning](https://arxiv.org/abs/1711.00832).

## 6. Candidate winning plan

**Hypothesis:** farm independently by default, concentrate briefly for profitable fights, and protect the tribute that wins the match.

1. **Opening:** assign distinct efficient targets and contest central income only when access and local strength justify it.
2. **Economy:** maintain several farming streams; add help where it improves total team output.
3. **Pressure:** exploit short upgrade or cooldown advantages to remove a vulnerable farmer, steal a valuable bag, interrupt a tribute, or secure access; then return to productive work.
4. **Defense:** identify danger early; when escape is impossible, use attacks and abilities effectively rather than walking while taking damage.
5. **Finish:** when existing carried gems can close the game, prioritize safe banking over additional resources.

The turn-based opportunity is precise scheduling: arrival times, respawns, cooldowns, captures, channels, and action order. The next three high-value experiments are camp-clear optimization, banking-route optimization, and combat against a genuinely aggressive opponent.

## 7. Concrete bot architectures to try

These are architectural adaptations, not drop-in compatible bots. The Java sources use different APIs and game mechanics; our implementations must respect personal vision, the eight-byte team buffer, alternating turns, and the fuel limit.

### First experiment: Battlecode candidate-action combat evaluator

References: [postmortem](https://battlecode.org/assets/files/postmortem-2024-cout-for-clout.pdf), [public repository](https://github.com/jonters/battlecode24), and [attacker source](https://github.com/jonters/battlecode24/blob/main/src/waxingmoon/Attacker.java).

The documented architecture scores possible movement directions using combat features. Our proposed extension is to score a bounded set of legal action sequences:

1. Generate candidates such as attack and stay, move and attack where legal, cast then retreat where legal, dash, or attack/reset/attack.
2. Estimate damage dealt, damage received before the next action, escape options, allied support, objective progress, and carried-gem exposure.
3. Reject illegal sequences, select the best candidate, and execute it with fresh legality checks.
4. Reobserve after actions that reveal new information or otherwise change the situation.

Keep farming and drafting unchanged for the first A/B experiment. Daniel v5's `fight_enemies()` in `bots/daniel/v5/src/bot.cpp` currently compares nearby total health before attacking or retreating; this is a contained replacement point. The low-health branch in `take_turn()` also retreats before reaching the normal combat routine, so evaluate whether that branch must call the new evaluator to address retreat deaths.

Measure actual fuel use; bounded local evaluation is a candidate for the budget, not a verified performance guarantee.

### Economic experiment: Halite utility planner with task commitments

References: [winner's algorithm and repository](https://github.com/teccles-halite/halite3-bot), [entry point](https://github.com/teccles-halite/halite3-bot/blob/master/MyBot.java). The entry point delegates to `bots.current_bot.Bot`; it is not the whole strategy.

Halite's documented resource-cycle scoring and claims resemble our current camp selection. The proposed CAMBC extension is a common task interface for:

- Farming a camp or capturing a cleared region.
- Banking at a specific altar.
- Recalling and upgrading.
- Intercepting a visible carrier or temporarily escorting an ally.

Each candidate reports expected reward, duration, risk, confidence, and the cost of abandoning the current task. A selector accounts for allied claims and chooses a task; its executor takes the next legal action. Calibrate values to comparable units so arbitrary scores do not silently prioritize every fight over every farming opportunity.

This replaces some of `take_turn()`'s fixed ordering among fighting, banking, shopping, and farming. Keep hard action constraints and channel handling explicit. Add commitment or a switching penalty to prevent oscillation, with overrides for meaningful new threats.

### Supporting component: Ants reachable-threat maps

Reference: [implementation account](https://www.anthonyvh.com/2013/03/27/ai_challenge-ants/). A working source download was not verified; the algorithm is described in the article.

Maintain separate estimates for immediate attack coverage, threats reachable after movement/dashes, and support allies can provide in time. Feed these estimates to the combat evaluator and route selection. Do not count a unit as occupying several possible positions simultaneously when calculating an exact outcome; reachable-threat unions are conservative approximations.

Unlike a centralized Ants controller, an individual CAMBC champion cannot commit teammates' actions. Use observed actions and compact communicated intentions, with age/confidence, rather than assuming allies will make the expected move.

### Proposed combined pipeline and rollout

```text
Observation + remembered information
                 |
Task selection and commitment       (Halite-inspired)
                 |
Legal action-sequence generation
                 |
Threat and outcome evaluation       (Battlecode/Ants-inspired)
                 |
Execution and reobservation
```

Test the combat evaluator first against unchanged Daniel v5 and an aggressive opponent. Test the task planner separately, then combine only after measuring both components and their interaction. Existing helpers and the world model should be reused before considering a larger rewrite.

## 8. Top-match observations

See [top replay analysis](top-replay-analysis.md) for an evidence-based analysis of the supplied Swirl match. It distinguishes timestamped observations from inferred roles and records candidate follow-up experiments.
