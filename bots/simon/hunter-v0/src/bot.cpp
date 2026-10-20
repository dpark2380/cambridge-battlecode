// Strategy v4. Every champion, every turn:
//   dead -> shop | channelling or stunned -> wait | hurt -> step out of reach, recall
//   | enemy tributing beside us -> drop an altar lock | enemies -> fight only when ahead, else fall back
//   | carrying gems -> tribute (breaking enemy altar locks) | rich -> recall to shop | else own target.
// Every body farms on its own (v3 farmed in pairs and captured half as often as the +200 bot) and
// claims its target in shared memory so allies pick other groups; bodies share a group when it
// needs them or beats their other options. Shared memory also holds the last place we were the
// weaker side, which everybody avoids for a while.
#include <cambc.h>
#include "bot.h"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <span>
#include <variant>

using cambc::team;
using cambc::vec2;

namespace {

// Hunter line: daniel/v5 plus the habits of the +200 bot that beat it (replays/v5-daniel): engage
// at worse odds, chase gem carriers, and converge on prey a teammate spotted. The danger marker
// bits carry that prey position instead, so groups are never avoided.
constexpr float hunt_ratio = 0.8f;   // engage when allies' health nearby is this share of theirs
constexpr int hunt_radius = 8;       // chase gem carriers this far; others only within engage_radius
constexpr int prey_rounds = 10;      // a prey marker stays fresh this long
constexpr int prey_reach = 12;       // empty-handed bodies this close converge on it

// Shared memory is one little-endian 64-bit word of bit fields:
//   bits 0-35   a claim per body (6 bits each): target group index + 1, 0 = none
//   bits 36-42  danger x + 1 (0 = none), bits 43-49 danger y, bits 50-57 its round mod 256
// The largest map has 42 camp groups, so 6-bit claims fit; groups past index 62 go unclaimed.
constexpr int claim_bits = 6, max_bodies = 6;
constexpr int danger_x_bit = 36, danger_y_bit = 43, danger_round_bit = 50;
// Avoid camp groups within this many tiles of the danger marker for this many rounds. The marker
// is set where we found ourselves the weaker side.
constexpr int danger_radius = 2, danger_rounds = 20;

// Rough per-body figures for allies' kill-time and risk (measured: 35-50 damage/turn at the start,
// more once shards are bought); our own estimate is measured each turn (`measure_damage`).
constexpr float body_damage = 50, body_health = 900;
constexpr int capture_turns = 5;
// Skip monster groups whose expected damage exceeds this multiple of the bodies' health. Above 1 on
// purpose: hurt champions walk out of reach (camps do not chase or heal) and recall, so a costly
// fight costs trips home, not a death, and the target rate already charges for those trips. Lower
// values made casters (~45 damage/turn) wait for help on two wolves.
constexpr float max_damage_share = 4.0351f;
// Give up on a target after waiting this many turns for help, and ignore it for a while.
constexpr int max_wait_turns = 20, give_up_rounds = 60;
// Turns without getting closer to the target or hitting it before we give up on it.
constexpr int stall_turns = 14;
// Target rate = (gems + gold_weight * gold) per body per turn. Gems win; gold only buys power.
constexpr float gold_weight = 0.1035f;
// A trip home to heal is the recall plus the walk back out; a full health bar of damage taken
// costs one, charged pro rata so free clusters win over equal-value monsters.
constexpr float recall_turns = 11;
// Most bodies on one group: past three, a fourth adds little but splits the reward further.
constexpr int max_group_bodies = 2;
// Value kept by a body joining a group that does not need it (see choose_target).
constexpr float extra_body_value = 0.4538f;
// Extra turns charged to starting a group that needs help, for the wait until it arrives.
constexpr float help_wait_turns = 50;
// The duo carries the most gems and Cassi has 700 health: it leaves earlier when enemies are around.
constexpr float recall_health = 0.2880f, duo_recall_health = 0.7487f;
constexpr float spawn_leave_health = 0.7716f;
constexpr int tribute_gems = 25;      // always bank at least this many
constexpr int tribute_detour = 10;     // bank anything when an altar is this close
constexpr int engage_radius = 4;
// Extra path tiles we accept to reach a free altar instead of clearing a lock (~3 attack turns).
constexpr int lock_detour = 6;
constexpr int lock_place_range = 2;   // altar locks are placed within two tiles

int distance(vec2 a, vec2 b) { return static_cast<int>(a.chebyshev_distance(b)); }

cambc::bitboard tiles_around(vec2 position, int radius) {
    cambc::bitboard tiles;
    tiles.clear();
    tiles.draw_chebyshev(position, radius);
    return tiles;
}

cambc::bitboard terrain_blocked() {
    return cambc::map::walls() | cambc::map::holes() | cambc::map::altars() | cambc::map::spawn_region(team::enemy);
}

// Terrain plus visible occupants, excluding our own tile.
cambc::bitboard blocked_tiles() {
    auto blocked = terrain_blocked() | cambc::vision::champion_tiles() | cambc::vision::camp_tiles()
        | cambc::vision::teleport_tiles();
    blocked.set(cambc::self().position(), false);
    return blocked;
}

float ability_range(const cambc::ability& ability) {
    const auto& info = ability.info();
    if (!info)
        return 0;
    return std::visit([](const auto& payload) -> float {
        if constexpr (requires { payload.range; }) return payload.range;
        else return 0.f;
    }, *info);
}

bool excludes_walking(const cambc::ability& ability) {
    const auto& info = ability.info();
    return info && std::visit([](const auto& payload) { return payload.exclusive_with_movement; }, *info);
}

// Shard stat per champion_type: casters buy focus, Ryth health (it also adds strength), the rest strength.
enum class stat { strength, health, focus };
constexpr std::array<stat, 12> build_stat{
    stat::health,   stat::strength, stat::strength, stat::focus, stat::strength, stat::focus,
    stat::focus,    stat::strength, stat::focus,    stat::strength, stat::strength, stat::focus,
};

// Build order (the +200 elo bot's): one Monster emblem of our stat (10% more camp damage), one
// Durability emblem of health (10% less damage taken), then Power shards of our stat forever.
// Emblem passives do not stack, so a second emblem of a family only adds stats.
std::array<cambc::item_type, 3> build_order(stat s) {
    using cambc::item_type;
    switch (s) {
    case stat::strength:
        return {item_type::monster_shard_of_strength, item_type::durability_shard_of_health, item_type::power_shard_of_strength};
    case stat::health:
        return {item_type::monster_shard_of_health, item_type::durability_shard_of_health, item_type::power_shard_of_health};
    default:
        return {item_type::monster_shard_of_focus, item_type::durability_shard_of_health, item_type::power_shard_of_focus};
    }
}

// A champion we can see right now, with the fields we use read once. Ally occupancy can include
// allies outside our own vision, so look each tile up defensively and skip what we cannot see.
struct seen_champion {
    cambc::champion unit;
    vec2 position;
    float health, max_health;
};

std::vector<seen_champion> visible_champions(team side) {
    std::vector<seen_champion> result;
    for (const auto p : (cambc::vision::champion_tiles(side) & cambc::vision::visible_tiles()).positions()) {
        try {
            auto unit = cambc::vision::champion_at(p);
            if (unit.is_alive())
                result.push_back({unit, p, unit.health(), unit.max_health()});
        } catch (const cambc::error&) {
        }
    }
    return result;
}

// Our damage per turn against camps: a basic attack (strength) every turn plus each camp-targeting
// spell's damage spread over its cooldown. Casters like Cassi sit well below the per-body figure
// (~45 against clusters), so the real number keeps them off groups they cannot clear in time.
// Engine calls cost fuel, so this is measured once per turn.
float measure_damage() {
    auto& me = cambc::self();
    float damage = me.strength();
    for (const auto& ability : me.abilities()) {
        const auto& info = ability.info();
        if (!info || !(ability.is_damage() || ability.is_aoe_damage()) || !ability.can_target_camps())
            continue;
        try {
            const int cooldown = std::visit([](const auto& payload) { return payload.max_cooldown; }, *info);
            damage += ability.damage_amount() / static_cast<float>(std::max(1, cooldown));
        } catch (const cambc::error&) {
        }
    }
    return damage;
}

// Can we plus `helpers` average allies kill the group before its damage costs too much health?
bool survivable(const group_info& group, int helpers, const self_estimate& own) {
    const float damage = own.damage + body_damage * helpers;
    const float health = own.health + body_health * helpers;
    return group.exposure / damage <= max_damage_share * health;
}

// Monsters do not chase and hit at range 3: is anything that hurts within reach of `p`?
bool threatened(const world& camps, vec2 p) {
    for (const auto tile : (cambc::vision::camp_tiles() & tiles_around(p, 3)).positions())
        if (const auto* camp = camps.camp_at(tile); camp && !camp->is_gem_cluster() && !camp->is_gold_cluster())
            return true;
    return !(cambc::vision::champion_tiles(team::enemy) & tiles_around(p, 4)).is_empty();
}

// Shared memory as one word: a single engine call each way (~150 fuel per call).
std::uint64_t read_memory() {
    std::array<std::byte, 8> bytes{};
    cambc::shared_memory.read(0, bytes);
    std::uint64_t word = 0;
    for (int i = 0; i < 8; ++i)
        word |= static_cast<std::uint64_t>(bytes[i]) << (8 * i);
    return word;
}

void write_memory(std::uint64_t word) {
    std::array<std::byte, 8> bytes{};
    for (int i = 0; i < 8; ++i)
        bytes[i] = static_cast<std::byte>(word >> (8 * i));
    cambc::shared_memory.write(0, std::span<const std::byte>(bytes));
}

int get_bits(std::uint64_t word, int offset, int count) {
    return static_cast<int>((word >> offset) & ((std::uint64_t{1} << count) - 1));
}

std::uint64_t set_bits(std::uint64_t word, int offset, int count, int value) {
    const auto mask = ((std::uint64_t{1} << count) - 1) << offset;
    return (word & ~mask) | ((static_cast<std::uint64_t>(value) << offset) & mask);
}

// Group index claimed by body `slot`, or -1.
int claim_of(std::uint64_t word, int slot) { return get_bits(word, slot * claim_bits, claim_bits) - 1; }

void mark_danger(vec2 p, int round) {
    auto word = read_memory();
    word = set_bits(word, danger_x_bit, 7, p.x + 1);
    word = set_bits(word, danger_y_bit, 7, p.y);
    word = set_bits(word, danger_round_bit, 8, round & 0xFF);
    write_memory(word);
}

// Was a group of enemies seen near `p` recently? Rounds are stored mod 256, so compare that way.
bool near_danger(std::uint64_t, vec2, int) { return false; }

// Fresh prey marker position, or none.
std::optional<vec2> prey_marker(std::uint64_t word, int round) {
    const int x = get_bits(word, danger_x_bit, 7);
    if (x == 0)
        return std::nullopt;
    const int age = (round - get_bits(word, danger_round_bit, 8)) & 0xFF;
    if (age > prey_rounds)
        return std::nullopt;
    return vec2{x - 1, get_bits(word, danger_y_bit, 7)};
}

[[maybe_unused]] bool old_near_danger(std::uint64_t word, vec2 p, int round) {
    const int x = get_bits(word, danger_x_bit, 7);
    if (x == 0)
        return false;
    const int age = (round - get_bits(word, danger_round_bit, 8)) & 0xFF;
    return age <= danger_rounds && distance(p, vec2{x - 1, get_bits(word, danger_y_bit, 7)}) <= danger_radius;
}

} // namespace

