#include <cambc.h>
#include "draft.h"
#include "draft_table.h"
#include <algorithm>
#include <cstdint>
#include <vector>

namespace {

using cambc::champion_draft;

// Experiments run with --fuel 100000 + 10000*seed (see tools/draft_lab.py). The real server uses 100000,
// so seed 0 means "play for real". The first draft turn gets 10x fuel.
int experiment_seed() {
    const bool first_turn = cambc::draft::current_draft(cambc::team::ally).empty();
    const double quantum = static_cast<double>(cambc::fuel_remaining()) / (first_turn ? 10 : 1);
    return static_cast<int>((quantum - 100000) / 10000 + 0.5);
}

std::uint32_t mix(std::uint32_t x) {
    x ^= x >> 16; x *= 0x7feb352dU; x ^= x >> 15; x *= 0x846ca68bU; x ^= x >> 16;
    return x;
}

bool taken(const std::vector<champion_draft>& picks, int c) {
    return std::find(picks.begin(), picks.end(), static_cast<champion_draft>(c)) != picks.end();
}

} // namespace

void play_draft() {
    const auto mine = cambc::draft::current_draft(cambc::team::ally);
    static int seed = experiment_seed(); // measured once, on the first turn

    if (seed > 0) {
        // Random roster per (seed, side, pick) so experiments cover many compositions.
        const auto spawn = cambc::map::spawn_region(cambc::team::ally).positions()[0];
        std::uint32_t h = mix(seed * 2654435761U ^ (spawn.x * 73856093U) ^ (spawn.y * 19349663U));
        std::vector<int> open;
        for (int c = 0; c < kChampionCount; ++c) if (!taken(mine, c)) open.push_back(c);
        cambc::draft::pick(static_cast<champion_draft>(open[mix(h + static_cast<std::uint32_t>(mine.size())) % open.size()]));
        return;
    }

    // Opponents cannot deny picks (both teams may take the same champion), so draft is composition:
    // take the highest-valued champion for this team size that we do not have yet.
    const int size = static_cast<int>(cambc::draft::team_size());
    const int bucket = std::clamp(size - 3, 0, 2);
    int best = -1;
    for (int c = 0; c < kChampionCount; ++c)
        if (!taken(mine, c) && (best < 0 || kDraftValue[bucket][c] > kDraftValue[bucket][best])) best = c;
    cambc::draft::pick(static_cast<champion_draft>(best));
}
