#include "actions.h"
#include "features.h"
#include <algorithm>
#include <type_traits>

namespace jame {
namespace {
bool alive(const cambc::camp& c) { return c.is_visible() && c.health() > 0; }
bool alive(const cambc::champion& c) { return c.is_alive() && c.is_visible(); }
bool available(const cambc::ability& a, bool moved) {
    return a.info() && (!moved || !std::visit([](const auto& p) { return p.exclusive_with_movement; }, *a.info()))
        && a.is_ready();
}
}

template<class Target> bool Actions::fight(const Target& target, bool moved) {
    const auto& me = cambc::self();
    if (!alive(target)) return false;
    bool acted = false;
    auto attack = [&] {
        if (alive(target) && me.can_attack() && me.attack_tiles().is_set(target.position())) {
            me.attack(target);
            used_basic_ = true;
            ++attacks;
            acted = true;
        }
    };
    attack();
    if (!use_abilities || !alive(target) || !me.can_cast()) return acted;
    const auto abilities = me.abilities();
    int best = -1;
    float best_value = 0;
    for (unsigned i = 0; i < abilities.size(); ++i) {
        const auto& a = abilities[i];
        if (!available(a, moved)) continue;
        const auto targets = std::visit([](const auto& p) { return p.valid_targets; }, *a.info());
        float value = 0;
        if (a.is_attack_reset()) {
            if (used_basic_ && !me.can_attack() && me.attack_tiles().is_set(target.position()))
                value = std::min(target.health(), me.strength()) + (a.get<cambc::ability_attack_reset>().enhanced_attack ? me.focus() : 0);
        } else if (a.is_damage() || a.is_cc() || a.is_aoe_damage()) {
            if (!a.valid_tiles().is_set(target.position())) continue;
            const bool unit_allowed = std::is_same_v<Target, cambc::camp>
                ? targets.contains(cambc::ability_target_mask::camps)
                : targets.contains(cambc::ability_target_mask::enemies);
            if (!unit_allowed && !targets.contains(cambc::ability_target_mask::ground)) continue;
            value = std::min(target.health(), a.damage_amount());
            if (a.is_cc() && target.strength() > 0 && target.attack_tiles().is_set(me.position())
                && !target.buffs().has_stun())
                value += target.strength() * a.get<cambc::ability_cc>().duration;
            if (a.is_aoe_damage()) {
                const auto info = a.get<cambc::ability_aoe_damage>();
                cambc::bitboard area;
                area.draw_chebyshev(target.position(), info.radius);
                const auto count = (area & (cambc::vision::camp_tiles() | cambc::vision::champion_tiles(cambc::team::enemy))).count();
                value *= std::max(1u, count);
            }
        }
        if (value > best_value) { best_value = value; best = i; }
    }
    if (best < 0 || !alive(target)) return acted;
    const auto& a = abilities[best];
    bool cast = false;
    if (a.is_attack_reset()) cast = a.use();
    else {
        const auto targets = std::visit([](const auto& p) { return p.valid_targets; }, *a.info());
        if (targets.contains(cambc::ability_target_mask::ground)) cast = a.use(target.position());
        else cast = a.use(target);
    }
    if (cast) {
        ++casts;
        acted = true;
        if (a.is_attack_reset()) { ++resets; attack(); }
        else ++damage_casts;
    }
    return acted;
}

bool Actions::engage(const cambc::camp& target, bool moved) { return fight(target, moved); }
bool Actions::engage(const cambc::champion& target, bool moved) { return fight(target, moved); }

float Actions::reach() const {
    const auto& me = cambc::self();
    float range = me.attack_range();
    if (use_abilities && me.can_cast()) for (const auto& a : me.abilities()) {
        if (a.is_damage() || a.is_cc() || a.is_aoe_damage())
            std::visit([&](const auto& p) { if constexpr (requires { p.range; }) range = std::max(range, p.range); }, *a.info());
    }
    return range;
}

bool Actions::support(bool moved) {
    const auto& me = cambc::self();
    if (!use_abilities || !me.can_cast()) return false;
    for (const auto& a : me.abilities()) {
        if ((!a.is_heal() && !a.is_shield()) || !available(a, moved)) continue;
        const auto flags = std::visit([](const auto& p) { return p.valid_targets; }, *a.info());
        const auto range = a.valid_tiles();
        auto allies = cambc::vision::champions(cambc::team::ally);
        if (flags.contains(cambc::ability_target_mask::self)
            && std::none_of(allies.begin(), allies.end(), [&](const auto& c) { return c == me; }))
            allies.push_back(me);
        for (const auto& ally : allies) {
            if (!ally.is_alive() || !range.is_set(ally.position())) continue;
            if (ally == me ? !flags.contains(cambc::ability_target_mask::self)
                           : !flags.contains(cambc::ability_target_mask::allies)) continue;
            bool useful = false;
            if (a.is_heal())
                useful = ally.health() < ally.max_health() * .65f
                    && ally.max_health() - ally.health() >= a.heal_amount() * .5f;
            else if (!ally.buffs().has_shield()) {
                // Shield only existing attack exposure, rather than every cooldown.
                for (const auto& enemy : cambc::vision::champions(cambc::team::enemy))
                    useful |= enemy.is_alive() && enemy.attack_tiles().is_set(ally.position());
                if (!useful) {
                    if (ally.health() < ally.max_health() * .8f) {
                        const auto living = cambc::vision::camp_tiles();
                        const auto position = ally.position();
                        for (const auto& threat : threats_)
                            if (living.is_set(threat.camp.spawn_position())
                                && position.chebyshev_distance(threat.camp.spawn_position()) <= threat.range) {
                                useful = true;
                                break;
                            }
                    }
                }
            }
            if (useful && (ally == me ? a.use() : a.use(ally))) { ++casts; ++support_casts; return true; }
        }
    }
    return false;
}
}
