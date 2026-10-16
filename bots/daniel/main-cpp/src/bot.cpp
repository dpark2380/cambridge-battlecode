// Champion decisions. main.cpp dispatches here after the draft.
// Plan each turn: shop, recall if hurt, fight enemies in range, bank gems, farm the best camp group.
#include <cambc.h>
#include "bot.h"
#include "params.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <variant>

using cambc::vec2;
using cambc::team;

namespace {

int distance(vec2 a, vec2 b) { return static_cast<int>(a.chebyshev_distance(b)); }

cambc::bitboard tiles_around(vec2 p, int radius) {
    cambc::bitboard tiles;
    tiles.clear();
    tiles.draw_chebyshev(p, radius);
    return tiles;
}

// Static terrain plus everything visible that occupies a tile.
cambc::bitboard blocked_now(const cambc::bitboard& terrain) {
    auto blocked = terrain | cambc::vision::champion_tiles() | cambc::vision::camp_tiles()
        | cambc::vision::teleport_tiles();
    blocked.set(cambc::self().position(), false);
    return blocked;
}

// Rough damage per turn against camps: basic attacks plus damaging spells averaged over their cooldown.
float camp_dps(const cambc::champion& me) {
    float dps = me.strength();
    for (const auto& ability : me.abilities()) {
        if (ability.is_attack_reset()) dps += me.strength() / 8.0f;
        else if (ability.is_damage() || ability.is_aoe_damage() || ability.is_cc()) dps += ability.damage_amount() / 8.0f;
    }
    return dps * me.base_stats().camp_damage_multiplier;
}

// Visible camps within Chebyshev `radius`. vision::camps() costs ~35k fuel; this is a few k.
std::vector<cambc::camp> camps_near(int radius) {
    std::vector<cambc::camp> camps;
    for (auto tile : (cambc::vision::camp_tiles() & tiles_around(cambc::self().position(), radius)).positions())
        camps.push_back(cambc::vision::camp_at(tile));
    return camps;
}

// Step to the free neighbour closest to `goal` (Chebyshev, ties broken by Euclidean).
bool approach(vec2 goal) {
    auto& me = cambc::self();
    if (!me.can_move()) return false;
    const auto blocked = cambc::map::walls() | cambc::map::holes() | cambc::map::altars()
        | cambc::map::spawn_region(team::enemy) | cambc::vision::champion_tiles() | cambc::vision::camp_tiles();
    const auto from = me.position();
    auto score = [&](vec2 p) { return distance(p, goal) * 1000 + (p.x - goal.x) * (p.x - goal.x) + (p.y - goal.y) * (p.y - goal.y); };
    auto best = from;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 tile{from.x + dx, from.y + dy};
            if (cambc::map::is_in_bounds(tile) && !blocked.is_set(tile) && score(tile) < score(best)) best = tile;
        }
    return best != from && me.move_absolute(best);
}

} // namespace

void Bot::init() {
    initialised = true;
    auto& me = cambc::self();
    const auto allies = cambc::champions(team::ally);
    for (std::size_t i = 0; i < allies.size(); ++i)
        if (allies[i] == me) slot = static_cast<int>(i);

    groups = cambc::map::camp_groups();
    for (const auto& group : groups) {
        GroupInfo g{group.spawn_tiles(), {}, 0, 0, group.gem_value() + W_GOLD * group.gold_value()};
        g.positions = g.tiles.positions();
        for (const auto& camp : group.camps()) {
            g.health += camp.base_stats().base_health;
            g.strength += camp.base_stats().base_strength;
        }
        info.push_back(std::move(g));
    }
    respawn_round.assign(groups.size(), 0);
    fields.resize(groups.size());
    field_ready.assign(groups.size(), false);

    terrain = cambc::map::walls() | cambc::map::holes() | cambc::map::altars() | cambc::map::spawn_region(team::enemy);

    // One field to the nearest altar approach tile.
    cambc::bitboard roots;
    roots.clear();
    for (auto altar : cambc::map::altars().positions())
        roots |= tiles_around(altar, cambc::constants::submit_gems_range);
    roots &= ~terrain;
    cambc::bitboard visited;
    altar_field.compute(terrain, roots, visited);
    for (std::size_t g = 0; g < groups.size() && cambc::fuel_remaining() > FIELD_RESERVE; ++g)
        group_field(static_cast<int>(g)); // ~1-4k fuel each; leftovers are built by build_fields
}

