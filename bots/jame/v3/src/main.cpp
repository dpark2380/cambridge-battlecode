#include "bot.h"
#include "draft.h"

#include <algorithm>
#include <cambc.h>
#include <cstdint>
#include <exception>
#include <iostream>
#include <limits>

int main() {
    jame::Bot bot;
    auto minimum_fuel = std::numeric_limits<std::uint64_t>::max();
    while (true) {
        try {
            if (cambc::is_draft()) {
                jame::draft_turn();
            } else {
                const auto started_round = cambc::round_number();
                const char* action = bot.turn();
                const auto ended_round = cambc::round_number();
                const auto fuel = cambc::fuel_remaining();
                minimum_fuel = std::min(minimum_fuel, fuel);
                if (started_round != ended_round)
                    std::cout << "jame/v3 turn-overrun " << started_round << "->" << ended_round
                              << " action=" << action << '\n';
                if (started_round <= 3 || started_round % 50 == 0) {
                    std::cout << "jame/v3 round=" << ended_round
                              << " champion=" << cambc::to_string(cambc::self().champion_name())
                              << " action=" << action << " fuel=" << fuel
                              << " min-fuel=" << minimum_fuel << '\n';
                    bot.print_metrics();
                }
            }
        } catch (const std::exception& error) {
            std::cout << "jame/v3 error: " << error.what() << '\n';
        } catch (...) {
            std::cout << "jame/v3 error: unknown exception\n";
        }
        // SDK flushing/yielding is the only shared runtime pattern taken from
        // the official template. Gameplay is independent of teammate bots.
        cambc::end_turn();
    }
}
