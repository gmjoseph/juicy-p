#include "Clock.h"
#include "Constants.h"
#include "PPU.h"

void
Clock::cpu_cycle(uint8_t next_cycles) {
    // Use the clock to drive PPU ticks.
    cpu_cycles += next_cycles;
    for (int i = 0; i < next_cycles * PPUCyclesPerCPUCycle; i++) {
        // TODO
        // Force tests to also create a PPU so this check isn't necessary.
        if (ppu != nullptr) {
            ppu->next();
        }
    }
}