// Walking distance once the group's field exists, otherwise a Chebyshev estimate (fields cost ~40k fuel each).
float Bot::travel_to(int g) {
    const auto origin = cambc::self().position();
    if (field_ready[g]) return fields[g].get(origin);
    int best = 1 << 20;
    for (auto tile : info[g].positions) best = std::min(best, distance(origin, tile));
    return best * 1.3f;
}

// Spend leftover fuel building any distance fields init could not afford.
void Bot::build_fields(std::uint64_t reserve) {
    for (std::size_t g = 0; g < groups.size() && cambc::fuel_remaining() > reserve; ++g)
        if (!field_ready[g]) group_field(static_cast<int>(g));
}

const cambc::distance_field& Bot::group_field(int g) {
    if (!field_ready[g]) {
        cambc::bitboard visited;
        fields[g].compute(terrain, info[g].tiles, visited);

        field_ready[g] = true;
    }
    return fields[g];
}

// Take the free step (or dash) that most reduces the static distance.
bool Bot::step_along(const cambc::distance_field& field, bool allow_dash) {
    auto& me = cambc::self();
    const auto origin = me.position();
    const auto blocked = blocked_now(terrain);

    if (allow_dash && me.can_cast() && field.get(origin) > 4) {
        for (const auto& ability : me.abilities()) {
            if (!ability.is_dash() || !ability.is_ready()) continue;
            auto best = origin;
            for (auto tile : (ability.valid_tiles() & blocked.reachable_tiles(origin, 2)).positions())
                if (field.get(tile) < field.get(best)) best = tile;
            if (best != origin && field.get(best) + 1 < field.get(origin) && ability.use(best)) break;
        }
    }

    if (!me.can_move()) return false;
    const auto from = me.position();
    auto best = from;
    for (int dx = -1; dx <= 1; ++dx)
        for (int dy = -1; dy <= 1; ++dy) {
            const vec2 tile{from.x + dx, from.y + dy};
            if (cambc::map::is_in_bounds(tile) && !blocked.is_set(tile) && field.get(tile) < field.get(best)) best = tile;
        }
    return best != from && me.move_absolute(best);
}

// Remember respawn timers of groups we can see; unseen groups keep their last known timer.
void Bot::observe_groups() {
    const int now = static_cast<int>(cambc::round_number());
    for (std::size_t g = 0; g < groups.size(); ++g) {
        bool seen = false;
        for (auto tile : info[g].positions) seen = seen || visible.is_set(tile);
        if (!seen) continue;
        const auto state = groups[g].state();
        if (const auto* r = std::get_if<cambc::map::camp_group_respawning>(&state))
            respawn_round[g] = now + r->timer;
        else
            respawn_round[g] = 0;
    }
}

void Bot::claim(int g) {
    cambc::shared_memory[slot] = static_cast<std::uint8_t>(g + 1);
}

// Best reward per turn among groups we can survive, sharing rewards with allies who claimed them.
int Bot::choose_group() {
    auto& me = cambc::self();
    const auto origin = me.position();
    const int now = static_cast<int>(cambc::round_number());
    const float dps = std::max(1.0f, camp_dps(me));

    std::array<int, 256> claims{};
    for (std::size_t i = 0; i < cambc::shared_memory_buffer::size(); ++i) {
        const int c = static_cast<int>(static_cast<std::uint8_t>(cambc::shared_memory[i]));
        if (c > 0 && static_cast<int>(i) != slot) ++claims[c - 1];
    }

    int best = -1;
    float best_rate = 0;
    for (std::size_t g = 0; g < groups.size(); ++g) {
        const float travel = travel_to(static_cast<int>(g));
        if (travel >= cambc::distance_field::unreachable) continue;
        const float wait = std::max(0.0f, static_cast<float>(respawn_round[g] - now) - travel);

        const float health = info[g].health, strength = info[g].strength;
        const int helpers = 1 + claims[g];
        const float kill_turns = health / (dps * helpers);
        const float damage = strength * kill_turns / helpers;
        // Damage beyond what we can absorb costs recall round trips instead of ruling the group out.
        const float excess = std::max(0.0f, damage - me.health() * CAMP_SAFETY) / me.max_health();
        const float recall_turns = excess * (RECALL_TRIP + 2 * travel);

        const float value = info[g].value / helpers;
        const float rate = value / (TRAVEL_W * travel + wait + kill_turns + recall_turns + cambc::constants::capture_time + 1);
        if (rate > best_rate || (g == static_cast<std::size_t>(target) && rate >= best_rate * 0.9f)) {
            best_rate = rate;
            best = static_cast<int>(g);
        }
    }
    return best;
}

