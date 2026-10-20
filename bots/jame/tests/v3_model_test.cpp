#include "../v3/src/combat_model.h"
#include "../v3/src/economy.h"
#include <cassert>

int main() {
    using namespace jame;
    const auto crystals = estimate_clear({{500, 0}, {500, 0}}, 100, 0);
    assert(crystals.cleared && crystals.damage_taken == 0 && crystals.rounds == 10);
    const auto wolf = estimate_clear({{300, 20}}, 100, 0);
    assert(wolf.cleared && wolf.rounds == 3 && wolf.damage_taken == 40);
    const auto burst = estimate_clear({{300, 20}}, 100, 200);
    assert(burst.cleared && burst.rounds == 1 && burst.damage_taken == 0);
    const auto pack = estimate_clear({{300, 20}, {300, 20}}, 100, 0);
    assert(pack.cleared && pack.damage_taken > wolf.damage_taken);
    // Nonattacking clusters must not delay removal of an attacking monster.
    const auto mixed = estimate_clear({{500, 0}, {300, 20}}, 100, 0);
    assert(mixed.cleared && mixed.damage_taken == wolf.damage_taken);
    const auto mitigated = estimate_clear({{300, 20}}, 100, 0, .7f);
    assert(mitigated.damage_taken == 28);
    assert(!estimate_clear({{20000, 200}}, 50, 0).cleared);
    assert(!estimate_clear({{300, 20}}, 0, 0).cleared);
    assert(estimate_clear({}, 0, 0).cleared);
    assert(clear_priority(300, 20) < clear_priority(10, 0));

    // Attack-only kits cannot benefit from Focus. A supported spellcaster can.
    assert(choose_stat(50, 100, 1200, 5, 10, 100, 0, 0) == 0);
    assert(choose_stat(100, 100, 3000, 2, 25, 50, 0, .5f) == 1);
    assert(choose_stat(300, 100, 700, 3, 5, 100, 0, 0) == 2);
    // Ryth's health-to-strength passive changes the marginal purchase value.
    assert(choose_stat(50, 100, 1200, 5, 10, 100, .125f, .125f, .01f) == 2);
}