void Bot::init() {
    initialised = true;
    plan = read_plan();
    const auto type = cambc::self().champion_name();
    const int mine = static_cast<int>(type);
    if (plan) {
        squad = plan->role_of(type) == role::gem_duo ? role::gem_duo : role::gold_squad;
        // Our claim slot: rank of our champion_type among the team's (Cassi and Issac are two).
        slot = team_bodies = 0;
        for (int t = 0; t < static_cast<int>(std::size(plan->roles)); ++t)
            if (plan->roles[t] != role::none) {
                ++team_bodies;
                slot += t < mine;
            }
    } else {
        slot = mine % max_bodies;
    }
    slot = std::min(slot, max_bodies - 1);
    camps.init();

    // Static trip lengths per group for the target rate. Unreachable counts as far, not free.
    const auto blocked = terrain_blocked();
    cambc::bitboard altar_tiles;
    altar_tiles.clear();
    for (const auto altar : cambc::map::altars().positions())
        altar_tiles |= tiles_around(altar, cambc::constants::submit_gems_range);
    auto distances_from = [&](cambc::bitboard sources, int group_info::*field, cambc::distance_field& distances) {
        cambc::bitboard visited;
        distances.compute(blocked & ~sources, sources & ~blocked, visited);
        for (auto& g : camps.groups()) {
            const int d = distances.get(g.anchor);
            g.*field = d == cambc::distance_field::unreachable ? 100 : d;
        }
    };
    cambc::distance_field home_walk;
    distances_from(cambc::map::spawn_region(team::ally), &group_info::home_distance, home_walk);
    distances_from(altar_tiles, &group_info::altar_distance, altar_walk);
    std::cout << "plan: " << cambc::to_string(type) << (squad == role::gem_duo ? " gem_duo" : " gold_squad")
              << " slot=" << slot << " bodies=" << team_bodies << (plan ? "" : " (no plan)") << '\n';
}

