#ifndef PPU_MEMORY_H
#define PPU_MEMORY_H

#include <stdint.h>
#include <stdio.h>
#include <exception>
#include <stdexcept>
#include "Constants.h"

#ifdef PPU_ADDRESS_CACHING
#include <unordered_map>
#endif

class PPUMemory {
private:
#ifdef PPU_ADDRESS_CACHING
    std::unordered_map<uint16_t, uint16_t> _address_cache;
#endif

public:
    uint8_t ppu_memory[0x4000] = { 0 };
    NametableMirroring nametable_mirroring = NametableMirroring::NONE;

private:
    uint16_t _run_address_preprocessors(uint16_t address);
    inline uint16_t _resolve_address(uint16_t address) {
// Cheaper to just run the code than use a cache,
// because of how slow C++ containers are.
#ifdef PPU_ADDRESS_CACHING
        if (_address_cache.find(address) != _address_cache.end()) {
            return _address_cache[address];
        }
#endif
        return _run_address_preprocessors(address);
    }

public:
    inline uint8_t read_one(uint16_t at_address) {
        // TODO
        // Add caching back in if necessary.
        at_address = _resolve_address(at_address);
        return ppu_memory[at_address];
    }

    inline uint32_t background_palette(uint8_t index) {
        /*
         * Returns a background palette for a given index. There are four
         * colours in each palette.
         */
        // Background palette is 4 bytes so uint32_t is enough to hold
        // all bytes in the palette.
        if (!(0 <= index && index <= 3)) {
            // FIXME
            // Raise exception
            printf("Background palettes are indexed 0-3, got %x\n", index);
        }
        uint32_t palette = 0;
        uint8_t* p_palette = (uint8_t*)&palette;

        // Palettes are at 4 byte intervals.
        uint16_t start = 0x3f00 + index * 0x4;

        for (int i = 0; i < 4; i++) {
            p_palette[i] = ppu_memory[start + i];
        }

        // First byte in the palette must always be the
        // universal background byte, that's why it's overwritten
        // here.
        p_palette[0] = ppu_memory[0x3f00];
        return palette;
    }

    inline uint32_t sprite_palette(uint8_t index) {
        /*
         * Returns a sprite palette for a given index. There are four
         * colours in each palette.
         */

        // Make sure to shift 0 -> 3 to 4 -> 7.
        index += 0x4;
        if (!(4 <= index && index <= 7)) {
            printf("Sprite palettes are indexed 4-7, got %x\n", index);
            std::throw_with_nested(
                std::runtime_error("Sprite palette index out of range.\n")
            );
        }

        uint32_t palette = 0;
        uint8_t* p_palette = (uint8_t*)&palette;

        // Palettes are at 4 byte intervals. Sprite palettes start
        // at 0x3f10 but since the indices start at 0x4 that means
        // we'll get to 0x3f10 because 0x4 * 0x4 (first index) is
        // 0x10, and 0x3f00 + 0x10 is 0x3f10.
        uint16_t start = 0x3f00 + index * 0x4;

        for (int i = 0; i < 4; i++) {
            p_palette[i] = ppu_memory[start + i];
        }

        // TODO
        // Confirm
        // First byte in the palette must always be the
        // universal background byte, that's why it's overwritten
        // here.
        p_palette[0] = ppu_memory[0x3f00];
        return palette;
    }

    inline void write(uint8_t what, uint16_t at_address) {
        at_address = _resolve_address(at_address);
        ppu_memory[at_address] = what;
    }

    void write_ppu_memory(uint16_t at_address, uint16_t amount, uint8_t* in_buffer);
};

#endif
