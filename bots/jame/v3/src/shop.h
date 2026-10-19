#pragma once
#include <cambc.h>
namespace jame {
class Shop {
public:
    unsigned shards = 0, sets = 0;
    void visit();
private:
    unsigned partial_ = 0;
    cambc::item_type pending_ = cambc::item_type::monster_shard_of_strength;
};
}