void Bot::shop() {
    auto& me = cambc::self();
    // An altar lock first: 10 gold to cancel an enemy tribute (only sold on spawn or while dead).
    const auto lock = cambc::consumable_type::altar_lock;
    if (me.consumables()[lock].count() == 0 && me.can_buy(lock))
        me.buy(lock);

    // Finish each emblem before starting the next; Power (last) soaks up the rest.
    const auto order = build_order(build_stat[static_cast<int>(me.champion_name())]);
    for (std::size_t i = 0; i < order.size(); ++i) {
        const auto shard = order[i];
        const auto owned = me.item_count();
        const bool last = i + 1 == order.size();
        const auto emblem = shard.result();
        if (!last && emblem && owned[*emblem] > 0)
            continue;
        unsigned count = me.gold_count() / shard.cost();
        if (!last)
            count = std::min<unsigned>(count, shard.combine_count() - owned[shard]);
        if (count == 0 || !me.can_buy(shard, count))
            return;
        me.buy(shard, count);
    }
}

// Drop our altar lock on an altar beside us where an enemy stands: placing it cancels their tribute.
bool Bot::place_lock() {
    auto& me = cambc::self();
    const auto& lock = me.consumables()[cambc::consumable_type::altar_lock];
    if (lock.count() == 0)
        return false;
    const auto pos = me.position();
    const auto enemies = cambc::vision::champion_tiles(team::enemy);
    for (const auto altar : cambc::map::altars().positions()) {
        if (distance(pos, altar) > lock_place_range || cambc::vision::has_altar_lock(altar)
            || (enemies & tiles_around(altar, cambc::constants::submit_gems_range)).is_empty())
            continue;
        try {
            if (lock.use(altar))
                return true;
        } catch (const cambc::error& error) {
            std::cout << "lock failed: " << error.what() << '\n';
        }
    }
    return false;
}

