// Strategy v3. Every champion, every turn:
//   dead -> shop | channelling or stunned -> wait | hurt -> step out of reach, recall
//   | enemy tributing beside us -> drop an altar lock | enemies -> fight only when ahead, else fall back
//   | carrying gems -> tribute (breaking enemy altar locks) | rich -> recall to shop | else squad target.
// Shared memory: squad targets (bytes 0-1) and the last place several enemies were seen (bytes 2-4),
// which both squads avoid for a while.
#include <cambc.h>
#include "bot.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <variant>

using cambc::team;
using cambc::vec2;

namespace {

// Shared memory: one byte per squad holding target group index + 1 (0 = none), then the danger
// marker: x + 1 (0 = none), y, and the round it was seen (mod 256).
constexpr std::size_t gem_target_slot = 0, gold_target_slot = 1;
// v5 solo farming: each gold-squad member claims its own group. Member k uses gold_member_slots[k];
// the first is the old shared gold slot, the rest are bytes 5-7 (free in v3).
constexpr std::array<std::size_t, 4> gold_member_slots{gold_target_slot, 5, 6, 7};
// 1 = gold-squad members farm separately where one body survives the group, joining others only when
// that pays better; 0 = v3 behaviour (the whole squad shares one target). Capture rewards are split
// among the allies present, so a pack only kills faster; it does not earn more.
constexpr int solo_farm = 1;
// Solo groups are judged on our own stats, not body_damage/body_health. Camps do not chase, so a
// costly group means a retreat and recall, not a death: allow this multiple of our max health.
constexpr float solo_damage_share = 2.0f;
constexpr std::size_t danger_x_slot = 2, danger_y_slot = 3, danger_round_slot = 4;
// Avoid camp groups within this many tiles of the danger marker for this many rounds. The marker
// is set where we found ourselves the weaker side.
constexpr int danger_radius = 9, danger_rounds = 24;

// Rough per-body figures for kill-time and risk estimates (GameRules.md: ~50-90 damage/turn).
constexpr float body_damage = 70, body_health = 900;
constexpr int capture_turns = 5;
// Skip monster groups whose expected damage exceeds this multiple of the bodies' health. Above 1 on
// purpose: hurt champions walk out of reach (camps do not chase) and recall, so a costly fight
// costs time, not a death. This only rules out hopeless fights like a lone ranged champion on an elk.
constexpr float max_damage_share = 1.4169f;
// Give up on a target after waiting this many turns for squad-mates, and ignore it for a while.
constexpr int max_wait_turns = 21, give_up_rounds = 74;
// Gold clusters ("mining") are valued at this fraction of monster gold: monsters come first.
constexpr float mining_weight = 0.4053f;
// Gold squad: one gold is worth this many gems when choosing a target.
constexpr float squad_gold_weight = 0.25f;
// The duo carries the most gems and Cassi has 700 health: it leaves earlier when enemies are around.
constexpr float recall_health = 0.3000f, duo_recall_health = 0.6726f;
constexpr float spawn_leave_health = 0.9570f;
constexpr int tribute_gems = 36;      // always bank at least this many
constexpr int tribute_detour = 9;     // bank anything when an altar is this close
constexpr int engage_radius = 4;
// Extra path tiles we accept to reach a free altar instead of clearing a lock (~3 attack turns).
constexpr int lock_detour = 4;
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

// Can `bodies` champions kill the group before its damage costs too much of their health?
bool survivable(const group_info& group, int bodies) {
    return group.exposure / (body_damage * bodies) <= max_damage_share * body_health * bodies;
}

// Our damage per turn against camps: basic attacks (plus resets) and damage spells over their cooldown.
float my_camp_damage() {
    auto& me = cambc::self();
    float damage = me.strength();
    for (const auto& ability : me.abilities()) {
        if (ability.is_attack_reset()) damage += me.strength() / 8.f;
        else if (ability.is_damage() || ability.is_aoe_damage() || ability.is_cc()) damage += ability.damage_amount() / 8.f;
    }
    if (me.passive() == cambc::passive_type::splash_attack) damage *= 1.5f;  // packed camps take splash
    return damage * me.base_stats().camp_damage_multiplier;
}

// Solo/join check on our own stats plus generic bodies for any helpers (see solo_damage_share).
bool solo_survivable(const group_info& group, int bodies) {
    const float damage = my_camp_damage() + body_damage * (bodies - 1);
    return group.exposure / damage <= solo_damage_share * (cambc::self().max_health() + body_health * (bodies - 1));
}

// Monsters do not chase and hit at range 3: is anything that hurts within reach of `p`?
bool threatened(const world& camps, vec2 p) {
    for (const auto tile : (cambc::vision::camp_tiles() & tiles_around(p, 3)).positions())
        if (const auto* camp = camps.camp_at(tile); camp && !camp->is_gem_cluster() && !camp->is_gold_cluster())
            return true;
    return !(cambc::vision::champion_tiles(team::enemy) & tiles_around(p, 4)).is_empty();
}

std::uint8_t read_slot(std::size_t slot) { return cambc::shared_memory[slot]; }
void write_slot(std::size_t slot, std::uint8_t value) { cambc::shared_memory[slot] = value; }

void mark_danger(vec2 p, int round) {
    write_slot(danger_x_slot, static_cast<std::uint8_t>(p.x + 1));
    write_slot(danger_y_slot, static_cast<std::uint8_t>(p.y));
    write_slot(danger_round_slot, static_cast<std::uint8_t>(round));
}

// Was a group of enemies seen near `p` recently? Rounds are stored mod 256, so compare that way.
bool near_danger(vec2 p, int round) {
    const int x = read_slot(danger_x_slot);
    if (x == 0)
        return false;
    const int age = static_cast<std::uint8_t>(round - read_slot(danger_round_slot));
    return age <= danger_rounds && distance(p, vec2{x - 1, static_cast<int>(read_slot(danger_y_slot))}) <= danger_radius;
}

} // namespace

