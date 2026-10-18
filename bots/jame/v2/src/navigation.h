#pragma once

#include <cambc.h>

namespace jame {
cambc::bitboard movement_blockers();
// A mechanical shortest-path step to any free goal, using native SDK searches.
bool walk_to(cambc::bitboard goals, const cambc::distance_field* prepared = nullptr);
}