bool Bot::move_towards_closest(cambc::bitboard goals) {
    auto& me = cambc::self();
    const auto origin = me.position();
    if (!me.can_move() || goals.is_set(origin))
        return false;

    // Only free goals or occupied camp tiles can seed the field.
    const auto blocked = blocked_tiles();
    goals &= ~blocked | cambc::vision::camp_tiles();
    if (goals.is_empty())
        return false;

    const auto path_walls = blocked & ~goals;
    cambc::distance_field field;
    cambc::bitboard visited;
    field.compute_to(path_walls, goals, tiles_around(origin, 0), visited);

    auto step = origin;
    for (auto tile : blocked.reachable_tiles(origin, me.base_stats().base_move_speed).positions())
        if (field.get(tile) < field.get(step)) step = tile;
    try {
        if (step == origin || !me.move_absolute(step))
            return false;
    } catch (const cambc::error&) {
        return false;  // tile became known-occupied since our snapshot
    }
    moved = true;

    // Dash further along the same field when one is ready (dashes allow walking).
    if (field.get(step) > 2 && me.can_cast())
        for (const auto& ability : me.abilities())
            if (ability.is_dash() && ability.is_ready()) {
                auto landing = step;
                for (auto tile : (ability.valid_tiles() & ~blocked_tiles()).positions())
                    if (field.get(tile) < field.get(landing)) landing = tile;
                try {
                    if (landing != step) ability.use(landing);
                } catch (const cambc::error&) {
                    // Illegal dash path (walls in between): keep the walk.
                }
                break;
            }
    return true;
}

// Position of a target that is still alive and in vision. Targets die or leave vision mid-turn
// (our own hit kills them, our move loses sight), and querying them then throws.
template <class Target>
std::optional<vec2> live_position(const Target& target) {
    try {
        if (target.is_visible() && target.health() > 0)
            return target.position();
    } catch (const cambc::error&) {
    }
    return std::nullopt;
}

// Basic attack if in range, then offensive casts. Returns whether we attacked or cast.
template <class Target>
bool Bot::strike(const Target& target) {
    auto& me = cambc::self();
    const auto position = live_position(target);
    if (!position)
        return false;
    bool acted = false;
    if (me.can_attack() && distance(me.position(), *position) <= me.attack_range()) {
        me.attack(target);
        acted = true;
    }
    const bool could_cast = me.can_cast();
    cast_offense(target);
    return acted || (could_cast && !me.can_cast());
}

