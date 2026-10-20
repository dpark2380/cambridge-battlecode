#pragma once

#include <cambc.h>
#include <vector>
#include "progress.h"

namespace jame {
class Bot {
public:
    const char* turn();
    void print_metrics() const;

private:
    struct Group {
        cambc::map::camp_group view;
        cambc::bitboard tiles;
        std::vector<cambc::camp_stats> designs;
        int retry_round = 0;
    };

    bool initialized_ = false;
    bool recovering_ = false;
    bool needs_rest_ = false;
    bool planning_ = false;
    unsigned planning_cursor_ = 0;
    float nearby_damage_ = 0;
    std::vector<Group> groups_;
    float camp_damage_multiplier_ = 1;
    int target_ = -1;
    Progress progress_;
    std::optional<cambc::distance_field> route_;
    struct Metrics {
        unsigned travel = 0, attacks = 0, capture = 0, banking = 0;
        unsigned recovery = 0, combat = 0, idle = 0, stalled = 0;
        unsigned dead = 0, disabled = 0, channels = 0, respawns = 0, reselections = 0;
        unsigned planning = 0, blocked = 0, camp_respawns = 0, contested = 0;
        unsigned captures = 0, banked = 0, deaths = 0;
        int first_capture = -1, first_bank = -1;
    } metrics_;
    bool moved_ = false, attacked_ = false, combat_ = false;
    bool sampled_ = false, was_alive_ = false, was_submitting_ = false;
    int capture_group_ = -1;
    unsigned previous_gems_ = 0;
    void sample_progress();
    const char* decide();
    void clear_target();
    cambc::bitboard goals_for(int index) const;
    float remaining_health(int index) const;
    bool plausible_clear(int index) const;
    bool select_target();

    void initialize();
    bool attack_enemy();
    bool attack_camp();
    bool recall_is_clear() const;
    const char* bank();
    const char* farm();
    const char* recover();
};
}
