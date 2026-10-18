#pragma once
#include <cambc.h>

namespace jame {
class Actions {
public:
    unsigned attacks = 0, casts = 0, resets = 0, damage_casts = 0, support_casts = 0;
    void begin_turn() { used_basic_ = false; }
    bool engage(const cambc::camp& target, bool moved);
    bool engage(const cambc::champion& target, bool moved);
    bool support(bool moved);
    float reach() const;
    void remember_threat(cambc::camp camp, int range) { threats_.push_back({camp, range}); }
private:
    struct Threat { cambc::camp camp; int range; };
    std::vector<Threat> threats_;
    bool used_basic_ = false;
    template<class Target> bool fight(const Target& target, bool moved);
};
}
