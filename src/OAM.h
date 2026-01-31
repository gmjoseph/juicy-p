#ifndef OAM_H
#define OAM_H

#include <exception>
#include <stdexcept>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

class OAM {
    // OAM: Object attribute memory. Holds 64 sprites of 1 byte
    // each that were uploaded using OAMDMA or OAMDATA (more
    // commonly the former than the latter)

public:
    uint8_t memory[0x100] = { 0 };

public:
    inline uint32_t sprite_at_index(uint8_t index) {
        // Reads one sprite.
        if (index >= 0x40) {
            printf("Out of range sprite index: %d\n", index);
            std::throw_with_nested(
                std::runtime_error("Sprite index out of range (0-63).\n")
            );
        }
        // TODO
        // Maybe return this data in a structured form rather than bytes?
        uint16_t address = index * 0x4;
        return *((uint32_t*)(&memory[address]));
    }

    inline void write(uint8_t what, uint16_t at_address) {
        // Supports writing one byte of data at a time to an absolute
        // address.
        memory[at_address] = what;
    }

    inline void upload_data(uint8_t* in_buffer) {
        // Writes all sprites (256 bytes) at once.
        // FIXME
        // May need to change the copying strategy here.
        memcpy(memory, in_buffer, 0x100);
    }

    // TODO
    // https://wiki.nesdev.com/w/index.php/PPU_sprite_evaluation
    // This involves determining which sprites are in the frame
    // range and then drawing them.
    // For now i'll just grab the first 8 and draw them from
    // the top left.
};

#endif
