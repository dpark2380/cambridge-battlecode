#pragma once
#include <cambc.h>
#include <cstdint>
#include <vector>

// Per-champion state survives between turns.
class Bot {
    bool initialised = false;
    int slot = 0;                                 // index among allied champions; owns shared_memory[slot]
    std::vector<cambc::map::camp_group> groups;   // fixed order; index is the claim id
    struct GroupInfo { cambc::bitboard tiles; std::vector<cambc::vec2> positions; float health, strength, value; };
    std::vector<GroupInfo> info;                  // static per-group facts, cached once (host calls cost fuel)
    cambc::bitboard visible;                      // this turn's vision
    std::vector<int> respawn_round;               // last known round each group respawns (0 = alive/unknown)
    std::vector<cambc::distance_field> fields;    // static walking distance to each group's tiles, lazily built
    std::vector<bool> field_ready;
    cambc::distance_field altar_field;
    cambc::bitboard terrain;                      // walls, holes, altars and the enemy spawn
    int target = -1;
    unsigned shards_bought = 0;

    void init();
    const cambc::distance_field& group_field(int g);
    float travel_to(int g);
    void build_fields(std::uint64_t reserve);
    void act();
    bool step_along(const cambc::distance_field& field, bool allow_dash);
    void observe_groups();
    int choose_group();
    void claim(int g);
    void buy_items();
    bool fight_enemies();
    bool cast_on(const cambc::unit* target, bool champion_target);
    bool attack_target(const cambc::unit& target, bool champion_target);
    bool farm();
    bool tribute();

public:
    void play_turn();
};
