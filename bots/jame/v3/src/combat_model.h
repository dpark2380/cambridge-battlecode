#pragma once
#include <algorithm>
#include <cmath>
#include <vector>

namespace jame {
struct Monster { float health, damage; };
struct ClearEstimate { float damage_taken = 0; int rounds = 0; bool cleared = false; };
inline float clear_priority(float health, float damage) {
    return health <= 0 ? 1e30f : damage > 0 ? health / damage : 1e20f + health;
}
// An analytical group estimate: every survivor can retaliate each phase.
// Remove incoming damage first; count ready burst once, then sustained damage.
// No speculative allied tanking, healing or future stun chains.
inline ClearEstimate estimate_clear(std::vector<Monster> monsters, float dps, float burst,
                                    float mitigation = 1, int horizon = 80) {
    ClearEstimate result;
    auto order = [](const auto& a, const auto& b) {
        return clear_priority(a.health, a.damage) < clear_priority(b.health, b.damage);
    };
    std::stable_sort(monsters.begin(), monsters.end(), order);
    if (burst > 0 && !monsters.empty()) monsters.front().health -= burst;
    std::stable_sort(monsters.begin(), monsters.end(), order);
    float incoming = 0;
    for (const auto& m : monsters) if (m.health > 0) incoming += m.damage;
    for (const auto& m : monsters) {
        if (m.health <= 0) continue;
        if (dps <= 0) return result;
        const int hits = int(std::ceil(m.health / dps));
        const int available = std::max(0, horizon - result.rounds);
        if (hits > available) {
            result.damage_taken += incoming * available * mitigation;
            result.rounds += available;
            return result;
        }
        // On the killing phase only the other surviving monsters retaliate.
        result.damage_taken += std::max(0.0f, incoming * hits - m.damage) * mitigation;
        incoming -= m.damage;
        result.rounds += hits;
    }
    result.cleared = true;
    return result;
}
}
