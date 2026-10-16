#!/usr/bin/env node
// Decode CAMBC replays with the visualiser's own engine build (the wasm under
// %LOCALAPPDATA%/cambc/assets/<hash>/visualiser/assets). For every input it replays the
// timeline and writes, next to the input (or into --out):
//   <name>.stats.json     final statistics, same schema as `cambc run --statistics`
//   <name>.timeline.csv   one row per champion per round: position, health, gems, gold, K/D/A
// and prints a per-game report from our team's point of view.
//
// Usage: node tools/replay/analyze.mjs [--us A|B] [--wasm path] [--out dir] <replay.zip|.repl26a|dir>...
// Inputs may be platform downloads (zip: replay.repl26a + team-a.stdout) or local bundles.
// Our team is detected from the "draft: round N picked X" lines our bot logs, unless --us is given.
//
// Byte layouts were calibrated against `cambc run --statistics` output and the visualiser's
// snapshot decoder for engine 0.0.1 (Version() == 65536). Re-check them if the engine changes.
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, mkdirSync } from "node:fs";
import { join, basename, extname, dirname } from "node:path";
import { inflateRawSync } from "node:zlib";
import { WASI } from "node:wasi";
import { homedir } from "node:os";

const CHAMPIONS = ["ryth", "vesper_vale", "vendetta", "cassi", "issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi"];
const DRAFT = ["ryth", "vesper_vale", "vendetta", "cassi_and_issac", "stellar", "prism", "marcella", "willow", "ren", "varg", "tavi"];
const ITEMS = ["monster", "power", "durability", "treasure", "jungle", "home", "bruiser"].flatMap(family =>
    ["strength", "focus", "health"].flatMap(stat => [`${family}_shard_of_${stat}`, `${family}_emblem_of_${stat}`]));
const OUTCOME = { 0: "unfinished", 1: "teamA", 2: "teamB" };
const ENGINE_VERSION = 65536;

// ---------- inputs ----------

// Minimal ZIP reader (stored or deflated entries) so the tool has no dependencies.
function readZip(path) {
    const buf = readFileSync(path);
    let eocd = buf.length - 22;
    while (eocd >= 0 && buf.readUInt32LE(eocd) !== 0x06054b50) eocd--;
    if (eocd < 0) throw new Error("not a zip file");
    const count = buf.readUInt16LE(eocd + 10);
    let p = buf.readUInt32LE(eocd + 16);
    const files = {};
    for (let i = 0; i < count; i++) {
        const method = buf.readUInt16LE(p + 10), size = buf.readUInt32LE(p + 20);
        const nameLen = buf.readUInt16LE(p + 28), extra = buf.readUInt16LE(p + 30), comment = buf.readUInt16LE(p + 32);
        const local = buf.readUInt32LE(p + 42);
        const name = buf.toString("utf8", p + 46, p + 46 + nameLen);
        const data = local + 30 + buf.readUInt16LE(local + 26) + buf.readUInt16LE(local + 28);
        const raw = buf.subarray(data, data + size);
        files[name] = method === 0 ? raw : inflateRawSync(raw);
        p += 46 + nameLen + extra + comment;
    }
    return files;
}

function loadInput(path) {
    const ext = extname(path).toLowerCase();
    if (ext !== ".zip" && ext !== ".repl26a") throw new Error("expected .zip or .repl26a");
    const bytes = readFileSync(path);
    // Local bundles are zips despite the .repl26a extension.
    if (bytes.readUInt32LE(0) !== 0x04034b50) return { replay: bytes, stdout: {} };
    const files = readZip(path);
    if (!files["replay.repl26a"]) throw new Error("archive has no replay.repl26a");
    const stdout = {};
    for (const side of ["a", "b"])
        if (files[`team-${side}.stdout`]) stdout[side.toUpperCase()] = files[`team-${side}.stdout`].toString("utf8").replaceAll("\0", "");
    return { replay: files["replay.repl26a"], stdout };
}

