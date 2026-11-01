#!/usr/bin/env python3
"""Per-map camp-group capture lists, ours vs the opponents, from a scrim panel version (stdlib only).

    python3 tools/captures.py v47            # data/scrims/v47: captures and gems per group per game, both sides

Panel sides are fixed per map, so a group id is the same side in every game of a map. One capture = one
(side, group, round) in the gemCollection events; gems are what that side received. Rewards come from
maps/ascii/<map>.txt. Process review 2026-11-01 H1: equal capture counts, half the gems captured (B128).
"""
import collections
import gzip
import json
import re
import sys

import features

ver = sys.argv[1]
rows={json.loads(l)['match']:json.loads(l) for l in open(f'data/scrims/{ver}/features.jsonl')}
def rewards(mapname):
    out={}
    for l in open(f'maps/ascii/{mapname.replace("_","-")}.txt'):
        m=re.match(r"# G(\d+) (\{.*?\}) gems=(\d+) gold=(\d+)",l)
        if m: out[int(m[1])]=(m[2],int(m[3]),int(m[4]))
    return out
permap=collections.defaultdict(lambda:collections.defaultdict(lambda:[0,0,0,0]))  # map -> gid -> [our caps, our gems, their caps, their gems]
games=collections.Counter(); tot=[0,0,0,0]
for mid,r in rows.items():
    p=f'data/scrims/{ver}/summaries/{mid}.json.gz'
    try: s=features.load(p)
    except FileNotFoundError: continue
    games[r['map']]+=1
    seen=set()
    for e in s['events']:
        if e['kind']!='gemCollection': continue
        mine=e['owner']['team']==r['side']
        for x in e['entries']:
            if x['context']!='campGroup': continue
            gid=x['target']['id']; rnd=x['timestamp']['round']
            key=(mine,gid,rnd)
            c=permap[r['map']][gid]; i=0 if mine else 2
            if key not in seen: c[i]+=1; seen.add(key)   # one capture per group per round per side
            c[i+1]+=int(x['value'])
for mp,g in sorted(permap.items()):
    rw=rewards(mp); n=games[mp]
    ours=sum(v[0] for v in g.values())/n; theirs=sum(v[2] for v in g.values())/n
    og=sum(v[1] for v in g.values())/n; tg=sum(v[3] for v in g.values())/n
    tot[0]+=ours;tot[1]+=og;tot[2]+=theirs;tot[3]+=tg
    print(f"\n== {mp} ({n} games): captures/game us {ours:.1f} them {theirs:.1f}; gems captured us {og:.0f} them {tg:.0f}")
    diff=sorted(g.items(), key=lambda kv:(kv[1][3]-kv[1][1]), reverse=True)
    for gid,(oc,ogm,tc,tgm) in diff[:4]+[d for d in diff[-2:] if d not in diff[:4]]:
        comp,gems,gold=rw.get(gid,('?',0,0))
        print(f"   G{gid:<3d} {comp:28s} gems={gems:<4d} gold={gold:<4d}  us {oc/n:4.1f} caps {ogm/n:5.0f} gems | them {tc/n:4.1f} caps {tgm/n:5.0f} gems")
print(f"\nALL maps avg: captures us {tot[0]/len(permap):.1f} them {tot[2]/len(permap):.1f}; gems captured us {tot[1]/len(permap):.0f} them {tot[3]/len(permap):.0f}")
