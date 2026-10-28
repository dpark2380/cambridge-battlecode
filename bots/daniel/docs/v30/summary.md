# v30: v27 + B80 (Ryth and Marcella leave earlier against pairs)

## Evidence
v27 ranked, first 30 games (`replays/daniel-v27/timelines`, `tools/fights.py` plus a death-context script):
- 38% of our deaths come on the walk home: Ryth 63%, Marcella 53%.
- Eight rounds before dying, Ryth averaged 56% health with 1.7 enemies within 5; 58% of its deaths had 2+ enemies
  that close. Marcella: 56% health, 1.1 enemies, 34% of deaths with 2+.

General fixes lost locally: leaving earlier at 60% (B67-dr6) 45%, falling back to an ally (B69) 46%.

## Change
Ryth and Marcella leave at 65% health when 2+ enemies are within 5.

## Results (`data/b80-race.txt`, `data/b80-gates.txt`)
- Race vs v27: 54% (75/140). Gain gate vs v27: 51% (285/560), FAIL, so neutral locally.
- Nonreg PASS vs v12 78%, Jame v3 91%.