function expandInputs(paths) {
    const result = [];
    for (const path of paths) {
        if (statSync(path).isDirectory()) {
            for (const name of readdirSync(path).sort())
                if (/\.(zip|repl26a)$/i.test(name)) result.push(join(path, name));
        } else result.push(path);
    }
    return result;
}

function findWasm() {
    // cambc caches assets in the platform cache dir: %LOCALAPPDATA% on Windows, ~/Library/Caches on macOS.
    const roots = [join(process.env.LOCALAPPDATA ?? "", "cambc", "assets"),
        join(homedir(), "Library", "Caches", "cambc", "assets"),
        join(process.env.XDG_CACHE_HOME ?? join(homedir(), ".cache"), "cambc", "assets")];
    const root = roots.find(existsSync);
    if (!root) throw new Error(`no cambc assets under ${roots.join(" or ")}; pass --wasm`);
    const candidates = [];
    for (const hash of readdirSync(root)) {
        const dir = join(root, hash, "visualiser", "assets");
        if (!existsSync(dir)) continue;
        for (const name of readdirSync(dir))
            if (/^v\d+_\d+_\d+-.*\.wasm$/.test(name)) candidates.push(join(dir, name));
    }
    if (!candidates.length) throw new Error("no engine wasm found; pass --wasm");
    return candidates.sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs)[0];
}

// ---------- engine ----------

class Engine {
    constructor(wasmPath) {
        const wasi = new WASI({ version: "preview1", args: [], env: {} });
        this.instance = new WebAssembly.Instance(new WebAssembly.Module(readFileSync(wasmPath)),
            { wasi_snapshot_preview1: wasi.wasiImport });
        wasi.initialize(this.instance);
        this.x = this.instance.exports;
        if (Number(this.x.Version()) !== ENGINE_VERSION)
            console.warn(`warning: engine version ${this.x.Version()} differs from the calibrated ${ENGINE_VERSION}; layouts may be wrong`);
        this.out = this.x.Engine_Malloc(64);
        this.args = this.x.Engine_Malloc(64);
        this.buf = this.x.Engine_Malloc(4096);
        this.snapshotPtr = this.x.Engine_Malloc(this.x.Game_Visualiser_SnapshotSize());
    }
    get mem() { return new DataView(this.x.memory.buffer); }
    check(code, what) {
        if (code === 0) return;
        const bytes = new Uint8Array(this.x.memory.buffer);
        const p = this.x.GetLastErrorMsg();
        let e = p;
        while (bytes[e]) e++;
        throw new Error(`${what} failed (${code}): ${new TextDecoder().decode(bytes.subarray(p, e))}`);
    }
    load(replay) {
        const p = this.x.Engine_Malloc(replay.length);
        new Uint8Array(this.x.memory.buffer, p, replay.length).set(replay);
        try { this.check(this.x.Game_FromReplayFileBytes(p, replay.length, this.out), "Game_FromReplayFileBytes"); }
        finally { this.x.Engine_Free(p); }
        return new Game(this, this.mem.getBigUint64(this.out, true));
    }
}

class Game {
    constructor(engine, handle) {
        this.e = engine; this.x = engine.x; this.handle = handle;
        engine.check(this.x.Game_Runner_SetCheckpointsEnabled(handle, 1), "SetCheckpointsEnabled");
        engine.check(this.x.Game_Visualiser_Timeline_GetMain(handle, engine.out), "Timeline_GetMain");
        this.timeline = engine.mem.getBigUint64(engine.out, true);
        engine.check(this.x.Game_Visualiser_Timeline_Info(handle, this.timeline, engine.args, engine.args + 8, engine.args + 16), "Timeline_Info");
        this.size = engine.mem.getUint32(engine.args, true);
    }
    destroy() { this.x.Game_Destroy(this.handle); }
    seek(position) { this.e.check(this.x.Game_Visualiser_Timeline_Seek(this.handle, this.timeline, position, 0), "Timeline_Seek"); }
    round() {
        this.e.check(this.x.Game_Runner_GetState(this.handle, this.e.args), "Runner_GetState");
        return this.e.mem.getUint32(this.e.args + 8, true);
    }

