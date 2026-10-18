#pragma once

#include <limits>

namespace jame {
// Count only turns spent working on this objective. Combat, recovery, channels,
// death and capture waits do not consume its travel/attack patience.
struct Progress {
    int distance = std::numeric_limits<int>::max();
    float health = std::numeric_limits<float>::max();
    int stalled = 0;

    bool observe(int next_distance, float next_health) {
        if (next_distance < distance || next_health < health - 0.01f)
            stalled = 0;
        else
            ++stalled;
        distance = next_distance < distance ? next_distance : distance;
        health = next_health < health ? next_health : health;
        return stalled >= 12;
    }
};
}
