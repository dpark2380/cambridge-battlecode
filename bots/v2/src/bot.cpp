// Strategy v2. Every champion, every turn:
//   dead -> shop | channelling -> wait | hurt -> recall | enemies -> fight (duo) or defend (squad)
//   | carrying gems -> tribute when worthwhile | rich -> recall to shop | else work our squad's target.
// Squad targets live in shared memory so members converge on the same camp group.
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

// Shared memory: one byte per squad holding target group index + 1 (0 = none).
constexpr std::size_t gem_target_slot = 0, gold_target_slot = 1;

// Rough per-body figures for kill-time and risk estimates (GameRules.md: ~50-90 damage/turn).
constexpr float body_damage = 70, body_health = 900;
constexpr int capture_turns = 5;
// Skip monster groups whose expected damage exceeds this multiple of the bodies' health. Above 1 on
// purpose: hurt champions walk out of reach (camps do not chase) and recall, so a costly fight
// costs time, not a death. This only rules out hopeless fights like a lone ranged champion on an elk.
constexpr float max_damage_share = 1.5f;
// Give up on a target after waiting this many turns for squad-mates, and ignore it for a while.
constexpr int max_wait_turns = 20, give_up_rounds = 60;
// Gold clusters ("mining") are valued at this fraction of monster gold: monsters come first.
constexpr float mining_weight = 0.5f;
constexpr float recall_health = 0.35f;
constexpr float spawn_leave_health = 0.9f;
constexpr int tribute_gems = 30;      // always bank at least this many
constexpr int tribute_detour = 8;     // bank anything when an altar is this close
constexpr int engage_radius = 5;

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

