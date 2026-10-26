# v13 summary (from v12)

## Change: B29, the_pack corridor

**Evidence.** v12's first 30 ranked games (to 06:45Z) went 24-6. One loss was 02the_pack at 0:0, lost on gold.
Locally v12 vs v11 was 0:0 in all 6 games there. The map's only altar (22,22) is inside one 48-wolf group (G0).
`move_towards_closest` finds no path through living camps, so a banking carrier stands still for the rest of the
game. The top 20 tribute there from r473-585, before any G0 clear (r582+): they cut a way in.

**Rules that shape it.** Damage wakes the whole group, every member hits the nearest champion within 3 tiles,
and monsters do not chase. Carriers standing at the ring are safe; whoever strikes first draws the hits.

**Change.**
- In `init`, if every walk from our spawn to an altar crosses a camp (`altar_walled`), run a 0-1 BFS from our
  spawn, costing one kill per camp tile entered. The camp tiles on the cheapest path are the `corridor`; on
  the_pack that is one wolf, entered diagonally.
- In `go_tribute`, when the walk to the altar fails, `breach()` runs. A carrier waits within 3 tiles of the
  corridor. Once 2 allies (1 on a two-body team) are within 3 tiles, it steps up and strikes the corridor member in
  reach.

**Errors on the way.**
- Striking alone: the carrier died at the ring 3 times a game (+8 gems vs v12).
- Waiting for allies at whichever ring tile each carrier reached: they never met, so nobody struck.
- Waiting only on the corridor's neighbours: just 2 tiles touch it, so the third carrier couldn't get close.
- The BFS read bitboards with `is_set`, an engine call costing about 150 fuel, so init took about 50 turns. The
  fix copies the masks into local grids with one `positions()` call each.

**Results.**
- Gate `map` on 02the_pack vs v12: 51/60 = 85%, pass.
- Gate `nonreg` on all 70 maps (280 games each): 51% vs v12, 57% vs v11, 66% vs Jame v3, all pass.
- Only 02the_pack sets the flag (probe: `plan: altar walled in` on 70 maps). Other maps differ from v12 only
  through fuel timing from the extra init work.

**Weaknesses / next.**
- Non-carriers don't help; the breach starts once enough carriers are banking.
- Gems are lost if the striker dies with them; it is usually still the winning trade.
- A carrier never chooses not to bank.
