#pragma once
// Tunable constants. tools/tune.py rewrites this file in candidate copies; keep one `P(name, value)` per line.
#define PARAMS(P) \
    P(RECALL_HP, 0.35f)        /* recall below this health fraction when away from spawn */ \
    P(RECALL_HP_GEMS, 0.5f)    /* ...or below this when carrying at least TRIBUTE_GEMS */ \
    P(TRIBUTE_GEMS, 60.0f)     /* walk to an altar once carrying this many gems */ \
    P(TRIBUTE_NEAR, 6.0f)      /* tribute any gems when an altar is this close */ \
    P(W_GOLD, 0.25f)           /* gold value relative to one gem when scoring camps */ \
    P(CAMP_SAFETY, 0.8f)       /* fraction of current health we accept losing to a camp */ \
    P(RECALL_TRIP, 15.0f)      /* turns lost per full health bar of extra camp damage, besides walking */ \
    P(TRAVEL_W, 1.0f)          /* weight of travel turns in camp time cost */ \
    P(FIGHT_RATIO, 1.0f)       /* attack enemy champions when my hp*str beats theirs by this */ \
    P(STAT_HEALTH_EVERY, 3.0f) /* every Nth shard is health, the rest strength/focus */

inline constexpr unsigned FIELD_RESERVE = 50000; // keep this much fuel when building fields (fields cost ~40k; more on big maps)
#define DECLARE_PARAM(name, value) inline constexpr float name = value;
PARAMS(DECLARE_PARAM)
#undef DECLARE_PARAM
