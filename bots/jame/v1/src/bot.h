#pragma once

#include <cambc.h>
#include <vector>

namespace jame {
class Bot {
public:
    const char* turn();

private:
    struct Group {
        cambc::map::camp_group view;
        cambc::bitboard tiles;
    };

    bool initialized_ = false;
    bool recovering_ = false;
    std::vector<Group> groups_;

    void initialize();
    bool attack_enemy() const;
    bool attack_camp() const;
    bool recall_is_clear() const;
    const char* bank() const;
    const char* farm() const;
};
}