template <class Target>
void Bot::cast_offense(const Target& target) {
    auto& me = cambc::self();
    constexpr bool at_champion = std::is_same_v<Target, cambc::champion>;
    for (const auto& ability : me.abilities()) {
        if (!me.can_cast())
            return;
        const auto position = live_position(target);
        if (!position)
            return;
        if (!ability.info() || !ability.is_ready() || (moved && excludes_walking(ability)))
            continue;
        const int d = distance(me.position(), *position);
        try {
            if (ability.is_attack_reset()) {
                // Restores the attack allowance: also lets ranged champions walk and still attack.
                if (!me.can_attack() && d <= me.attack_range() && ability.use() && me.can_attack())
                    me.attack(target);
            } else if (ability.is_damage() || ability.is_cc()) {
                const bool allowed = at_champion ? ability.can_target_enemies() : ability.can_target_camps();
                if (allowed && d <= ability_range(ability))
                    ability.use(target);
            } else if (ability.is_aoe_damage()) {
                if (d <= ability_range(ability))
                    ability.use(*position);
            }
        } catch (const cambc::error& error) {
            std::cout << "cast failed: " << error.what() << '\n';
        }
    }
}

// Heal the most hurt visible ally; shield ourselves when hurt and under threat.
void Bot::cast_support() {
    auto& me = cambc::self();
    if (!me.can_cast())
        return;
    for (const auto& ability : me.abilities()) {
        if (!ability.info() || !ability.is_ready())
            continue;
        try {
            if (ability.is_heal()) {
                const seen_champion* best = nullptr;
                const auto allies = visible_champions(team::ally);
                float worst = 0.7f;
                for (const auto& ally : allies) {
                    if (ally.unit == me || distance(me.position(), ally.position) > ability_range(ability))
                        continue;
                    if (const float ratio = ally.health / ally.max_health; ratio < worst) {
                        worst = ratio;
                        best = &ally;
                    }
                }
                if (best) { ability.use(best->unit); return; }
            } else if (ability.is_shield() && me.health() < 0.85f * me.max_health()) {
                ability.use();
                return;
            }
        } catch (const cambc::error& error) {
            std::cout << "support cast failed: " << error.what() << '\n';
        }
    }
}

void Bot::retreat() {
    move_towards_closest(cambc::map::spawn_region(team::ally));
}

// Weigh the fight by total visible health within reach, ours against theirs: head counts froze a
// v3-vs-v2 game in a 4-vs-5 standoff we would have won on health. Fight at parity or better (or to
// finish a nearly dead enemy); otherwise mark the spot as dangerous, fall back, and take whatever
// shot is still legal. The duo chases; the gold squad only hits what is in range.
// Hunter: fight at `hunt_ratio` odds or better within `hunt_radius`, richest carrier first (then the
// weakest), chase it, and mark it as prey for the team. Outmatched: fall back without marking.
bool Bot::fight_enemies(int round) {
    auto& me = cambc::self();
    const auto pos = me.position();
    const seen_champion* prey = nullptr;
    float enemy_health = 0, ally_health = 0, prey_key = 0;
    const auto enemies = visible_champions(team::enemy);
    for (const auto& enemy : enemies) {
        float gems = 0;
        try {
            gems = static_cast<float>(enemy.unit.gem_count());
        } catch (const cambc::error&) {
        }
        if (distance(pos, enemy.position) > (gems > 0 ? hunt_radius : engage_radius))
            continue;
        enemy_health += enemy.health;
        const float key = gems * 10000 + (enemy.max_health - enemy.health) + 1;
        if (!prey || key > prey_key) {
            prey = &enemy;
            prey_key = key;
        }
    }
    if (!prey)
        return false;
    for (const auto& ally : visible_champions(team::ally))
        if (distance(pos, ally.position) <= hunt_radius)
            ally_health += ally.health;

    const auto& target = prey->unit;
    if (ally_health < hunt_ratio * enemy_health) {
        retreat();
        strike(target);
        return true;
    }
    if (prey_key >= 10000)  // carrying gems
        mark_danger(prey->position, round);
    if (strike(target))
        return true;
    if (move_towards_closest(tiles_around(prey->position, static_cast<int>(me.attack_range()))))
        strike(target);
    return true;
}

bool Bot::should_tribute(int round) {
    auto& me = cambc::self();
    const int gems = static_cast<int>(me.gem_count());
    if (gems == 0)
        return false;
    // Once heading to an altar, keep going: on interlock a Chebyshev check flipped every turn
    // between "altar close" and "back to the camp" where walls make the walk long.
    if (banking || gems >= tribute_gems)
        return banking = true;
    // Walking distance: a nearby altar behind a wall is not a short detour.
    if (static_cast<int>(altar_walk.get(me.position())) <= tribute_detour)
        return banking = true;
    // Nothing worth capturing right now: bank what we hold.
    return banking = choose_target(round) < 0;
}

