#pragma once
// Tunable constants. tools/tune.py rewrites this file in candidate copies; keep one `P(name, value)` per line.
#define PARAMS(P) \
    P(RECALL_HP, 0.1791f)        /* recall below this health fraction when away from spawn */ \
    P(GEM_RISK, 0.1092f)          /* recall threshold rises by this per 100 carried gems */ \
    P(ESCAPE_TURNS, 3.8405f)      /* retreat when current damage intake would kill us within this many turns */ \
    P(TRIBUTE_GEMS, 22.8025f)     /* walk to an altar once carrying this many gems */ \
    P(TRIBUTE_NEAR, 8.7448f)      /* tribute any gems when an altar is this close */ \
    P(W_GOLD, 0.0540f)           /* gold value relative to one gem when scoring camps */ \
    P(CAMP_SAFETY, 0.6251f)       /* fraction of current health we accept losing to a camp */ \
    P(RECALL_TRIP, 25.2703f)      /* turns lost per full health bar of extra camp damage, besides walking */ \
    P(TRAVEL_W, 1.5382f)          /* weight of travel turns in camp time cost */ \
    P(FIGHT_RATIO, 1.0184f)       /* attack enemy champions when my hp*str beats theirs by this */ \
    P(STAT_HEALTH_EVERY, 1.6524f) /* every Nth shard is health, the rest strength/focus */

inline constexpr unsigned FIELD_RESERVE = 20000; // keep this much fuel when building fields (each costs ~1-4k)
#define DECLARE_PARAM(name, value) inline constexpr float name = value;
PARAMS(DECLARE_PARAM)
#undef DECLARE_PARAM