void Bot::buy_items() {
    using cambc::item_type;
    auto& me = cambc::self();
    // Jungle emblem first (camps hurt less), then Monster (camps die faster), then raw Power shards.
    const bool caster = me.focus() * 2 > me.strength() * 8;
    static constexpr std::array<std::array<item_type, 3>, 3> families{{
        {item_type::jungle_shard_of_strength, item_type::jungle_shard_of_focus, item_type::jungle_shard_of_health},
        {item_type::monster_shard_of_strength, item_type::monster_shard_of_focus, item_type::monster_shard_of_health},
        {item_type::power_shard_of_strength, item_type::power_shard_of_focus, item_type::power_shard_of_health},
    }};
    while (true) {
        const auto& family = families[std::min<unsigned>(shards_bought / 5, 2)];
        const int every = std::max(1, static_cast<int>(STAT_HEALTH_EVERY));
        const auto item = (shards_bought % 5) % every == every - 1 ? family[2] : family[caster ? 1 : 0];
        if (me.gold_count() < item.cost() || !me.can_buy(item)) return;
        me.buy(item);
        ++shards_bought;
    }
}

// Use the first ready offensive spell on a target in range.
template<class Target>
bool cast_spell_on(const Target& target) {
    auto& me = cambc::self();
    if (!me.can_cast()) return false;
    for (const auto& ability : me.abilities()) {
        if (!ability.is_ready() || !(ability.is_damage() || ability.is_cc() || ability.is_aoe_damage())) continue;
        if (!ability.valid_tiles().is_set(target.position())) continue;
        if (ability.can_target_ground() ? ability.use(target.position()) : ability.use(target)) return true;
    }
    return false;
}

// Basic attack, then an attack reset for a second hit.
template<class Target>
bool hit(const Target& target) {
    auto& me = cambc::self();
    if (!target.is_visible() || target.health() <= 0) return false;
    bool acted = cast_spell_on(target);
    if (me.can_attack() && distance(me.position(), target.position()) <= me.attack_range()) {
        me.attack(target);
        acted = true;
        if (me.can_cast())
            for (const auto& ability : me.abilities())
                if (ability.is_attack_reset() && ability.is_ready() && ability.use()) {
                    if (me.can_attack() && target.is_visible() && target.health() > 0) me.attack(target);
                    break;
                }
    }
    return acted;
}

bool Bot::fight_enemies() {
    auto& me = cambc::self();
    const auto enemies = cambc::vision::champions(team::enemy);
    const cambc::champion* best = nullptr;
    for (const auto& enemy : enemies) {
        if (!enemy.is_visible() || enemy.health() <= 0) continue;
        if (me.health() * me.strength() < FIGHT_RATIO * enemy.health() * enemy.strength() && enemy.gem_count() == 0) continue;
        if (!best || enemy.health() < best->health()) best = &enemy;
    }
    return best && hit(*best);
}

void heal_allies() {
    auto& me = cambc::self();
    if (!me.can_cast()) return;
    for (const auto& ability : me.abilities()) {
        if (!ability.is_heal() || !ability.is_ready()) continue;
        const cambc::champion* worst = nullptr;
        for (const auto& ally : cambc::vision::champions(team::ally))
            if (!(ally == me) && ally.is_visible() && ally.health() > 0 && ability.valid_tiles().is_set(ally.position())
                && ally.max_health() - ally.health() > ability.heal_amount(ally) * 0.7f
                && (!worst || ally.health() / ally.max_health() < worst->health() / worst->max_health()))
                worst = &ally;
        if (worst) ability.use(*worst);
    }
}

void shield_if_hurt() {
    auto& me = cambc::self();
    if (!me.can_cast() || me.health() > me.max_health() * 0.9f) return;
    for (const auto& ability : me.abilities())
        if (ability.is_shield() && ability.is_ready()) ability.use();
}

