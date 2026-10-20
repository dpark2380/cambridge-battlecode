# Jame bot versions

Jame is an independent implementation using the official C++ SDK and the repository's common build and match tools. Teammates' gameplay, drafting, world models, parameters, and communication code are not imported or copied.

Planning references: [draft selection and champion behavior](draft-selection.md), [top-team popular picks and candidate rosters](../../../docs/research/top-team-picks.md). Confidence-ranked future version plans are in the project's `TODO.md`; v1 remains the baseline.

| Version | Source | Notes | Status |
| --- | --- | --- | --- |
| v1 | [v1/src](../v1/src/) | [v1 summary](v1/summary.md) | Validated mechanics baseline; retain for future comparisons |
| v2 | [v2/src](../v2/src/) | [v2 summary](v2/summary.md) | Reliability/scoring experiment; mixed improvement across opponents |
| v3 | [v3/src](../v3/src/) | [v3 summary](v3/summary.md) | Abilities, equipment, resupply and planning fixes; validated results recorded per opponent |

## Version discipline

- Keep each meaningful strategy iteration in its own `bots/jame/vN/` folder with matching `docs/vN/summary.md`.
- Once a version is validated and recorded, retain it as a baseline; develop meaningful behavior changes in the next version.
- Record behavior, policy assumptions, results, problems, and omissions. A passing smoke match is not evidence of a winning strategy.
- Use explicit bot paths in commands because other teammates also have `v1`, `v4`, etc.
- Build caches, compiled Wasm, logs, and replay bundles remain local; commit source and concise notes to Git when ready.
- Run local matches only; submitting a bot is a separate action.

## Commands

From the repository root:

```sh
.venv/bin/cambc build bots/jame/v3
python3 tools/batch.py bots/jame/v3 bots/jame/v2
python3 tools/batch.py jame simon

# Historical v2 comparison:
.venv/bin/cambc build bots/jame/v2
python3 tools/batch.py bots/jame/v2 bots/jame/v1

# Historical v1 baseline:
.venv/bin/cambc build bots/jame/v1
.venv/bin/cambc run bots/jame/v1 bots/starter-cpp --map swirl --view
.venv/bin/cambc run bots/starter-cpp bots/jame/v1 --map swirl --view
PATH="$PWD/.venv/bin:$PATH" python3 tools/arena.py bots/jame/v1 bots/starter-cpp
```
