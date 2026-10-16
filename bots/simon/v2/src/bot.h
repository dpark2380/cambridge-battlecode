#pragma once
#include <cambc.h>
#include <optional>
#include "plan.h"
#include "world.h"

// Per-champion state survives between turns.
// Strategy v2: the gem duo greedily captures gem camps and fights for them; the gold squad farms
// gold, monsters before gold clusters. Both tribute any gems they carry.
class Bot {
    std::optional<draft_plan> plan;  // from draft memory; nullopt if the draft wrote none
    role squad = role::gold_squad;
    int squad_bodies = 1;            // champions sharing our role, for kill-time estimates
    world camps;
    bool initialised = false;
    bool moved = false;              // this turn: blocks casts that exclude walking
    int waiting_for = -1, waited = 0;  // group we are holding off from until squad-mates arrive

    void init();
    void shop();
    bool fight_enemies();
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
