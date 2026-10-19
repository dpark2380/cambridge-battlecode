#pragma once
#include <algorithm>

namespace jame {
// Marginal relative damage/survival gain per equal-cost shard. Stat ordering is
// strength, focus, health. This is a simple balancing rule, not a universal build.
inline int choose_stat(float strength, float focus, float health,
                       float strength_growth, float focus_growth, float health_growth,
                       float reset_rate, float focus_rate, float health_strength = 0,
                       float support_rate = 0) {
    const float dps = std::max(1.0f, strength * (1 + reset_rate) + focus * focus_rate);
    const float attack_value = strength_growth * (1 + reset_rate) / dps;
    const float spell_value = focus_growth * focus_rate / dps
        + focus_growth * support_rate / std::max(1.0f, health);
    const float health_value = health_growth / std::max(1.0f, health)
        + health_growth * health_strength * (1 + reset_rate) / dps;
    return health_value > std::max(attack_value, spell_value) ? 2 : spell_value > attack_value ? 1 : 0;
}
}