// Gold squad builds Jungle (30% less camp damage); the duo builds Power (an extra shard of stats).
cambc::item_type shard_for(role squad, stat s) {
    using cambc::item_type;
    if (squad == role::gold_squad) {
        switch (s) {
        case stat::strength: return item_type::jungle_shard_of_strength;
        case stat::health: return item_type::jungle_shard_of_health;
        case stat::focus: return item_type::jungle_shard_of_focus;
        }
    }
    switch (s) {
    case stat::strength: return item_type::power_shard_of_strength;
    case stat::health: return item_type::power_shard_of_health;
    default: return item_type::power_shard_of_focus;
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

// Monsters do not chase and hit at range 3: is anything that hurts within reach of `p`?
bool threatened(const world& camps, vec2 p) {
    for (const auto tile : (cambc::vision::camp_tiles() & tiles_around(p, 3)).positions())
        if (const auto* camp = camps.camp_at(tile); camp && !camp->is_gem_cluster() && !camp->is_gold_cluster())
            return true;
    return !(cambc::vision::champion_tiles(team::enemy) & tiles_around(p, 4)).is_empty();
}

std::uint8_t read_slot(std::size_t slot) { return cambc::shared_memory[slot]; }
void write_slot(std::size_t slot, std::uint8_t value) { cambc::shared_memory[slot] = value; }

} // namespace

void Bot::init() {
    initialised = true;
    plan = read_plan();
    const auto type = cambc::self().champion_name();
    if (plan) {
        squad = plan->role_of(type) == role::gem_duo ? role::gem_duo : role::gold_squad;
        squad_bodies = static_cast<int>(std::count(std::begin(plan->roles), std::end(plan->roles), squad));
    }
    camps.init();
    std::cout << "plan: " << cambc::to_string(type) << (squad == role::gem_duo ? " gem_duo" : " gold_squad")
              << " bodies=" << squad_bodies << (plan ? "" : " (no plan)") << '\n';
}

void Bot::shop() {
    auto& me = cambc::self();
    const auto item = shard_for(squad, build_stat[static_cast<int>(me.champion_name())]);
    const unsigned count = me.gold_count() / item.cost();
    if (count && me.can_buy(item, count))
        me.buy(item, count);
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

// Duo: fight when we are not outnumbered nearby, else back off. Squad: only hit what is in range.
bool Bot::fight_enemies() {
    auto& me = cambc::self();
    const auto pos = me.position();
    const seen_champion* weakest = nullptr;
    int enemies_near = 0, allies_near = 0;
    const auto enemies = visible_champions(team::enemy);
    for (const auto& enemy : enemies) {
        if (distance(pos, enemy.position) > engage_radius)
            continue;
        ++enemies_near;
        if (!weakest || enemy.health < weakest->health)
            weakest = &enemy;
    }
    if (!weakest)
        return false;
    for (const auto& ally : visible_champions(team::ally))
        allies_near += distance(pos, ally.position) <= engage_radius;

    const auto& target = weakest->unit;
    if (squad == role::gold_squad)
        return strike(target);

    const bool favourable = allies_near >= enemies_near || weakest->health < 0.3f * weakest->max_health;
    if (!favourable) {
        const bool hit = strike(target);
        if (me.health() < 0.6f * me.max_health()) retreat();
        return hit || moved;
    }
    if (strike(target))
        return true;
    // Close in; melee can still attack after walking.
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

void Bot::go_tribute() {
    auto& me = cambc::self();
    cambc::bitboard goals;
    goals.clear();
    for (auto altar : cambc::map::altars().positions()) {
        if (cambc::vision::has_altar_lock(altar))
            continue;
        if (distance(me.position(), altar) <= cambc::constants::submit_gems_range) {
            me.submit_gems(altar);
            return;
        }
        goals |= tiles_around(altar, cambc::constants::submit_gems_range);
    }
    move_towards_closest(goals);
}

// Gold only helps once spent: head home to shop when carrying an emblem's worth (Tavi shops anywhere).
bool Bot::shop_trip() {
    auto& me = cambc::self();
    const unsigned threshold = squad == role::gold_squad ? 150 : 300;
    if (me.champion_name() == cambc::champion_type::tavi || me.gold_count() < threshold || me.gem_count() > 0)
        return false;
    if (auto* target = camps.group(read_slot(squad == role::gem_duo ? gem_target_slot : gold_target_slot) - 1))
        if (target->reward_ready && target->tiles.is_set(me.position()))
            return false;  // mid-capture
    me.recall();
    return true;
}

// Keep the squad's shared target while it is worth it; otherwise pick the best rate from here.
int Bot::choose_target(int round) {
    const auto slot = squad == role::gem_duo ? gem_target_slot : gold_target_slot;
    const auto other = squad == role::gem_duo ? gold_target_slot : gem_target_slot;
    if (auto* current = camps.group(read_slot(slot) - 1))
        if (current->respawn_round - round <= 10 && current->skip_until <= round)
            return read_slot(slot) - 1;

    const auto origin = cambc::self().position();
    cambc::distance_field field;
    cambc::bitboard visited;
    field.compute(terrain_blocked(), tiles_around(origin, 0), visited);

    const float squad_damage = body_damage * squad_bodies;
    const int taken = read_slot(other) - 1;
    int best = -1;
    float best_rate = 0;
    auto& groups = camps.groups();
    for (int i = 0; i < static_cast<int>(groups.size()); ++i) {
        const auto& g = groups[i];
        if (g.monolith || g.skip_until > round)
            continue;
        const int travel = field.get(g.anchor);
        if (travel == cambc::distance_field::unreachable)
            continue;
        const float kill_turns = g.health / squad_damage;
        const float time = std::max<float>(travel, g.respawn_round - round) + kill_turns + capture_turns;

        if (!survivable(g, squad_bodies))
            continue;
        float value;
        if (squad == role::gem_duo) {
            value = static_cast<float>(g.gems);
        } else {
            if (i == taken || g.gold == 0)
                continue;
            value = g.gold * (g.gold_only ? mining_weight : 1.f);
        }
        if (value > 0 && value / time > best_rate) {
            best_rate = value / time;
            best = i;
        }
    }
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
        if (!survivable(group, bodies)) {
            // Wait for the squad at a safe distance (camps hit at range 3 and do not chase); give
            // up if nobody comes.
            waited = waiting_for == index ? waited + 1 : 1;
            waiting_for = index;
            if (waited > max_wait_turns) {
                group.skip_until = round + give_up_rounds;
                write_slot(squad == role::gem_duo ? gem_target_slot : gold_target_slot, 0);
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
    if (!me.is_alive()) {
        shop();
        return;
    }
    // Leave channels running.
    if (me.is_recalling() || me.is_submitting_gems() || me.is_teleporting())
        return;

    const bool at_spawn = cambc::map::spawn_region(team::ally).is_set(me.position());
    if (me.gold_count() >= 30 && (at_spawn || me.champion_name() == cambc::champion_type::tavi))
        shop();

    if (!at_spawn && me.health() < recall_health * me.max_health()) {
        // Damage cancels a recall: step out of reach first.
        if (threatened(camps, me.position())) retreat();
        else me.recall();
        return;
    }
    // Spawn heals every round: top up before heading back out.
    if (at_spawn && me.health() < spawn_leave_health * me.max_health())
        return;

    cast_support();
    if (fight_enemies())
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
