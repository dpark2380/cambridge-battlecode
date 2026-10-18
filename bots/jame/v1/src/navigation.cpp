#include "navigation.h"

namespace jame {
bool walk_to(cambc::bitboard goals) {
    const auto& me = cambc::self();
    if (!me.can_move())
        return false;

    const auto origin = me.position();
    if (goals.is_set(origin))
        return false;

    auto blocked = cambc::map::walls() | cambc::map::holes() | cambc::map::altars()
        | cambc::map::spawn_region(cambc::team::enemy)
        | cambc::vision::champion_tiles() | cambc::vision::camp_tiles()
        | cambc::vision::teleport_tiles();
    blocked.set(origin, false);

    cambc::bitboard destination;
    destination.set(origin);
    cambc::distance_field field;
    // At most eight adjacent obstructions can be discovered in one turn.
    for (int attempt = 0; attempt < 8; ++attempt) {
        goals &= ~blocked;
        if (goals.is_empty())
            return false;
        cambc::bitboard visited;
        field.compute_to(blocked, goals, destination, visited);
        if (field.get(origin) == cambc::distance_field::unreachable)
            return false;

        const auto legal = blocked.reachable_tiles(origin, 1);
        bool discovered_obstruction = false;
        for (const auto delta : field.next_moves_from(origin)) {
            const auto next = origin + delta;
            if (!legal.is_set(next))
                continue;
            if (me.move_absolute(next))
                return true;
            // A hidden occupant was revealed; failed movement costs no allowance.
            blocked.set(next);
            discovered_obstruction = true;
            break;
        }
        if (!discovered_obstruction)
            return false;
    }
    return false;
}
}
