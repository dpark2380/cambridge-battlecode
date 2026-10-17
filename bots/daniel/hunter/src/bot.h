#pragma once
#include <cambc.h>
#include <optional>
#include "plan.h"
#include "world.h"

// Our own figures for target estimates, measured once per turn.
struct self_estimate {
    float damage = 50, health = 900;
};

// Per-champion state survives between turns.
// Strategy v4 (see bots/docs/v4): every body farms its own best group and claims it in shared
// memory; bodies share a group when it needs them or beats their other options. Everyone tributes
// the gems they carry.
class Bot {
    std::optional<draft_plan> plan;  // from draft memory; nullopt if the draft wrote none
    role squad = role::gold_squad;   // the draft's role: now only steers fighting and shopping
    int slot = 0;                    // our claim slot in shared memory
    int team_bodies = 3;             // bodies on our team (Cassi and Issac count as two)
    world camps;
    self_estimate own;
    bool initialised = false;
    bool moved = false;              // this turn: blocks casts that exclude walking
    int waiting_for = -1, waited = 0;  // group we are holding off from until help arrives
    int current_target = -1, target_round = -1;  // chosen group, and the round it was chosen
    int claim = -1;                  // group we hold this turn, published at its end
    int published_claim = -2, published_round = -1000;
    bool banking = false;            // committed to tributing what we carry
    cambc::distance_field altar_walk;  // walking distance to the nearest tribute tile
    // Progress watchdog on the current target (see watch_progress).
    int progress_target = -1, progress_round = -1, best_distance = 0, stalled = 0;
    bool hit_target = false;

    void init();
    void take_turn(int round);
    void publish_claim(int round);
    void watch_progress(int round);
    void shop();
    bool place_lock();
    bool fight_enemies(int round);
    bool should_tribute(int round);
    void go_tribute();
    bool shop_trip();
    int choose_target(int round);
    void work_group(int index, int round);
    void retreat();

    // Movement and combat helpers that track `moved`.
    bool move_towards_closest(cambc::bitboard goals);
    template <class Target> bool strike(const Target& target);
    template <class Target> void cast_offense(const Target& target);
    void cast_support();

public:
    void play_turn();
};
