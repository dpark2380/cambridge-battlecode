#!/usr/bin/env python3
"""Audit v2's completed batches, replay diagnostics and scoring progress.

python3 bots/jame/tests/validate_v2.py matches/<run> ... --out matches/v2-audit.json
Counters are the last periodic samples, not exact end-of-game totals. Final
scores/deaths come from engine statistics. Event times are owner-turn observations.
"""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BOT = ROOT / 'bots/jame/v2'


def audit(directory):
    payload = json.loads((directory / 'results.json').read_text())
    bots = {b['name']: b for b in payload['bots']}
    names = {name for name, b in bots.items() if Path(b['path']).resolve() == BOT}
    if len(names) != 1:
        raise ValueError(f'Expected exactly one release v2 in {directory}')
    name = names.pop()
    rows = []
    for pair in payload['pairs']:
        if name not in (pair['a'], pair['b']):
            continue
        first = pair['a'] == name
        opponent = bots[pair['b'] if first else pair['a']]
        for game in pair['games']:
            if game['status'] != 'completed':
                raise ValueError(f'Incomplete game: {game["directory"]}')
            side = 0 if game['aFirst'] == first else 1
            stats = json.loads((Path(game['directory']) / 'statistics.json').read_text())
            log = ''
            for replay in game.get('replays', []):
                with zipfile.ZipFile(replay) as bundle:
                    log += bundle.read(f'team-{"a" if side == 0 else "b"}.stdout').decode(errors='replace').replace('\0', '')
            if 'jame/v2 metrics' not in log:
                raise ValueError(f'Missing v2 diagnostics: {game["directory"]}')
            diagnostics = [line for line in log.splitlines() if 'jame/v2' in line
                           and ('error:' in line or 'turn-overrun' in line)]
            minimum = min(int(n) for n in re.findall(r'min-fuel=(\d+)', log))
            samples = {}
            for line in log.splitlines():
                if 'jame/v2 metrics ' in line:
                    values = dict(re.findall(r'([a-z-]+)=([\w-]+)', line))
                    champion = values.pop('champion')
                    samples[champion] = {k: int(v) for k, v in values.items()}
            def first_event(event):
                values = [int(v) for v in re.findall(rf'event={event} round=(\d+)', log)]
                return min(values) if values else None
            champions = [c for c in stats['champions'] if c['team'] == side]
            score = game['gemsA'] if first else game['gemsB']
            rows.append({'run': directory.name, 'opponent': opponent['name'] if opponent['name'].endswith('/' + opponent['version']) or opponent['name'] == opponent['version'] else f'{opponent["name"]}/{opponent["version"]}',
                         'map': game['map'], 'side': 'AB'[side], 'won': game['aWon'] == first,
                         'gems': score, 'opponentGems': game['gemsB'] if first else game['gemsA'],
                         'rounds': stats['round'], 'gemsPer100Rounds': 100 * score / stats['round'],
                         'collectedGems': sum(c['collectedGems'] for c in champions),
                         'deaths': sum(c['deaths'] for c in champions),
                         'firstCapture': first_event('first-capture'), 'firstBank': first_event('first-bank'),
                         'faults': stats['botFaults'][side], 'diagnostics': diagnostics,
                         'minimumLoggedFuel': minimum, 'lastCounterSamples': samples})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs', nargs='+', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    rows = [row for directory in args.runs for row in audit(directory)]
    result = {'sourceSHA256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted((BOT / 'src').iterdir()) if p.is_file()},
              'games': rows}
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    for opponent in sorted({r['opponent'] for r in rows}):
        games = [r for r in rows if r['opponent'] == opponent]
        wins = sum(r['won'] for r in games)
        print(f'{opponent}: {wins}–{len(games)-wins}; faults={sum(r["faults"] for r in games)}; '
              f'diagnostics={sum(len(r["diagnostics"]) for r in games)}; '
              f'minimum logged fuel={min(r["minimumLoggedFuel"] for r in games)}')
    return int(any(r['faults'] or r['diagnostics'] for r in rows))


if __name__ == '__main__':
    raise SystemExit(main())
