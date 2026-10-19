#pragma once

namespace jame {
// Fixed release settings. Local ablations change one switch in isolated copies.
inline constexpr bool use_abilities = true;
inline constexpr bool buy_equipment = true;
// The stricter group model reduced scoring in all-map ablations. Keep it as an
// explicit experiment; the release retains the simpler camp admission screen.
inline constexpr bool estimate_survival = false;
inline constexpr bool commit_targets = true;
inline constexpr bool prefer_gems = true;
}