    // Final statistics: only available once the game has finished (error 18 before that).
    summary() {
        const { buf } = this.e;
        this.e.check(this.x.Game_Statistics_GetSummary(this.handle, buf), "Statistics_GetSummary");
        const m = this.e.mem;
        const picks = (count, at) => Array.from({ length: count }, (_, i) => m.getUint32(at + 4 * i, true));
        return {
            engineVersionPacked: m.getUint32(buf, true),
            outcome: OUTCOME[m.getUint32(buf + 4, true)] ?? `code${m.getUint32(buf + 4, true)}`,
            round: m.getUint32(buf + 8, true),
            championCount: m.getUint32(buf + 12, true),
            teams: [0, 1].map(t => ({
                team: t,
                submittedGems: Number(m.getBigUint64(buf + 16 + 8 * t, true)),
                draftPicks: picks(m.getUint32(buf + 32 + 4 * t, true), buf + 40 + 20 * t),
            })),
        };
    }
    champion(index) {
        const { buf } = this.e;
        this.e.check(this.x.Game_Statistics_GetChampion(this.handle, index, buf), "Statistics_GetChampion");
        const m = this.e.mem;
        const u32 = o => m.getUint32(buf + o, true), u64 = o => Number(m.getBigUint64(buf + o, true)), f64 = o => m.getFloat64(buf + o, true);
        return {
            champion: u32(0), team: u32(4), type: u32(8), kills: u32(12), deaths: u32(16), assists: u32(20),
            earnedGold: u64(24), collectedGems: u64(32), submittedGems: u64(40), spentGold: u64(48),
            gold: u32(56), gems: u32(60),
            itemsBought: Array.from({ length: 42 }, (_, i) => u64(64 + 8 * i)),
            consumablesBought: Array.from({ length: 4 }, (_, i) => u64(400 + 8 * i)),
            items: Array.from({ length: 42 }, (_, i) => u32(432 + 4 * i)),
            consumables: Array.from({ length: 4 }, (_, i) => u32(600 + 4 * i)),
            monsterDamageDone: f64(616), monsterDamageTaken: f64(624), championDamageDone: f64(632),
            championDamageTaken: f64(640), healingDone: f64(648), shieldingDone: f64(656),
        };
    }
    champions(count) { return Array.from({ length: count }, (_, i) => this.champion(i)); }

    // Spectator snapshot (Game_Visualiser_ReadState). Layout from the visualiser's decoder:
    // header; champion table count@120, data@140, stride 456; extension tables for earned gold
    // (@184248, 16 B per champion) and K/D/A (@184504, 12 B per champion).
    snapshot() {
        const { e } = this, b = e.snapshotPtr, view = e.args + 48;
        e.mem.setUint32(view, 2, true);             // team 2: spectator
        e.mem.setUint32(view + 4, 0xFFFFFFFF, true); // no champion
        e.check(this.x.Game_Visualiser_ReadState(this.handle, view, b), "ReadState");
        const m = e.mem;
        const u32 = o => m.getUint32(b + o, true), i32 = o => m.getInt32(b + o, true), f32 = o => m.getFloat32(b + o, true);
        if (u32(0) !== 1) throw new Error("unsupported snapshot ABI");
        const champions = [];
        for (let i = 0; i < u32(120); i++) {
            const c = 140 + i * 456, index = u32(c + 4);
            champions.push({
                champion: index, team: u32(c + 8), type: u32(c + 12),
                x: i32(c + 20), y: i32(c + 24), health: f32(c + 28), maxHealth: f32(c + 32),
                alive: u32(c + 224) !== 0, gold: u32(c + 232), gems: u32(c + 236),
                earnedGold: u32(184248 + index * 16) + u32(184252 + index * 16) * 2 ** 32,
                kills: u32(184504 + index * 12), deaths: u32(184508 + index * 12), assists: u32(184512 + index * 12),
            });
        }
        return { round: u32(8), submittedGems: [Number(m.getBigUint64(b + 32, true)), Number(m.getBigUint64(b + 40, true))], champions };
    }
}