// Tribute at the nearest free altar, or break an enemy lock (three basic attacks; ranged champions
// hit it from range) when a free altar is more than `lock_detour` tiles further. Skipping locked
// altars outright stalled v2 for 300 rounds once every altar was locked.
void Bot::go_tribute() {
    auto& me = cambc::self();
    const auto pos = me.position();
    const int submit_range = cambc::constants::submit_gems_range;
    const int hit_range = me.attack_range();
    const auto enemy_locks = cambc::vision::altar_lock_tiles(team::enemy);

    const auto altars = cambc::map::altars().positions();
    for (const auto altar : altars)
        if (!enemy_locks.is_set(altar) && distance(pos, altar) <= submit_range) {
            me.submit_gems(altar);
            return;
        }
    cambc::bitboard free_goals, locked_goals;
    free_goals.clear();
    locked_goals.clear();
    for (const auto altar : altars) {
        const bool locked = enemy_locks.is_set(altar);
        if (locked && distance(pos, altar) <= hit_range && me.can_attack()) {
            try {
                me.attack(cambc::vision::altar_lock_at(altar));
            } catch (const cambc::error& error) {
                std::cout << "lock attack failed: " << error.what() << '\n';
            }
            return;
        }
        (locked ? locked_goals : free_goals) |= tiles_around(altar, locked ? hit_range : submit_range);
    }

    // Both kinds available: compare walking distances to each set.
    auto walk = [&](const cambc::bitboard& goals) {
        if (goals.is_empty())
            return static_cast<int>(cambc::distance_field::unreachable);
        const auto blocked = terrain_blocked();
        cambc::distance_field field;
        cambc::bitboard visited;
        field.compute_to(blocked, goals & ~blocked, tiles_around(pos, 0), visited);
        return static_cast<int>(field.get(pos));
    };
    const bool use_free = locked_goals.is_empty()
        || (!free_goals.is_empty() && walk(free_goals) <= walk(locked_goals) + lock_detour);
    move_towards_closest(use_free ? free_goals : locked_goals);
}

// Gold only helps once spent: head home to shop when carrying an emblem's worth (Tavi shops anywhere).
bool Bot::shop_trip() {
    auto& me = cambc::self();
    const unsigned threshold = squad == role::gold_squad ? 150 : 300;
    if (me.champion_name() == cambc::champion_type::tavi || me.gold_count() < threshold || me.gem_count() > 0)
        return false;
    if (auto* target = camps.group(current_target))
        if (target->reward_ready && target->tiles.is_set(me.position()))
            return false;  // mid-capture
    me.recall();
    return true;
}

