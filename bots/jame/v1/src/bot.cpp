#include "bot.h"
#include "navigation.h"

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
    for (auto& group : cambc::map::camp_groups()) {
        const auto tiles = group.spawn_tiles();
        groups_.push_back({std::move(group), tiles});
    }
    initialized_ = true;
}

bool Bot::attack_enemy() const {
    const auto& me = cambc::self();
    if (!me.can_attack())
        return false;
    const auto range = me.attack_tiles();
    // First legal target in SDK tile order: no chase, focus-fire, or prediction.
    for (const auto& enemy : cambc::vision::champions(cambc::team::enemy)) {
        if (enemy.is_alive() && range.is_set(enemy.position())) {
            me.attack(enemy);
            return true;
        }
    }
    return false;
}

bool Bot::attack_camp() const {
    const auto& me = cambc::self();
    if (!me.can_attack())
        return false;
    const auto targets = me.attack_tiles() & cambc::vision::camp_tiles();
    for (const auto& group : groups_) {
        for (const auto& member : group.view.camps()) {
            if (targets.is_set(member.spawn_position()) && member.is_visible() && member.health() > 0) {
                me.attack(member);
                return true;
            }
        }
    }
    return false;
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

const char* Bot::bank() const {
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
    return walk_to(approaches) ? "walk-to-altar" : "bank-no-step";
}

const char* Bot::farm() const {
    const auto& me = cambc::self();
    const auto origin = me.position();
    const auto visible = cambc::vision::visible_tiles();
    auto living = cambc::vision::camp_tiles();

    // Stay on a ready region until its automatic capture completes.
    for (const auto& group : groups_) {
        if (group.tiles.is_set(origin)
            && std::holds_alternative<cambc::map::camp_group_reward_available>(group.view.state()))
            return "capture";
    }

    const bool attacked = attack_camp();
    if (!me.can_move())
        return attacked ? "attack-camp" : "no-move";

    // A melee attack may have cleared the last monster. Refresh occupancy and
    // group state before choosing a capture tile for the remaining movement.
    living = cambc::vision::camp_tiles();
    cambc::bitboard goals;
    for (const auto& group : groups_) {
        if (!(group.tiles & visible).is_empty()) {
            const auto state = group.view.state();
            if (std::holds_alternative<cambc::map::camp_group_respawning>(state))
                continue; // In particular, never wait on a respawn tile.
            if (std::holds_alternative<cambc::map::camp_group_reward_available>(state)) {
                goals |= group.tiles;
                continue;
            }
        }
        for (const auto& member : group.view.camps()) {
            const auto tile = member.spawn_position();
            if (living.is_set(tile))
                goals.draw_chebyshev(tile, me.attack_range());
            else if (!visible.is_set(tile))
                goals.set(tile); // Approach known layout without inventing hidden live state.
        }
    }
    const bool moved = walk_to(goals);
    // Movement can reveal a new target; ranged move/attack exclusion is checked
    // by can_attack(), so this also handles melee moving into attack range.
    if (moved && (attack_enemy() || attack_camp()))
        return "walk-and-attack";
    if (attacked)
        return moved ? "attack-and-walk" : "attack-camp";
    return moved ? "walk-to-camp" : "farm-no-step";
}

const char* Bot::turn() {
    const auto& me = cambc::self();
    if (!me.is_alive()) {
        recovering_ = false;
        return "dead";
    }
    if (me.is_recalling() || me.is_submitting_gems() || me.is_teleporting())
        return "channel";
    if (!me.can_move() && !me.can_attack())
        return "disabled";
    if (!initialized_)
        initialize();

    if (attack_enemy())
        return "attack-enemy";

    const bool at_spawn = cambc::map::spawn_region(cambc::team::ally).is_set(me.position());
    if (at_spawn) {
        if (me.health() < me.max_health())
            return "heal-on-spawn";
        recovering_ = false;
    } else if (me.health() < recovery_fraction * me.max_health()) {
        recovering_ = true;
    }
    if (recovering_) {
        if (recall_is_clear()) {
            me.recall();
            return "recall";
        }
        return walk_to(cambc::map::spawn_region(cambc::team::ally)) ? "walk-home" : "home-no-step";
    }
    if (me.gem_count() > 0)
        return bank();
    return farm();
}
}
