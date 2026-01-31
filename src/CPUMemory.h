#ifndef CPU_MEMORY_H
#define CPU_MEMORY_H

#include <stdint.h>

// TODO
// Update to handle mirroring in various parts of the
// non-PPU address space:
// https://wiki.nesdev.com/w/index.php/CPU_memory_map
// Probably treat this like virtual memory access that knows
// how to do the mapping.

class CPUMemory {
public:
    uint8_t cpu_memory[0x10000] = { 0 };

private:
    void _debug_read_using_disk_addr(uint16_t at_address);

public:
    // TODO
    // Consider inlining if the compiler doesn't do it.
    inline uint8_t read_one(uint16_t at_address) {
        return cpu_memory[at_address];
    }
    uint16_t read_two(uint16_t at_address);
    uint8_t read_from_zero_page_uint8(uint16_t at_address);
    uint16_t read_from_zero_page_uint16(uint16_t at_address);
    void read(uint16_t at_address, uint16_t amount, uint8_t* out_buffer);
    void write(uint8_t what, uint16_t at_address);
    void write_cpu_memory(uint16_t at_address, uint16_t amount, uint8_t* in_buffer);
};

#endif