// Best gems-and-gold per turn for this body. A group is started with the fewest bodies that survive
// it, and stays open to joiners up to `max_group_bodies`; every body splits its value. Computed
// once per turn.
int Bot::choose_target(int round) {
    if (target_round == round)
        return current_target;
    target_round = round;
    const auto word = read_memory();
    auto& groups = camps.groups();
    const int count = std::min<int>(static_cast<int>(groups.size()), (1 << claim_bits) - 1);
    const int max_helpers = std::max(0, std::min(team_bodies, max_group_bodies) - 1);

    // Bodies needed for group i (0 = too much even with help) and allies already claiming it.
    auto needed = [&](const group_info& g) {
        for (int helpers = 0; helpers <= max_helpers; ++helpers)
            if (survivable(g, helpers, own)) return helpers + 1;
        return 0;
    };
    auto claimants = [&](int index) {
        int n = 0;
        for (int s = 0; s < max_bodies; ++s)
            n += s != slot && claim_of(word, s) == index;
        return n;
    };

    // Keep the current target while it is up soon and not taken over.
    if (auto* current = camps.group(current_target); current && current_target < count)
        if (needed(*current) > 0 && claimants(current_target) < max_group_bodies
            && current->respawn_round - round <= 10 && current->skip_until <= round
            && !near_danger(word, current->anchor, round))
            return current_target;

    const auto origin = cambc::self().position();
    cambc::distance_field field;
    cambc::bitboard visited;
    field.compute(terrain_blocked(), tiles_around(origin, 0), visited);

    int best = -1;
    float best_rate = 0;
    for (int i = 0; i < count; ++i) {
        const auto& g = groups[i];
        if (g.monolith || g.skip_until > round || near_danger(word, g.anchor, round))
            continue;
        // Join a claimed group as one more body (its value split further), or start one with the
        // fewest bodies that survive it. Joining wins when groups are scarce (rows: three groups
        // per side for five bodies) and halves the damage a lone melee body would tank.
        const int need = needed(g);
        const int others = claimants(i);
        const int bodies = std::max(need, others + 1);
        if (need == 0 || bodies > max_group_bodies)
            continue;
        const int travel = field.get(g.anchor);
        if (travel == cambc::distance_field::unreachable)
            continue;
        const float damage = own.damage + body_damage * (bodies - 1);
        const float taken = g.exposure / damage / bodies;  // our share of the damage
        // One cycle: get there (or wait out the respawn), kill, capture, carry our share of the gems
        // to an altar and channel them in; damage taken costs that share of a trip home and back.
        const float gems = static_cast<float>(g.gems) / bodies;
        float time = std::max<float>(travel, g.respawn_round - round) + g.health / damage + capture_turns
            + (gems > 0 ? g.altar_distance + std::ceil(gems / 10) : 0)
            + taken / own.health * (2 * g.home_distance + recall_turns);
        if (bodies > 1 && others + 1 < bodies)
            time += help_wait_turns;
        // A body past what the group needs only speeds it up: its share comes out of the
        // claimants' shares, so value it at a discount.
        float value = (g.gems + gold_weight * g.gold) / bodies;
        if (bodies > need)
            value *= extra_body_value;
        if (value > 0 && value / time > best_rate) {
            best_rate = value / time;
            best = i;
        }
    }
    current_target = best;
    return best;
}

// Publish this turn's claim (or none) when it changed.
void Bot::publish_claim(int round) {
    if (published_claim == claim && published_round + 50 > round)
        return;  // refresh now and then in case a write was lost to running out of fuel
    const auto word = read_memory();
    write_memory(set_bits(word, slot * claim_bits, claim_bits, claim + 1));
    published_claim = claim;
    published_round = round;
}

void Bot::work_group(int index, int round) {
    auto& group = camps.groups()[index];
    auto& me = cambc::self();
    const auto pos = me.position();

    // Fight the group's living members: monsters before clusters, nearest first.
    std::optional<cambc::camp> target;
    int target_key = 1 << 30;
    const auto live = group.tiles & cambc::vision::camp_tiles() & cambc::vision::visible_tiles();
    for (const auto p : live.positions()) {
        const auto* camp = camps.camp_at(p);
        if (!camp)
            continue;
        const bool cluster = camp->is_gem_cluster() || camp->is_gold_cluster();
        const int key = (cluster ? 1000 : 0) + distance(pos, p);
        if (key < target_key) { target_key = key; target = *camp; }
    }
    if (target && !target->is_gem_cluster() && !target->is_gold_cluster()) {
        int helpers = 0;
        for (const auto& ally : visible_champions(team::ally))
            helpers += !(ally.unit == me) && distance(ally.position, group.anchor) <= 6;
        if (!survivable(group, helpers, own)) {
            // Wait for help at a safe distance (camps hit at range 3 and do not chase); give up if
            // nobody comes.
            waited = waiting_for == index ? waited + 1 : 1;
            waiting_for = index;
            if (waited > max_wait_turns) {
                group.skip_until = round + give_up_rounds;
                current_target = claim = -1;
            }
            if (threatened(camps, pos)) retreat();
            else if (distance(pos, group.anchor) > 5) move_towards_closest(group.tiles);
            return;
        }
    }
    if (target) {
        if (strike(*target)) {
            hit_target = true;
            return;
        }
        cambc::bitboard goals;
        goals.clear();
        goals.set(target->spawn_position());
        if (move_towards_closest(goals))
            hit_target = strike(*target);
        return;
    }

    // Everything dead and the reward waiting: stand on a spawn tile until the capture completes.
    if (group.reward_ready) {
        if (!group.tiles.is_set(pos))
            move_towards_closest(group.tiles);
        return;
    }

    // Respawning: an occupied spawn tile delays the whole group, so wait beside the tiles, never on
    // them. Otherwise (unseen, or alive members out of sight) walk up beside them.
    cambc::bitboard beside;
    beside.clear();
    for (const auto tile : group.tiles.positions())
        beside |= tiles_around(tile, 1);
    beside &= ~group.tiles;
    const bool waiting = group.known_respawning(round) && group.seen_round == round;
    if (group.tiles.is_set(pos) || !waiting)
        move_towards_closest(beside);
}