void Bot::init() {
    initialised = true;
    plan = read_plan();
    const auto type = cambc::self().champion_name();
    if (plan) {
        squad = plan->role_of(type) == role::gem_duo ? role::gem_duo : role::gold_squad;
        squad_bodies = static_cast<int>(std::count(std::begin(plan->roles), std::end(plan->roles), squad));
        // Our index among gold-squad members, in champion_type order (every member computes the same).
        const int me_type = static_cast<int>(type);
        int k = 0;
        for (int t = 0; t < me_type; ++t) k += plan->roles[t] == role::gold_squad;
        member = std::min(k, static_cast<int>(gold_member_slots.size()) - 1);
    }
    camps.init();
    std::cout << "plan: " << cambc::to_string(type) << (squad == role::gem_duo ? " gem_duo" : " gold_squad")
              << " bodies=" << squad_bodies << (plan ? "" : " (no plan)") << '\n';
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
bool Bot::fight_enemies(int round) {
    auto& me = cambc::self();
    const auto pos = me.position();
    const seen_champion* weakest = nullptr;
    float enemy_health = 0, ally_health = 0;
    vec2 centre{0, 0};
    int enemies_near = 0;
    const auto enemies = visible_champions(team::enemy);
    for (const auto& enemy : enemies) {
        if (distance(pos, enemy.position) > engage_radius)
            continue;
        ++enemies_near;
        enemy_health += enemy.health;
        centre = centre + enemy.position;
        if (!weakest || enemy.health < weakest->health)
            weakest = &enemy;
    }
    if (!weakest)
        return false;
    for (const auto& ally : visible_champions(team::ally))
        if (distance(pos, ally.position) <= engage_radius)
            ally_health += ally.health;

    const auto& target = weakest->unit;
    const bool even = ally_health >= enemy_health;
    const bool finish = weakest->health < 0.3f * weakest->max_health && ally_health >= 0.7f * enemy_health;
    if (!even && !finish) {
        mark_danger(vec2{centre.x / enemies_near, centre.y / enemies_near}, round);
        retreat();
        strike(target);  // melee can still hit after walking; casts that exclude walking are skipped
        return true;
    }
    const bool hit = strike(target);
    if (hit || squad == role::gold_squad)
        return hit;
    // Duo: close in; melee can still attack after walking.
    if (move_towards_closest(tiles_around(weakest->position, 1)))
        strike(target);
    return true;
}

bool Bot::should_tribute(int round) {
    auto& me = cambc::self();
    const int gems = static_cast<int>(me.gem_count());
    if (gems == 0)
        return false;
    if (gems >= tribute_gems)
        return true;
    for (auto altar : cambc::map::altars().positions())
        if (distance(me.position(), altar) <= tribute_detour)
            return true;
    // Nothing worth capturing right now: bank what we hold.
    return choose_target(round) < 0;
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
    if (auto* target = camps.group(read_slot(target_slot()) - 1))
        if (target->reward_ready && target->tiles.is_set(me.position()))
            return false;  // mid-capture
    me.recall();
    return true;
}

std::size_t Bot::target_slot() const {
    if (squad == role::gem_duo) return gem_target_slot;
    return solo_farm ? gold_member_slots[member] : gold_target_slot;
}

// Keep our target while it is worth it; otherwise pick the best rate from here. The duo shares one
// target. With solo_farm, each gold-squad member claims its own group and counts squad-mates that
// already claimed one as helpers (faster kill, but the reward is split among everyone present).
int Bot::choose_target(int round) {
    const auto slot = target_slot();
    if (auto* current = camps.group(read_slot(slot) - 1))
        if (current->respawn_round - round <= 10 && current->skip_until <= round && !near_danger(current->anchor, round))
            return read_slot(slot) - 1;

    const auto origin = cambc::self().position();
    cambc::distance_field field;
    cambc::bitboard visited;
    field.compute(terrain_blocked(), tiles_around(origin, 0), visited);

    const bool gold = squad == role::gold_squad;
    const bool solo = gold && solo_farm && squad_bodies > 1;
    const int duo_target = read_slot(gem_target_slot) - 1;
    auto& groups = camps.groups();
    std::vector<int> claimants(groups.size(), 0);
    if (solo)
        for (int k = 0; k < static_cast<int>(gold_member_slots.size()); ++k)
            if (k != member)
                if (const int c = read_slot(gold_member_slots[k]) - 1; c >= 0 && c < static_cast<int>(groups.size()))
                    ++claimants[c];

    const float my_damage = my_camp_damage(), my_health = cambc::self().max_health();

    // pack = true: v3's estimate, the whole squad on one target.
    auto pick = [&](bool pack) {
        int best = -1;
        float best_rate = 0;
        for (int i = 0; i < static_cast<int>(groups.size()); ++i) {
            const auto& g = groups[i];
            if (g.monolith || g.skip_until > round || near_danger(g.anchor, round) || (gold && i == duo_target))
                continue;
            const int travel = field.get(g.anchor);
            if (travel == cambc::distance_field::unreachable)
                continue;
            const int bodies = pack ? squad_bodies : 1 + claimants[i];
            // Solo/join estimates use our real damage plus generic bodies for the others.
            const float damage = pack ? body_damage * bodies : my_damage + body_damage * (bodies - 1);
            if (pack ? !survivable(g, bodies)
                     : g.exposure / damage > solo_damage_share * (my_health + body_health * (bodies - 1)))
                continue;
            const float kill_turns = g.health / damage;
            const float time = std::max<float>(travel, g.respawn_round - round) + kill_turns + capture_turns;
            // Gems win games; gold only buys stats. Value monsters' gems as well as their gold.
            float value = gold ? g.gems + squad_gold_weight * g.gold * (g.gold_only ? mining_weight : 1.f)
                               : static_cast<float>(g.gems);
            if (!pack) value /= bodies;
            if (value > 0 && value / time > best_rate) {
                best_rate = value / time;
                best = i;
            }
        }
        return best;
    };
    int best = pick(!solo);
    if (best < 0 && solo)
        best = pick(true);  // nothing one body can take: fall back to the squad estimate
    write_slot(slot, static_cast<std::uint8_t>(best + 1));
    return best;
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
        int bodies = 1;
        for (const auto& ally : visible_champions(team::ally))
            bodies += !(ally.unit == me) && distance(ally.position, group.anchor) <= 6;
        const bool ok = squad == role::gold_squad && solo_farm ? solo_survivable(group, bodies) : survivable(group, bodies);
        if (!ok) {
            // Wait for the squad at a safe distance (camps hit at range 3 and do not chase); give
            // up if nobody comes.
            waited = waiting_for == index ? waited + 1 : 1;
            waiting_for = index;
            if (waited > max_wait_turns) {
                group.skip_until = round + give_up_rounds;
                write_slot(target_slot(), 0);
            }
            if (threatened(camps, pos)) retreat();
            else if (distance(pos, group.anchor) > 5) move_towards_closest(group.tiles);
            return;
        }
    }
    if (target) {
        if (strike(*target))
            return;
        cambc::bitboard goals;
        goals.clear();
        goals.set(target->spawn_position());
        if (move_towards_closest(goals))
            strike(*target);
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

    auto& me = cambc::self();
    // A solo claim is ours alone: release it while we are dead or heading home so others can take it.
    const bool own_claim = squad == role::gold_squad && solo_farm;
    if (!me.is_alive()) {
        if (own_claim) write_slot(target_slot(), 0);
        shop();
        return;
    }
    // Leave channels running.
    if (me.is_recalling() && own_claim) write_slot(target_slot(), 0);
    if (me.is_recalling() || me.is_submitting_gems() || me.is_teleporting())
        return;

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
    if (fight_enemies(round))
        return;
    if (should_tribute(round)) {
        go_tribute();
        return;
    }
    if (shop_trip())
        return;

    const int target = choose_target(round);
    if (round % 100 == 0) {
        const auto p = me.position();
        std::cout << "status r" << round << ' ' << cambc::to_string(me.champion_name()) << " at " << p.x << ',' << p.y
                  << " gems=" << me.gem_count() << " gold=" << me.gold_count() << " hp=" << int(me.health())
                  << " target=" << target;
        if (const auto* g = camps.group(target))
            std::cout << " (" << g->anchor.x << ',' << g->anchor.y << " ready=" << g->reward_ready
                      << " respawn=" << g->respawn_round << " waited=" << (waiting_for == target ? waited : 0) << ')';
        std::cout << '\n';
    }
    if (target >= 0)
        work_group(target, round);
}
