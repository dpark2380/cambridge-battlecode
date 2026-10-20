#pragma once

#include <cambc.h>

namespace jame {
// A mechanical shortest-path step to any free goal, using native SDK searches.
bool walk_to(cambc::bitboard goals);
}
