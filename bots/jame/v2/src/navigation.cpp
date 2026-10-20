#include "navigation.h"

namespace jame {
cambc::bitboard movement_blockers() {
    auto blocked = cambc::map::walls() | cambc::map::holes() | cambc::map::altars()
        | cambc::map::spawn_region(cambc::team::enemy)
        | cambc::vision::champion_tiles() | cambc::vision::camp_tiles()
        | cambc::vision::teleport_tiles();
    blocked.set(cambc::self().position(), false);
    return blocked;
}

bool walk_to(cambc::bitboard goals, const cambc::distance_field* prepared) {
    const auto& me = cambc::self();
    if (!me.can_move())
        return false;

    const auto origin = me.position();
    if (goals.is_set(origin))
        return false;

    auto blocked = movement_blockers();

    cambc::bitboard destination;
    destination.set(origin);
    cambc::distance_field field;
    // At most eight adjacent obstructions can be discovered in one turn.
    for (int attempt = 0; attempt < 8; ++attempt) {
        // A retry can involve another full-map native search. Yield and use the
        // newly revealed occupancy next turn rather than suspending mid-action.
        if (cambc::fuel_remaining() < (attempt == 0 && prepared ? 12000 : 35000))
            return false;
        goals &= ~blocked;
        if (goals.is_empty())
            return false;
        const cambc::distance_field* route = prepared;
        if (attempt > 0 || !route) {
            cambc::bitboard visited;
            field.compute_to(blocked, goals, destination, visited);
            route = &field;
        }
        if (route->get(origin) == cambc::distance_field::unreachable)
            return false;

        const auto legal = blocked.reachable_tiles(origin, 1);
        bool discovered_obstruction = false;
        for (const auto delta : route->next_moves_from(origin)) {
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
