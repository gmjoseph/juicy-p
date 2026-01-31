#ifndef CLOCK_H
#define CLOCK_H

#include <stdint.h>

class PPU;

class Clock {
public:
    PPU* ppu = nullptr;
    // Tracks the cycles for the CPU and PPU
    uint64_t cpu_cycles = 0x7;
    uint64_t ppu_cycles = 0x0;

public:
    // TODO
    // Would be nice to inline but can't because of circular import
    // between PPU and Clock.
    void cpu_cycle(uint8_t cycles);
};

#endif