bool Bot::farm() {
    auto& me = cambc::self();
    // Hit the weakest camp within spell reach, but leave monoliths alone unless they are the target.
    const cambc::camp* best = nullptr;
    const auto camps = camps_near(std::max(me.attack_range(), 4)); // spells reach 4
    for (const auto& camp : camps)
        if (camp.health() > 0 && (!camp.is_monolith() || camp.camp_group() == groups[std::max(target, 0)])
            && (!best || camp.health() < best->health()))
            best = &camp;
    if (best) {
        hit(*best);
        target = static_cast<int>(std::find(groups.begin(), groups.end(), best->camp_group()) - groups.begin());
        claim(target);
        if (!me.can_move() || distance(me.position(), best->position()) <= me.attack_range()) return true;
        if (approach(best->position())) {
            for (const auto& camp : camps_near(me.attack_range()))
                if (camp.health() > 0 && !camp.is_monolith()) return hit(camp);
            return true;
        }
    } else {
        target = choose_group();
        if (target < 0) return false;
        claim(target);
    }

    const auto& tiles = info[target].tiles;
    if (tiles.is_set(me.position())) {
        // Capture by standing still, but never sit on a respawning group: occupied tiles delay its respawn.
        const auto state = groups[target].state();
        if (!std::holds_alternative<cambc::map::camp_group_respawning>(state)) return true;
        const auto blocked = blocked_now(terrain) | tiles;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy) {
                const vec2 tile{me.position().x + dx, me.position().y + dy};
                if (cambc::map::is_in_bounds(tile) && !blocked.is_set(tile) && me.move_absolute(tile)) return true;
            }
        return true;
    }

    if (!field_ready[target] || !step_along(fields[target], true)) {
        // No static field yet, or allies block the static route: path around visible units instead.
        auto goal = info[target].positions[0];
        for (auto tile : info[target].positions) if (distance(me.position(), tile) < distance(me.position(), goal)) goal = tile;
        if (me.can_move() && !cambc::vision::has_camp(goal) && !cambc::vision::has_champion(goal)) me.move_towards(goal);
    }

    // Fresh vision after moving may put a camp in range.
    for (const auto& camp : camps_near(me.attack_range()))
        if (camp.health() > 0 && !camp.is_monolith()) return hit(camp);
    return true;
}

bool Bot::tribute() {
    auto& me = cambc::self();
    for (auto altar : cambc::map::altars().positions())
        if (distance(me.position(), altar) <= cambc::constants::submit_gems_range) {
            me.submit_gems(altar);
            return true;
        }
    return step_along(altar_field, true);
}

void Bot::play_turn() {
    if (!initialised) init();
    visible = cambc::vision::visible_tiles();
    act();
    build_fields(FIELD_RESERVE);
}

void Bot::act() {
    auto& me = cambc::self();
    observe_groups();

    if (!me.is_alive()) {
        buy_items(); // dead champions may shop
        cambc::shared_memory[slot] = std::uint8_t{0};
        return;
    }
    if (me.is_recalling() || me.is_submitting_gems() || me.is_teleporting()) return;

    const bool at_spawn = cambc::map::spawn_region(team::ally).is_set(me.position());
    if (at_spawn || me.passive() == cambc::passive_type::remote_shop) buy_items();

    const float hp = me.health() / me.max_health();
    const unsigned gems = me.gem_count();
    const bool on_target_tiles = target >= 0 && info[target].tiles.is_set(me.position());
    // Damage we take per turn from what can hit us now: camps within 3, enemy champions within 4.
    float incoming = 0;
    for (const auto& camp : camps_near(3)) incoming += camp.strength();
    for (auto tile : (cambc::vision::champion_tiles(team::enemy) & tiles_around(me.position(), 4)).positions())
        incoming += 1.5f * cambc::vision::champion_at(tile).strength();
    const bool in_danger = me.health() < incoming * ESCAPE_TURNS;
    if (!at_spawn && (!on_target_tiles || in_danger)
        && (in_danger || hp < RECALL_HP + GEM_RISK * gems / 100.0f)) {
        // Recall breaks on damage: first walk out of camp and enemy reach.
        const auto threats = (cambc::vision::camp_tiles() & tiles_around(me.position(), 3))
            | (cambc::vision::champion_tiles(team::enemy) & tiles_around(me.position(), 4));
        if (!threats.is_empty()) {
            if (fight_enemies() || !me.can_move()) return;
            const auto blocked = blocked_now(terrain);
            const auto threat_tiles = threats.positions();
            auto safest = [&](vec2 p) { int d = 99; for (auto t : threat_tiles) d = std::min(d, distance(p, t)); return d; };
            auto best = me.position();
            for (int dx = -1; dx <= 1; ++dx)
                for (int dy = -1; dy <= 1; ++dy) {
                    const vec2 tile{best.x + dx, best.y + dy};
                    if (cambc::map::is_in_bounds(tile) && !blocked.is_set(tile) && safest(tile) > safest(best)) best = tile;
                }
            if (best != me.position()) me.move_absolute(best);
            return;
        }
        cambc::shared_memory[slot] = std::uint8_t{0};
        me.recall();
        return;
    }

    heal_allies();
    shield_if_hurt();
    if (fight_enemies()) return;

    const auto near_altar = altar_field.get(me.position());
    if (gems > 0 && (gems >= TRIBUTE_GEMS || near_altar <= TRIBUTE_NEAR) && !on_target_tiles) {
        tribute();
        return;
    }

    if (!farm() && gems > 0) tribute();
}