// Walk the timeline once, taking a spectator snapshot at the first step of every round.
function timeline(game) {
    const rounds = [];
    let last = -1;
    for (let position = 0; position <= game.size; position++) {
        game.seek(position);
        const round = game.round();
        if (round === last) continue;
        last = round;
        const snap = game.snapshot();
        if (snap.champions.length) rounds.push(snap);
    }
    return rounds;
}

function timelineRows(rounds) {
    return rounds.flatMap(r => r.champions.map(c => ({
        round: r.round, submittedA: r.submittedGems[0], submittedB: r.submittedGems[1],
        champion: c.champion, team: c.team === 0 ? "A" : "B", type: CHAMPIONS[c.type], alive: +c.alive,
        x: c.x, y: c.y, health: Math.round(c.health), maxHealth: Math.round(c.maxHealth),
        gems: c.gems, gold: c.gold, earnedGold: c.earnedGold, kills: c.kills, deaths: c.deaths, assists: c.assists,
    })));
}

// ---------- analysis ----------

function detectUs(stdout, summary) {
    for (const [side, log] of Object.entries(stdout)) {
        const picks = [...log.matchAll(/draft: round \d+ picked (\w+)/g)].map(m => DRAFT.indexOf(m[1]));
        if (!picks.length) continue;
        const own = side === "A" ? 0 : 1;
        if (picks.every((p, i) => summary.teams[own].draftPicks[i] === p)) return side;
        if (picks.every((p, i) => summary.teams[1 - own].draftPicks[i] === p)) return side === "A" ? "B" : "A";
    }
    return undefined;
}

// Deaths, with the gems carried just before (handed to the killer, or destroyed by a camp) and
// whether an enemy champion stood within 4 tiles (a fight) or not (most likely a camp).
function deaths(rounds) {
    const events = [];
    for (let i = 1; i < rounds.length; i++) {
        const before = new Map(rounds[i - 1].champions.map(c => [c.champion, c]));
        for (const c of rounds[i].champions) {
            const prev = before.get(c.champion);
            if (!prev || !prev.alive || c.alive) continue;
            const enemyNear = rounds[i - 1].champions.some(o => o.team !== c.team && o.alive &&
                Math.max(Math.abs(o.x - prev.x), Math.abs(o.y - prev.y)) <= 4);
            events.push({ round: rounds[i].round, team: c.team, type: c.type, x: prev.x, y: prev.y, gemsLost: prev.gems, enemyNear });
        }
    }
    return events;
}

function gemsAt(rounds, round) {
    let best = [0, 0];
    for (const r of rounds) if (r.round <= round) best = r.submittedGems;
    return best;
}

