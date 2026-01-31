#ifndef PPU_H
#define PPU_H

#include <stdint.h>
#include "Clock.h"
#include "CPUMemory.h"
#include "Stack.h"
#include "OAM.h"
#include "Opcodes.h"
#include "PPUMemory.h"
#include "Renderer.h"

struct PPUState {
    uint8_t nametable_byte;
    uint8_t attribute_table_byte;
    uint8_t pattern_table_low_byte;
    uint8_t pattern_table_high_byte;
    uint32_t palette;
};

// IO_DB imports PPU.h in its header.
class IO_DB;

class PPU {

private:
    // OAMDATA, PPUDATA, and OAMDMA are missing because they're just proxies
    // for memory read/write at specific places.
    uint8_t _PPUCTRL = 0x0;
    uint8_t _PPUMASK = 0x0;
    uint8_t _PPUSTATUS = 0x0;
    uint8_t _OAMADDR = 0x0;
    uint16_t _PPUSCROLL = 0x0;
    uint16_t _PPUADDR = 0x0;
    uint8_t _PPUADDR_pushes = 0x0;
    uint8_t _PPUSCROLL_pushes = 0x0;

    // Fine x scroll for the pixel x, y
    uint16_t _x = 0x0;
    // Fine y scroll for the pixel x, y
    uint16_t _y = 0x0;

public:
    PPUMemory memory = PPUMemory();
    Renderer renderer = Renderer();
    Clock& clock;
    IO_DB& bus;
    OAM& oam;
    PPUState background_state;
    uint16_t scanline = 0;
    uint64_t frames = 0;
    uint8_t pixels[256 * 240] = { 0 };

private:
    uint8_t _receive_bus_data();
    void _cycle();
    void _update_state();
    void _maybe_compute_pixel();
    void _post_cycle();

public:
    PPU(IO_DB& bus, Clock& clock, OAM& oam);

    inline uint8_t PPUCTRL() { return _PPUCTRL; };
    inline void set_PPUCTRL(uint8_t what) { _PPUCTRL = what; };
    inline uint16_t base_nametable_address() {
        uint8_t index = _PPUCTRL & 0x3;
        switch (index) {
            case 0: return 0x2000;
            case 1: return 0x2400;
            case 2: return 0x2800;
            case 3: return 0x2c00;
            // This is impossible because & 0x3 will always produce
            // a valid case.
            default: return 0xffff;
        }
    }
    inline uint8_t increment_mode() { return _PPUCTRL & 0x4; }
    inline uint16_t sprite_pattern_table_start() {
        // Note: Background uses 0x10
        return (_PPUCTRL & 0x8) ? 0x1000 : 0x0;
    }
    inline uint16_t background_pattern_table_start() {
        // Note: Sprites uses 0x8
        return (_PPUCTRL & 0x10) ? 0x1000 : 0x0;
    }
    inline bool generated_nmi() {
        // Only returns true if the current cycle is the beginning
        // of VBLANK and _generate_nmi is true.
        bool first_cycle = clock.ppu_cycles == 1;
        bool correct_scanline = scanline == PPUVBlankScanline;
        // Generate an NMI at the start of the
        // vertical blanking interval (0: off; 1: on)
        bool generate_nmi = _PPUCTRL & 0x80;
        return generate_nmi && correct_scanline && first_cycle;
    }

    inline uint8_t PPUMASK() {
        return _PPUMASK;
    }
    inline void set_PPUMASK(uint8_t what) { _PPUMASK = what; }

    inline uint8_t PPUSTATUS() {
        // "This register reflects the state of various functions inside the
        // PPU. It is often used for determining timing. To determine when
        // the PPU has reached a given pixel of the screen, put an opaque
        // (non-transparent) pixel of sprite 0 there."
        // Whenever this is read we have to clear bit 7 
        uint8_t previous = _PPUSTATUS;
        _PPUSTATUS &= 0x7f;
        return previous;
    }

    inline uint16_t PPUADDR() { return _PPUADDR; }
    void set_PPUADDR(uint8_t what);

    inline uint16_t PPUSCROLL() { return _PPUSCROLL; }
    void set_PPUSCROLL(uint8_t what);
    // FIXME
    // This might not be the high byte?
    inline uint8_t scroll_x() { return _PPUSCROLL >> 8; }
    // FIXME
    // This might not be the low byte
    inline uint8_t scroll_y() { return _PPUSCROLL & 0xff; }

    inline uint8_t x() { return _x; }
    inline uint8_t y() { return _y; }

    uint8_t send_data_to_bus(PPURegister from_register);
    void receive_data_from_bus(uint8_t data, PPURegister to_register);
    void next();

    inline bool rendering() {
        /*
         * Rendering happens for now between scanline 0 and 241 and cycles 1
         * and 256. This _MAY_ be accurate in terms of outputing pixels to
         * the screen, but it isn't in terms of computing the next frame's
         * pixels up front.
         */
        // FIXME
        // Copied and pasted this from maybe compute pixel.
        if (scanline >= 240) {
            return false;
        }
        if (1 > clock.ppu_cycles || clock.ppu_cycles > 256) {
            return false;
        }
        return true;
    }
};

#endif
