#include "shop.h"
#include "features.h"
#include "economy.h"
#include <algorithm>

namespace jame {
void Shop::visit() {
    if (!buy_equipment) return;
    const auto& me = cambc::self();
    if (me.gold_count() < 30) return;
    if (me.is_alive() && !cambc::map::spawn_region(cambc::team::ally).is_set(me.position())) return;
    // Finish each five-shard block before changing stat or family. Duplicate
    // passives do not stack, so use Power after the three distinct passives.
    for (int block = 0; block < 4 && cambc::fuel_remaining() > 45000; ++block) {
        if (!partial_) {
            const auto stats = me.base_stats();
            float focus_rate = 0, reset_rate = 0, support_rate = 0;
            for (const auto& a : me.abilities()) {
                if (!a.info()) continue;
                std::visit([&](const auto& p) {
                    const float period = std::max(1, p.max_cooldown);
                    using T = std::decay_t<decltype(p)>;
                    if constexpr (std::is_same_v<T, cambc::ability_attack_reset>) reset_rate += 1 / period;
                    else if constexpr (std::is_same_v<T, cambc::ability_heal> || std::is_same_v<T, cambc::ability_shield>)
                        support_rate += p.modifier / period;
                    else if constexpr (requires { p.modifier; }) focus_rate += p.modifier / period;
                }, *a.info());
            }
            const int stat = choose_stat(me.strength(), me.focus(), me.max_health(),
                stats.strength_growth, stats.focus_growth, stats.health_growth,
                use_abilities ? reset_rate : 0, use_abilities ? focus_rate : 0,
                me.passive() == cambc::passive_type::health_strength ? .01f : 0,
                use_abilities ? support_rate : 0);
            const std::array<std::array<cambc::item_type, 3>, 4> families{{
                {cambc::item_type::monster_shard_of_strength, cambc::item_type::monster_shard_of_focus, cambc::item_type::monster_shard_of_health},
                {cambc::item_type::jungle_shard_of_strength, cambc::item_type::jungle_shard_of_focus, cambc::item_type::jungle_shard_of_health},
                {cambc::item_type::durability_shard_of_strength, cambc::item_type::durability_shard_of_focus, cambc::item_type::durability_shard_of_health},
                {cambc::item_type::power_shard_of_strength, cambc::item_type::power_shard_of_focus, cambc::item_type::power_shard_of_health}}};
            pending_ = families[std::min(sets, 3u)][stat];
        }
        const auto cost = pending_.cost();
        const unsigned count = std::min(5 - partial_, me.gold_count() / std::max(1u, cost));
        if (!count || !me.can_buy(pending_, count)) return;
        me.buy(pending_, count);
        shards += count;
        partial_ += count;
        if (partial_ == 5) { ++sets; partial_ = 0; }
    }
}
}
