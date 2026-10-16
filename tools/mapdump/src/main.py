"""Map dumper for tools/dump_maps.py: prints the grid, legend and camp groups on the first game turn."""
import cambc
import draft
from cambc import game_map, Vec2, Team, CampType

SYM = {0: "horizontal mirror (x reflected)", 1: "vertical mirror (y reflected)", 2: "180-degree rotation"}
KIND = {CampType.WOLF: "w", CampType.ELK: "k", CampType.MONOLITH: "M",
        CampType.GEM_CLUSTER: "g", CampType.GOLD_CLUSTER: "$"}
picks = None


def dump():
    w, h = game_map.width(), game_map.height()
    layers = [(game_map.walls(), "#"), (game_map.holes(), "o"), (game_map.bushes(), '"'),
              (game_map.altars(), "A"), (game_map.spawn_region(Team.ALLY), "S"),
              (game_map.spawn_region(Team.ENEMY), "E")]
    grid = [["."] * w for _ in range(h)]
    for board, ch in layers:
        for p in board.positions():
            grid[p.y][p.x] = ch
    groups = game_map.camp_groups()
    lines = []
    for i, g in enumerate(groups):
        counts = {}
        xs = ys = 0
        for c in g:
            k = KIND[c.kind()]
            counts[k] = counts.get(k, 0) + 1
            p = c.spawn_position()
            grid[p.y][p.x] = k
            xs += p.x
            ys += p.y
        n = len(g)
        lines.append(f"# G{i} {counts} gems={g.gem_value()} gold={g.gold_value()} "
                     f"respawn={g.max_respawn_timer()} at=({round(xs / n)},{round(ys / n)})")
    out = ["@@DUMP-BEGIN",
           f"# MAPNAME: {w}x{h}, {picks} picks per team, symmetry: {SYM[int(game_map.symmetry())]}",
           "# Legend: . floor  # wall  o hole  \" bush  A altar  S team-A spawn  E team-B spawn",
           "#         w wolf  k elk  M monolith  g gem cluster  $ gold cluster (camp spawn tiles)",
           "# Row index is y, column index is x. Dumped via the engine from Team A's perspective.",
           "",
           "      " + "".join(str(x // 10) if x % 10 == 0 else " " for x in range(w)),
           "      " + "".join(str(x % 10) for x in range(w))]
    out += [f"{y:4d}  " + "".join(grid[y]) for y in range(h)]
    out += ["", "# Camp groups (gems/gold per capture, respawn in rounds, centroid of spawn tiles)"]
    out += lines
    out.append("@@DUMP-END")
    print("\n".join(out), flush=True)


def main():
    global picks
    done = False
    while True:
        try:
            if cambc.is_draft():
                if picks is None:
                    picks = cambc.draft.team_size()
                    print(f"@@PICKS {picks}", flush=True)
                draft.play()
            elif not done:
                done = True
                dump()
        except Exception as error:
            print(f"bot error: {error}", flush=True)
        cambc.end_turn()


if __name__ == "__main__":
    main()