void Bot::play_turn() {
    if (!initialised)
        init();
    const int round = static_cast<int>(cambc::round_number());
    camps.observe(round);
    moved = false;
    if (cambc::self().is_alive())
        own = {measure_damage(), cambc::self().max_health()};
    claim = -1;  // held only while working the target (or fighting near it)
    take_turn(round);
    publish_claim(round);
}

void Bot::take_turn(int round) {
    auto& me = cambc::self();
    if (!me.is_alive()) {
        shop();
        return;
    }
    // Leave channels running.
    if (me.is_recalling() || me.is_submitting_gems() || me.is_teleporting())
        return;

    if (me.gem_count() == 0)
        banking = false;
    const bool at_spawn = cambc::map::spawn_region(team::ally).is_set(me.position());
    if (me.gold_count() >= 10 && (at_spawn || me.champion_name() == cambc::champion_type::tavi))
        shop();
    // Stunned: any action would throw "champion cannot act".
    if (!me.can_move() && !me.can_attack() && !me.can_cast())
        return;

    // The duo leaves early only under champion threat: against camps that just slowed it down.
    const bool enemy_seen = !(cambc::vision::champion_tiles(team::enemy) & cambc::vision::visible_tiles()).is_empty();
    const float leave_at = squad == role::gem_duo && enemy_seen ? duo_recall_health : recall_health;
    if (!at_spawn && me.health() < leave_at * me.max_health()) {
        // Damage cancels a recall: step out of reach first.
        if (threatened(camps, me.position())) retreat();
        else me.recall();
        return;
    }
    // Spawn heals every round: top up before heading back out.
    if (at_spawn && me.health() < spawn_leave_health * me.max_health())
        return;

    cast_support();
    place_lock();
    if (fight_enemies(round)) {
        claim = current_target;
        watch_progress(round);
        return;
    }
    if (should_tribute(round)) {
        go_tribute();
        return;
    }
    // Converge on a teammate's prey while empty-handed.
    if (const auto prey = prey_marker(read_memory(), round);
        prey && distance(me.position(), *prey) <= prey_reach && distance(me.position(), *prey) > 2) {
        move_towards_closest(tiles_around(*prey, 1));
        return;
    }
    if (shop_trip())
        return;

    const int target = choose_target(round);
    if (round % 100 == 0) {
        const auto p = me.position();
        std::cout << "status r" << round << ' ' << cambc::to_string(me.champion_name()) << " at " << p.x << ',' << p.y
                  << " gems=" << me.gem_count() << " gold=" << me.gold_count() << " hp=" << int(me.health()) << " dmg=" << int(own.damage)
                  << " target=" << target << " claims=";
        const auto word = read_memory();
        for (int s = 0; s < max_bodies; ++s)
            std::cout << claim_of(word, s) << (s + 1 < max_bodies ? "," : "");
        if (const auto* g = camps.group(target))
            std::cout << " (" << g->anchor.x << ',' << g->anchor.y << " ready=" << g->reward_ready
                      << " respawn=" << g->respawn_round << " waited=" << (waiting_for == target ? waited : 0) << ')';
        std::cout << '\n';
    }
    if (target >= 0) {
        claim = target;
        work_group(target, round);
        watch_progress(round);
    }
}

// Give up on a target we stop making progress on: neither closer to it nor hitting it for
// `stall_turns` turns spent working or fighting near it. On interlock a body walked towards its
// target, met an idle enemy, fell back, and repeated that for 200 rounds.
void Bot::watch_progress(int round) {
    auto* group = camps.group(current_target);
    if (!group) {
        progress_target = -1;
        return;
    }
    const auto pos = cambc::self().position();
    const int d = distance(pos, group->anchor);
    // Restart after any break (tribute, recall, shopping): the walk back starts from scratch.
    const bool continued = current_target == progress_target && round == progress_round + 1;
    progress_round = round;
    if (!continued) {
        progress_target = current_target;
        best_distance = d;
        stalled = 0;
    } else if (hit_target || d < best_distance || group->known_respawning(round)
               || (group->reward_ready && group->tiles.is_set(pos))) {
        best_distance = std::min(best_distance, d);
        stalled = 0;
    } else if (++stalled > stall_turns) {
        std::cout << "stalled r" << round << " on group " << current_target << " at " << pos.x << ',' << pos.y << '\n';
        group->skip_until = round + give_up_rounds;
        current_target = claim = progress_target = -1;
    }
    hit_target = false;
}
