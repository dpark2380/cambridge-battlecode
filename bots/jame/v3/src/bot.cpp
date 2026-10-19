#include "bot.h"
#include "navigation.h"
#include "features.h"
#include "combat_model.h"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <string_view>

#include <utility>
#include <variant>

namespace jame {
namespace {
// An explicit v1 policy default, not a claim that 25% is optimal.
constexpr float recovery_fraction = 0.25f;
}

void Bot::initialize() {
    // Physical handles and spawn locations are static. Do not reload the whole
    // map's camp catalogue through the SDK every turn.
    std::array<std::optional<cambc::camp_stats>, 5> designs_by_type;
    camp_damage_multiplier_ = cambc::self().base_stats().camp_damage_multiplier;
    for (auto& group : cambc::map::camp_groups()) {
        const auto tiles = group.spawn_tiles();
        std::vector<cambc::camp_stats> designs;
        for (const auto& member : group.camps()) {
            auto& design = designs_by_type[static_cast<int>(member.kind())];
            if (!design)
                design = member.base_stats();
            designs.push_back(*design);
            if (design->base_strength > 0)
                actions_.remember_threat(member, design->base_attack_range);
        }
        groups_.push_back({std::move(group), tiles, std::move(designs)});
    }
    initialized_ = true;
}

bool Bot::attack_enemy() {
    const auto& me = cambc::self();
    if ((!me.can_attack() && !me.can_cast()) || cambc::fuel_remaining() < 35000) return false;
    for (const auto& enemy : cambc::vision::champions(cambc::team::enemy)) {
        if (enemy.is_alive() && actions_.engage(enemy, moved_)) {
            combat_ = true;
            return true;
        }
    }
    return false;
}

bool Bot::attack_camp() {
    const auto& me = cambc::self();
    if (target_ < 0 || (!me.can_attack() && !me.can_cast())) return false;
    std::vector<std::pair<float, cambc::camp>> candidates;
    const auto living = cambc::vision::camp_tiles();
    const auto origin = me.position();
    const float reach = actions_.reach();
    for (const auto& member : groups_[target_].view.camps())
        if (origin.chebyshev_distance(member.spawn_position()) <= reach
            && living.is_set(member.spawn_position()) && member.is_visible() && member.health() > 0)
            candidates.emplace_back(clear_priority(member.health(), member.strength()), member);
    std::stable_sort(candidates.begin(), candidates.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
    bool acted = false;
    for (const auto& [health, member] : candidates) {
        if (cambc::fuel_remaining() < 40000) break;
        if (actions_.engage(member, moved_)) { acted = true; attacked_ = true; }
        if (!me.can_attack() && !me.can_cast()) break;
    }
    return acted;
}

bool Bot::recall_is_clear() const {
    const auto origin = cambc::self().position();
    for (const auto& enemy : cambc::vision::champions(cambc::team::enemy)) {
        if (enemy.is_alive() && enemy.attack_tiles().is_set(origin))
            return false;
    }
    const auto living = cambc::vision::camp_tiles();
    for (const auto& group : groups_) {
        for (const auto& member : group.view.camps()) {
            if (living.is_set(member.spawn_position()) && member.is_visible()
                && member.strength() > 0 && member.attack_tiles().is_set(origin))
                return false;
        }
    }
    // Only current visible basic-attack coverage is checked. This is not an
    // escape predictor or a guarantee against hidden enemies, spells, or moves.
    return true;
}

const char* Bot::bank() {
    const auto& me = cambc::self();
    const auto origin = me.position();
    cambc::bitboard approaches;
    for (const auto altar : cambc::map::altars().positions()) {
        if (origin.chebyshev_distance(altar) <= cambc::constants::submit_gems_range) {
            // The engine turns a tribute attempt against an opposing lock into
            // a basic attack on that lock. Do not keep farming with a bag.
            me.submit_gems(altar);
            return "tribute-or-clear-lock";
        }
        approaches.draw_chebyshev(altar, cambc::constants::submit_gems_range);
    }
    moved_ = walk_to(approaches);
    return moved_ ? "walk-to-altar" : "bank-no-step";
}

void Bot::clear_target() {
    target_ = -1;
    progress_ = {};
    plan_ready_ = false;
    planning_cursor_ = 0;
}

cambc::bitboard Bot::goals_for(int index) const {
    const auto& group = groups_[index];
    const auto visible = cambc::vision::visible_tiles();
    if (!(group.tiles & visible).is_empty()) {
        const auto state = group.view.state();
        if (std::holds_alternative<cambc::map::camp_group_respawning>(state))
            return {};
        if (std::holds_alternative<cambc::map::camp_group_reward_available>(state))
            return group.tiles;
    }
    const auto living = cambc::vision::camp_tiles();
    cambc::bitboard goals;
    for (const auto& member : group.view.camps()) {
        const auto tile = member.spawn_position();
        if (living.is_set(tile))
            goals.draw_chebyshev(tile, cambc::self().attack_range());
        else if (!visible.is_set(tile))
            goals.set(tile); // Approach unseen spawns until personal vision reveals the target.
    }
    return goals;
}

float Bot::remaining_health(int index) const {
    float health = 0;
    const auto visible = cambc::vision::visible_tiles();
    const auto living = cambc::vision::camp_tiles();
    const auto& group = groups_[index];
    for (unsigned i = 0; i < group.designs.size(); ++i) {
        const auto& member = group.view.camps()[i];
        if (living.is_set(member.spawn_position()) && member.is_visible())
            health += member.health();
        else if (!visible.is_set(member.spawn_position()))
            health += group.designs[i].base_health;
    }
    return health;
}

bool Bot::plausible_clear(int index) {
    // Screen individually lethal monsters, not the whole group's survival cost.
    // Summing solo budgets rejects ordinary multi-wolf groups that allies can
    // clear together. Overlapping damage and assistance need the v3 estimator.
    const auto& me = cambc::self();
    const float damage = me.strength() * camp_damage_multiplier_ + nearby_damage_;
    if (damage <= 0)
        return false;
    const auto visible = cambc::vision::visible_tiles();
    const auto living = cambc::vision::camp_tiles();
    const auto& group = groups_[index];
    if (estimate_survival) {
        std::vector<Monster> monsters;
        for (unsigned i = 0; i < group.designs.size(); ++i) {
            const auto& member = group.view.camps()[i];
            const auto tile = member.spawn_position();
            if (visible.is_set(tile) && !living.is_set(tile)) continue;
            const bool observed = living.is_set(tile) && member.is_visible();
            monsters.push_back({observed ? member.health() : group.designs[i].base_health,
                                observed ? member.strength() : group.designs[i].base_strength});
        }
        const float camp_bonus = shop_.sets >= 1 ? 1.1f : 1;
        float dps = me.strength(), burst = 0;
        if (use_abilities) for (const auto& a : me.abilities()) {
            if (!a.info()) continue;
            const float period = std::visit([](const auto& p) { return float(std::max(1, p.max_cooldown)); }, *a.info());
            if (a.is_attack_reset()) {
                dps += me.strength() / period;
                if (a.is_ready()) burst = std::max(burst, me.strength());
            } else if (a.is_damage() || a.is_aoe_damage() || a.is_cc()) {
                const float amount = a.damage_amount();
                dps += amount / period;
                if (a.is_ready()) burst = std::max(burst, amount);
            }
        }
        const float mitigation = (shop_.sets >= 2 ? .7f : 1) * (shop_.sets >= 3 ? .9f : 1);
        // Assistance contributes damage only, discounted because proximity is
        // not a promise of help. Never assume allies absorb our incoming damage.
        const auto estimate = estimate_clear(std::move(monsters),
            dps * camp_damage_multiplier_ * camp_bonus + nearby_damage_ * .5f,
            burst * camp_damage_multiplier_ * camp_bonus, mitigation);
        last_clear_cost_ = estimate.cleared ? estimate.damage_taken : 1e30f;
        return estimate.cleared && estimate.damage_taken < me.health() * (1 - recovery_fraction);
    }
    float retaliation = 0;
    for (unsigned i = 0; i < group.designs.size(); ++i) {
        const auto& member = group.view.camps()[i];
        const auto tile = member.spawn_position();
        if (visible.is_set(tile) && !living.is_set(tile))
            continue;
        const bool observed = living.is_set(tile) && member.is_visible();
        const float hp = observed ? member.health() : group.designs[i].base_health;
        const float strength = observed ? member.strength() : group.designs[i].base_strength;
        retaliation = std::max(retaliation, std::max(0.0f, std::ceil(hp / damage) - 1) * strength);
    }
    return retaliation < me.health() * (1 - recovery_fraction);
}

bool Bot::select_target() {
    const auto& me = cambc::self();
    const auto round = cambc::round_number();
    const auto origin = me.position();
    const auto blocked = movement_blockers();
    cambc::bitboard destination;
    destination.set(origin);
    auto distance_to = [&](int index) {
        const auto goals = goals_for(index) & ~blocked;
        if (goals.is_empty())
            return int(cambc::distance_field::unreachable);
        cambc::bitboard visited;
        cambc::distance_field field;
        field.compute_to(blocked, goals, destination, visited);
        const int distance = field.get(origin);
        route_ = std::move(field);
        return distance;
    };
    if (target_ >= 0 && commit_targets) {
        const int distance = distance_to(target_);
        if (distance != cambc::distance_field::unreachable
            && !progress_.observe(distance, remaining_health(target_)))
            return true;
        if (distance != cambc::distance_field::unreachable)
            ++metrics_.stalled;
        else {
            const auto& group = groups_[target_];
            if (!(group.tiles & cambc::vision::visible_tiles()).is_empty()
                && std::holds_alternative<cambc::map::camp_group_respawning>(group.view.state()))
                ++metrics_.camp_respawns;
            else
                ++metrics_.blocked;
        }
        groups_[target_].retry_round = round + 12;
        ++metrics_.reselections;
        clear_target();
    }
    // Rank physical metadata cheaply; inspect live state only for candidates
    // actually considered. A bounded, resumable scan prevents dense maps from
    // silently consuming more than one owner turn.
    nearby_damage_ = 0;
    for (const auto& ally : cambc::vision::champions(cambc::team::ally)) {
        if (ally == me || !ally.is_alive())
            continue;
        if (ally.position().chebyshev_distance(origin) <= 4 && ally.health() >= ally.max_health() / 2)
            nearby_damage_ += ally.strength() * camp_damage_multiplier_;
    }
    const float damage = std::max(1.0f, me.strength() * camp_damage_multiplier_ + nearby_damage_);
    const float budget = me.health() * (1 - recovery_fraction);
    const float healed_budget = me.max_health() * (1 - recovery_fraction);
    if (planning_cursor_ == 0)
        needs_rest_ = false;
    planning_ = false;
    if (!plan_ready_) {
        candidates_.clear();
        for (unsigned i = 0; i < groups_.size(); ++i) {
            const auto& group = groups_[i];
            if (group.retry_round > round)
                continue;
            int distance = cambc::distance_field::unreachable;
            for (const auto& member : group.view.camps())
                distance = std::min(distance, int(origin.chebyshev_distance(member.spawn_position())));
            candidates_.push_back({int(i), distance, prefer_gems && group.view.gem_value() > 0, 0});
        }
        std::stable_sort(candidates_.begin(), candidates_.end(), [](const auto& a, const auto& b) {
            return a.gems != b.gems ? a.gems > b.gems : a.distance < b.distance;
        });
        plan_ready_ = true;
    }
    if (planning_cursor_ >= candidates_.size())
        planning_cursor_ = 0;
    for (; planning_cursor_ < candidates_.size(); ++planning_cursor_) {
        if (cambc::fuel_remaining() < 45000) {
            planning_ = true;
            return false;
        }
        // Refresh the cheap danger screen against current stats: the ranking
        // may have survived a yield while health, buffs or nearby allies changed.
        auto& candidate = candidates_[planning_cursor_];
        candidate.retaliation = 0;
        for (const auto& design : groups_[candidate.index].designs)
            candidate.retaliation = std::max(candidate.retaliation,
                std::max(0.0f, std::ceil(design.base_health / damage) - 1) * design.base_strength);
        if (buy_equipment && !candidate.gems && me.gold_count() >= 300) {
            needs_rest_ = true;
            break;
        }
        if (prefer_gems && !candidate.gems && needs_rest_)
            break;
        auto& group = groups_[candidate.index];
        const auto visible = cambc::vision::visible_tiles();
        if (!(group.tiles & visible).is_empty()) {
            const auto state = group.view.state();
            if (const auto* respawn = std::get_if<cambc::map::camp_group_respawning>(&state)) {
                group.retry_round = round + std::max(1, respawn->timer);
                continue;
            }
        }
        if ((estimate_survival || candidate.retaliation >= budget) && !plausible_clear(candidate.index)) {
            if (!needs_rest_ && candidate.gems && me.health() < me.max_health() * .95f
                && (estimate_survival ? last_clear_cost_ : candidate.retaliation) < healed_budget
                && distance_to(candidate.index) != cambc::distance_field::unreachable)
                needs_rest_ = true;
            continue;
        }
        const int distance = distance_to(candidate.index);
        if (distance == cambc::distance_field::unreachable) {
            ++metrics_.blocked;
            continue;
        }
        if (target_ != candidate.index) {
            clear_target();
            target_ = candidate.index;
        }
        planning_cursor_ = 0;
        progress_.observe(distance, remaining_health(target_));
        return true;
    }
    planning_cursor_ = 0;
    clear_target();
    if (buy_equipment && me.gold_count() >= 150)
        needs_rest_ = true;
    return false;
}

const char* Bot::farm() {
    const auto& me = cambc::self();
    const auto origin = me.position();
    route_.reset();
    // Preserve automatic capture, including partial/contested capture waits.
    // Respawning tiles are not capture goals and are left on the next decision.
    for (unsigned i = 0; i < groups_.size(); ++i) {
        const auto& group = groups_[i];
        if (group.tiles.is_set(origin)
            && std::holds_alternative<cambc::map::camp_group_reward_available>(group.view.state())) {
            target_ = i;
            progress_ = {};
            if (!(group.tiles & cambc::vision::champion_tiles(cambc::team::enemy)).is_empty())
                ++metrics_.contested;
            return "capture";
        }
    }
    if (cambc::fuel_remaining() < 50000)
        return "planning";
    const bool selected = select_target();
    // Leave enough fuel for movement's bounded obstruction retries and metrics.
    // Keep the selected target so the next turn can resume cheaply.
    if (cambc::fuel_remaining() < 25000)
        return "planning";
    if (!selected) {
        if (planning_)
            return "planning";
        if (needs_rest_) {
            recovering_ = true;
            return recover();
        }
        return "no-viable-work";
    }
    const bool attacked = attack_camp();
    if (!me.can_move())
        return attacked ? "attack-camp" : "no-move";
    // Query state again after damage: a last kill turns attack goals into capture tiles.
    moved_ = walk_to(goals_for(target_), !attacked && route_ ? &*route_ : nullptr);
    if (moved_ && (attack_enemy() || attack_camp()))
        return "walk-and-attack";
    if (attacked)
        return moved_ ? "attack-and-walk" : "attack-camp";
    return moved_ ? "walk-to-camp" : "farm-no-step";
}

const char* Bot::recover() {
    clear_target();
    if (recall_is_clear()) {
        cambc::self().recall();
        return "recall";
    }
    moved_ = walk_to(cambc::map::spawn_region(cambc::team::ally));
    return moved_ ? "walk-home" : "home-no-step";
}

const char* Bot::decide() {
    const auto& me = cambc::self();
    shop_.visit();
    if (!me.is_alive()) {
        recovering_ = false;
        clear_target();
        return "dead";
    }
    if (me.is_recalling() || me.is_submitting_gems() || me.is_teleporting())
        return "channel";
    if (!me.can_move() && !me.can_attack() && !me.can_cast())
        return "disabled";
    if (!initialized_)
        initialize();

    actions_.support(moved_);
    if (attack_enemy())
        return "attack-enemy";

    const bool at_spawn = cambc::map::spawn_region(cambc::team::ally).is_set(me.position());
    if (at_spawn) {
        if (me.health() < me.max_health())
            return "heal-on-spawn";
        recovering_ = false;
        if (target_ < 0) {
            const auto outside = ~cambc::map::spawn_region(cambc::team::ally);
            moved_ = walk_to(outside);
            if (moved_) return "leave-spawn";
        }
    } else if (me.health() < recovery_fraction * me.max_health()) {
        recovering_ = true;
    }
    if (recovering_) {
        return recover();
    }
    if (me.gem_count() > 0) {
        clear_target();
        return bank();
    }
    if (buy_equipment && !at_spawn && target_ < 0 && me.gold_count() >= 300) {
        recovering_ = true;
        return recover();
    }
    return farm();
}
void Bot::sample_progress() {
    const auto& me = cambc::self();
    const bool alive = me.is_alive();
    const auto gems = me.gem_count();
    const int round = cambc::round_number();
    if (sampled_) {
        if (was_alive_ && !alive)
            ++metrics_.deaths;
        if (!was_alive_ && alive)
            ++metrics_.respawns;
        if (alive && was_alive_ && capture_group_ >= 0
            && groups_[capture_group_].tiles.is_set(me.position())
            && std::holds_alternative<cambc::map::camp_group_respawning>(groups_[capture_group_].view.state())) {
            ++metrics_.captures;
            if (metrics_.first_capture < 0) {
                metrics_.first_capture = round;
                std::cout << "jame/v3 event=first-capture round=" << round
                          << " champion=" << cambc::to_string(me.champion_name()) << '\n';
            }
        }
        // No other v2 action spends gems. Require consecutive alive observations
        // and an observed tribute channel so deaths are never counted as deposits.
        if (alive && was_alive_ && was_submitting_ && gems < previous_gems_) {
            metrics_.banked += previous_gems_ - gems;
            if (metrics_.first_bank < 0) {
                metrics_.first_bank = round;
                std::cout << "jame/v3 event=first-bank round=" << round
                          << " champion=" << cambc::to_string(me.champion_name()) << '\n';
            }
        }
    }
    sampled_ = true;
    was_alive_ = alive;
    previous_gems_ = gems;
}

const char* Bot::turn() {
    sample_progress();
    moved_ = attacked_ = combat_ = false;
    actions_.begin_turn();
    const char* action = decide();
    const std::string_view name(action);
    metrics_.travel += moved_;
    metrics_.attacks += attacked_;
    metrics_.combat += combat_;
    metrics_.capture += name == "capture";
    metrics_.banking += name == "walk-to-altar" || name == "tribute-or-clear-lock" || name == "bank-no-step";
    metrics_.recovery += name == "recall" || name == "walk-home" || name == "home-no-step" || name == "heal-on-spawn";
    metrics_.dead += name == "dead";
    metrics_.disabled += name == "disabled";
    metrics_.channels += name == "channel";
    metrics_.planning += name == "planning";
    metrics_.idle += !moved_ && !attacked_ && !combat_ &&
        (name == "planning" || name == "farm-no-step" || name == "no-viable-work" || name == "no-move" || name == "bank-no-step" || name == "home-no-step");
    capture_group_ = name == "capture" ? target_ : -1;
    was_submitting_ = cambc::self().is_alive() && cambc::self().is_submitting_gems();
    return action;
}

void Bot::print_metrics() const {
    std::cout << "jame/v3 metrics round=" << cambc::round_number()
              << " champion=" << cambc::to_string(cambc::self().champion_name())
              << " casts=" << actions_.casts + dash_casts() << " resets=" << actions_.resets
              << " dash-casts=" << dash_casts()
              << " damage-casts=" << actions_.damage_casts << " support-casts=" << actions_.support_casts
              << " shards=" << shop_.shards << " emblems=" << shop_.sets
              << " travel=" << metrics_.travel << " camp-attacks=" << metrics_.attacks
              << " capture-turns=" << metrics_.capture << " banking-turns=" << metrics_.banking
              << " recovery=" << metrics_.recovery << " combat=" << metrics_.combat
              << " idle=" << metrics_.idle << " stalls=" << metrics_.stalled
              << " reselections=" << metrics_.reselections << " channels=" << metrics_.channels
              << " planning=" << metrics_.planning << " blocked=" << metrics_.blocked
              << " camp-respawns=" << metrics_.camp_respawns << " contested=" << metrics_.contested
              << " dead-turns=" << metrics_.dead << " disabled=" << metrics_.disabled
              << " deaths=" << metrics_.deaths << " respawns=" << metrics_.respawns
              << " captures=" << metrics_.captures << " banked=" << metrics_.banked
              << " first-capture=" << metrics_.first_capture << " first-bank=" << metrics_.first_bank
              << " target=" << target_ << " target-stall=" << progress_.stalled << '\n';
}

}