function report(name, summary, champions, rounds, us) {
    const u = us === "B" ? 1 : 0, them = 1 - u;
    const lines = [];
    const result = summary.outcome === "unfinished" ? "unfinished" : summary.outcome === `team${us ?? "A"}` ? "WIN" : "LOSS";
    lines.push(`== ${name}: ${result} (we are team ${us ?? "A?"}) at round ${summary.round}, gems ${summary.teams[u].submittedGems}-${summary.teams[them].submittedGems}`);
    lines.push(`   draft  us: ${summary.teams[u].draftPicks.map(p => DRAFT[p]).join(", ")}  |  them: ${summary.teams[them].draftPicks.map(p => DRAFT[p]).join(", ")}`);
    const marks = [50, 100, 150, 200, 300, 400, 500, 750, 1000, 1500].filter(r => r < summary.round);
    lines.push("   gems submitted us-them: " + marks.map(r => { const g = gemsAt(rounds, r); return `r${r} ${g[u]}-${g[them]}`; }).join("  "));
    for (const t of [u, them]) {
        lines.push(`   ${t === u ? "us  " : "them"} champion      sub  coll   K/D/A  earned spent  mobDmg mobTaken  pvpDmg pvpTaken  build`);
        for (const c of champions.filter(c => c.team === t)) {
            const build = c.items.map((n, i) => n ? `${ITEMS[i].replace("_shard_of_", ":").replace("_emblem_of_", "*:")}x${n}` : "").filter(Boolean).join(" ");
            lines.push(`        ${CHAMPIONS[c.type].padEnd(12)} ${String(c.submittedGems).padStart(4)} ${String(c.collectedGems).padStart(5)} ${`${c.kills}/${c.deaths}/${c.assists}`.padStart(7)} ${String(c.earnedGold).padStart(7)} ${String(c.spentGold).padStart(5)} ${c.monsterDamageDone.toFixed(0).padStart(7)} ${c.monsterDamageTaken.toFixed(0).padStart(8)} ${c.championDamageDone.toFixed(0).padStart(7)} ${c.championDamageTaken.toFixed(0).padStart(8)}  ${build}`);
        }
    }
    const ds = deaths(rounds);
    for (const [label, t] of [["our", u], ["their", them]]) {
        const list = ds.filter(d => d.team === t), fights = list.filter(d => d.enemyNear);
        lines.push(`   ${label} deaths: ${list.length} (${fights.length} with an enemy near, ${list.length - fights.length} likely to camps), gems carried at death: ${list.reduce((s, d) => s + d.gemsLost, 0)}`);
        if (list.length) lines.push("     " + list.slice(0, 24).map(d => `r${d.round} ${CHAMPIONS[d.type]}@${d.x},${d.y}${d.gemsLost ? ` -${d.gemsLost}g` : ""}${d.enemyNear ? "" : " [camp?]"}`).join("  "));
    }
    return lines.join("\n");
}

// ---------- main ----------

const argv = process.argv.slice(2);
const opt = { us: undefined, wasm: undefined, out: undefined, inputs: [] };
for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--us") opt.us = argv[++i].toUpperCase();
    else if (argv[i] === "--wasm") opt.wasm = argv[++i];
    else if (argv[i] === "--out") opt.out = argv[++i];
    else opt.inputs.push(argv[i]);
}
if (!opt.inputs.length) {
    console.error("usage: node tools/replay/analyze.mjs [--us A|B] [--wasm path] [--out dir] <replay.zip|.repl26a|dir>...");
    process.exit(2);
}

const engine = new Engine(opt.wasm ?? findWasm());
for (const path of expandInputs(opt.inputs)) {
    const name = basename(path).replace(/\.(zip|repl26a)$/i, "");
    try {
        const input = loadInput(path);
        const game = engine.load(input.replay);
        const rounds = timeline(game);
        game.seek(game.size);
        const summary = game.summary();
        const champions = game.champions(summary.championCount);
        game.destroy();
        const us = opt.us ?? detectUs(input.stdout, summary);

        const outDir = opt.out ?? dirname(path);
        mkdirSync(outDir, { recursive: true });
        writeFileSync(join(outDir, `${name}.stats.json`), JSON.stringify({ ...summary, us, champions }, null, 2));
        const rows = timelineRows(rounds);
        const header = Object.keys(rows[0] ?? {});
        writeFileSync(join(outDir, `${name}.timeline.csv`), [header.join(","), ...rows.map(r => header.map(k => r[k]).join(","))].join("\n") + "\n");
        console.log(report(name, summary, champions, rounds, us));
    } catch (error) {
        console.log(`== ${name}: ERROR ${error.message}`);
    }
}
