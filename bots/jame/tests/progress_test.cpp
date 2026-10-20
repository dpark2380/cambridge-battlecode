#include "../v2/src/progress.h"
#include <cassert>

int main() {
    jame::Progress travel;
    assert(!travel.observe(20, 1350));
    for (int d = 19; d >= 0; --d)
        assert(!travel.observe(d, 1350));

    // Bouncing between equally unproductive positions must eventually expire.
    jame::Progress bouncing;
    assert(!bouncing.observe(4, 1350));
    for (int i = 1; i < 12; ++i)
        assert(!bouncing.observe(i % 2 ? 5 : 4, 1350));
    assert(bouncing.observe(4, 1350));

    // Stationary attacks that actually reduce health are productive.
    jame::Progress fighting;
    for (int hp = 1350; hp >= 0; hp -= 25)
        assert(!fighting.observe(0, hp));
    for (int i = 0; i < 11; ++i)
        assert(!fighting.observe(0, 0));
    assert(fighting.observe(0, 0));

    // Useful damage resets an accumulated stall, and a new objective resets all history.
    jame::Progress resetting;
    resetting.observe(5, 100);
    for (int i = 0; i < 10; ++i)
        resetting.observe(5, 100);
    assert(!resetting.observe(5, 90));
    assert(resetting.stalled == 0);
    resetting = {};
    assert(!resetting.observe(50, 20000));
}
