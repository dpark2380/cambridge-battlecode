#include "draft.h"

#include <algorithm>
#include <cambc.h>
#include <iostream>

namespace jame {
void draft_turn() {
    // SDK order is a reproducible baseline, not a champion ranking.
    const auto picked = cambc::draft::current_draft(cambc::team::ally);
    for (int value = 0; value <= static_cast<int>(cambc::champion_draft::tavi); ++value) {
        const auto candidate = static_cast<cambc::champion_draft>(value);
        if (std::find(picked.begin(), picked.end(), candidate) != picked.end())
            continue;
        std::cout << "jame/v2 draft pick=" << value << '\n';
        cambc::draft::pick(candidate);
        return;
    }
}
}
