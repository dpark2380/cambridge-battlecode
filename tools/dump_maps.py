#!/usr/bin/env python3
"""Write maps/ascii/<map>.txt for every map (or the named ones) by running tools/mapdump in the engine.

    python3 tools/dump_maps.py                 # every maps/*.map26a
    python3 tools/dump_maps.py ambush swirl    # just these

tools/mapdump is a Python bot that records its team size during the draft and prints the grid, legend and
camp groups on its first game turn, from Team A's perspective. Each map plays 5 rounds against starter-python.
"""
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMBC = shutil.which("cambc") or str(Path.home() / ".local/bin/cambc")
sys.path.insert(0, str(ROOT / "tools"))
import arena  # noqa: E402


def dump(name, scratch):
    out = scratch / name
    subprocess.run([CAMBC, "run", str(ROOT / "tools/mapdump"), str(ROOT / "bots/starter-python"),
                    "--map", name, "--rounds", "5", "-o", str(out)], cwd=ROOT, capture_output=True, check=True)
    text = zipfile.ZipFile(next(out.glob("*.repl26a"))).read("team-a.stdout").decode()
    picks = re.search(r"@@PICKS (\d+)", text).group(1)
    body = text.split("@@DUMP-BEGIN\n", 1)[1].split("@@DUMP-END", 1)[0]
    body = body.replace("MAPNAME", name, 1).replace("None picks", f"{picks} picks", 1)
    (ROOT / "maps/ascii" / f"{name}.txt").write_text(body)
    return name, body.splitlines()[0]


def main():
    names = sys.argv[1:] or arena.maps()
    with tempfile.TemporaryDirectory() as tmp, ThreadPoolExecutor(8) as pool:
        for name, header in pool.map(lambda n: dump(n, Path(tmp)), names):
            print(header)


if __name__ == "__main__":
    main()
