#include <tuple>
#include <vector>
#include <assert.h>
#include "Constants.h"
#include "Clock.h"
#include "IO_DB.h"
#include "OAM.h"
#include "PPU.h"
#include "PPUUtils.h"

void
test_resolve_register() {
    /*
     * Since the PPU registers are memory mapped and mirrored, we
     * should be able to get the right register for an address even
     * if it's a mirrored one.
     */
    std::vector<std::tuple<uint16_t, PPURegister>> cases = {
        std::make_tuple(0x0, PPURegister::NONE),
        std::make_tuple(0x4000, PPURegister::NONE),
        std::make_tuple(0x8000, PPURegister::NONE),
        // Test literals
        std::make_tuple(0x2000, PPURegister::PPUCTRL),
        std::make_tuple(0x2001, PPURegister::PPUMASK),
        std::make_tuple(0x2002, PPURegister::PPUSTATUS),
        std::make_tuple(0x2003, PPURegister::OAMADDR),
        std::make_tuple(0x2004, PPURegister::OAMDATA),
        std::make_tuple(0x2005, PPURegister::PPUSCROLL),
        std::make_tuple(0x2006, PPURegister::PPUADDR),
        std::make_tuple(0x2007, PPURegister::PPUDATA),
        std::make_tuple(0x4014, PPURegister::OAMDMA),
        // Test that enums and produce the right register.
        std::make_tuple((uint16_t)PPUAddress::PPUCTRL_ADDRESS, PPURegister::PPUCTRL),
        std::make_tuple((uint16_t)PPUAddress::PPUMASK_ADDRESS, PPURegister::PPUMASK),
        std::make_tuple((uint16_t)PPUAddress::PPUSTATUS_ADDRESS, PPURegister::PPUSTATUS),
        std::make_tuple((uint16_t)PPUAddress::OAMADDR_ADDRESS, PPURegister::OAMADDR),
        std::make_tuple((uint16_t)PPUAddress::OAMDATA_ADDRESS, PPURegister::OAMDATA),
        std::make_tuple((uint16_t)PPUAddress::PPUSCROLL_ADDRESS, PPURegister::PPUSCROLL),
        std::make_tuple((uint16_t)PPUAddress::PPUADDR_ADDRESS, PPURegister::PPUADDR),
        std::make_tuple((uint16_t)PPUAddress::PPUDATA_ADDRESS, PPURegister::PPUDATA),
        std::make_tuple((uint16_t)PPUAddress::OAMDMA_ADDRESS, PPURegister::OAMDMA),
        // Test mirroring in the middle of the space.
        std::make_tuple(0x2aa8, PPURegister::PPUCTRL),
        std::make_tuple(0x2aa9, PPURegister::PPUMASK),
        std::make_tuple(0x2aaa, PPURegister::PPUSTATUS),
        std::make_tuple(0x2aab, PPURegister::OAMADDR),
        std::make_tuple(0x2aac, PPURegister::OAMDATA),
        std::make_tuple(0x2aad, PPURegister::PPUSCROLL),
        std::make_tuple(0x2aae, PPURegister::PPUADDR),
        std::make_tuple(0x2aaf, PPURegister::PPUDATA),
        // Test mirroring at the end of the space.
        std::make_tuple(0x3ff8, PPURegister::PPUCTRL),
        std::make_tuple(0x3ff9, PPURegister::PPUMASK),
        std::make_tuple(0x3ffa, PPURegister::PPUSTATUS),
        std::make_tuple(0x3ffb, PPURegister::OAMADDR),
        std::make_tuple(0x3ffc, PPURegister::OAMDATA),
        std::make_tuple(0x3ffd, PPURegister::PPUSCROLL),
        std::make_tuple(0x3ffe, PPURegister::PPUADDR),
        std::make_tuple(0x3fff, PPURegister::PPUDATA),
    };
    for (auto& c : cases) {
        uint16_t address = std::get<0>(c);
        PPURegister expected_register = std::get<1>(c);
        assert(expected_register == resolve_register(address));
    }
}

void
test_maybe_resolve_nametable_address() {
    /*
     * There is a variety of mirroring that happens in name table
     * accesses. This tests that we resolve an address to the
     * mirrored location correctly.
     */

    std::vector<std::tuple<uint16_t, uint16_t, NametableMirroring>> cases = {
        std::make_tuple(0x0, 0x0, NametableMirroring::NONE),
        // Edgecase on the border of nametable_0.
        std::make_tuple(0x1FFF, 0x1FFF, NametableMirroring::NONE),
        // Palette ram index.
        std::make_tuple(0x3F00, 0x3F00, NametableMirroring::NONE),
        // nametable_0
        std::make_tuple(0x2000, 0x2000, NametableMirroring::NONE),
        std::make_tuple(0x2000, 0x2000, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x2000, 0x2000, NametableMirroring::VERTICAL),
        // std::make_tuple(0x2001, 0x2001, NametableMirroring::NONE),
        // std::make_tuple(0x2001, 0x2001, NametableMirroring::HORIZONTAL),
        // std::make_tuple(0x2001, 0x2001, NametableMirroring::VERTICAL),
        std::make_tuple(0x23FF, 0x23FF, NametableMirroring::NONE),
        std::make_tuple(0x23FF, 0x23FF, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x23FF, 0x23FF, NametableMirroring::VERTICAL),
        // nametable_1
        std::make_tuple(0x2400, 0x2400, NametableMirroring::NONE),
        std::make_tuple(0x2400, 0x2000, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x2400, 0x2400, NametableMirroring::VERTICAL),
        std::make_tuple(0x27FF, 0x27FF, NametableMirroring::NONE),
        std::make_tuple(0x27FF, 0x23FF, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x27FF, 0x27FF, NametableMirroring::VERTICAL),
        // nametable_2
        std::make_tuple(0x2800, 0x2800, NametableMirroring::NONE),
        std::make_tuple(0x2800, 0x2800, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x2800, 0x2000, NametableMirroring::VERTICAL),
        std::make_tuple(0x2BFF, 0x2BFF, NametableMirroring::NONE),
        std::make_tuple(0x2BFF, 0x2BFF, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x2BFF, 0x23FF, NametableMirroring::VERTICAL),
        // nametable_3
        std::make_tuple(0x2C00, 0x2C00, NametableMirroring::NONE),
        std::make_tuple(0x2C00, 0x2800, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x2C00, 0x2400, NametableMirroring::VERTICAL),
        std::make_tuple(0x2FFF, 0x2FFF, NametableMirroring::NONE),
        std::make_tuple(0x2FFF, 0x2BFF, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x2FFF, 0x27FF, NametableMirroring::VERTICAL),
        // Nametable mirrors
        std::make_tuple(0x3000, 0x2000, NametableMirroring::NONE),
        std::make_tuple(0x3C00, 0x2800, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x3C00, 0x2400, NametableMirroring::VERTICAL),
        std::make_tuple(0x3EFF, 0x2EFF, NametableMirroring::NONE),
        std::make_tuple(0x3EFF, 0x2AFF, NametableMirroring::HORIZONTAL),
        std::make_tuple(0x3EFF, 0x26FF, NametableMirroring::VERTICAL),
    };
    for (auto& c : cases) {
        int address = std::get<0>(c);
        uint16_t expected_address = std::get<1>(c);
        NametableMirroring mirroring = std::get<2>(c);
        assert(expected_address == maybe_resolve_nametable_address(address, mirroring));
    }
}

void
test_maybe_resolve_palette_address() {
    /*
     * Four addresses are mirrored in the PPU palette.
     */
    std::vector<std::tuple<uint16_t, uint16_t>> cases = {
        std::make_tuple(0x0, 0x0),
        std::make_tuple(0x3F00, 0x3F00),
        std::make_tuple(0x3F04, 0x3F04),
        std::make_tuple(0x3F08, 0x3F08),
        std::make_tuple(0x3F0C, 0x3F0C),
        std::make_tuple(0x3F10, 0x3F00),
        std::make_tuple(0x3F14, 0x3F04),
        std::make_tuple(0x3F18, 0x3F08),
        std::make_tuple(0x3F1C, 0x3F0C),
        // These are all palette ram mirrors.
        std::make_tuple(0x3F00, 0x3F00),
        std::make_tuple(0x3F20, 0x3F00),
        std::make_tuple(0x3F01, 0x3F01),
        std::make_tuple(0x3F21, 0x3F01),
        std::make_tuple(0x3F0A, 0x3F0A),
        std::make_tuple(0x3FEA, 0x3F0A),
        std::make_tuple(0x3F3F, 0x3F1F),
        std::make_tuple(0x3FFF, 0x3F1F),
        // Unaffected
        std::make_tuple(0x2000, 0x2000),
        std::make_tuple(0x3EFF, 0x3EFF),
    };
    for (auto& c : cases) {
        uint16_t address = std::get<0>(c);
        uint16_t expected_address = std::get<1>(c);
        assert(expected_address == maybe_resolve_palette_address(address));
    }
}

void
test_get_pixel_bits_from_pattern_table() {
    /*
     * Pattern table bytes combine together to generate pixel bits
     * for the x pixels in the background.
     */
    Clock clock;
    OAM oam;
    IO_DB bus;
    PPU ppu = PPU(bus, clock, oam);

    std::vector<std::tuple<uint8_t, uint8_t, uint8_t, uint8_t>> cases = {};
    // Generate a lot of test cases. This basically uses working code to
    // do the same generation of the bits to the ntest against any modification
    // of the working code.
    // Although we only care really about shifting from [0, 7], shifting
    // from [0, 8] will ensure we get 0 values in both the high and low bytes.
    // as the bit will inevitably fall off the end.
    for (uint8_t x = 0; x < 16; x++) {
        for (uint8_t high_byte_shift = 0; high_byte_shift <= 8; high_byte_shift++) {
            for (uint8_t low_byte_shift = 0; low_byte_shift <= 8; low_byte_shift++) {
                uint8_t low_byte = 1 << low_byte_shift;
                uint8_t high_byte = 1 << high_byte_shift;

                uint8_t x_offset_into_tile = 7 - (x % 8);
                uint16_t pixel_low_bit = low_byte & (0x1 << x_offset_into_tile);
                uint16_t pixel_high_bit = high_byte & (0x1 << x_offset_into_tile);
                pixel_high_bit <<= 1;
                uint16_t pixel_bits = pixel_low_bit + pixel_high_bit;
                // By this point pixel_bits fits into uint8_t once more.
                pixel_bits >>= x_offset_into_tile;

                uint8_t reversed_low_byte = ByteReverseTable[low_byte];
                uint8_t reversed_high_byte = ByteReverseTable[high_byte];
                auto t = std::make_tuple(
                    reversed_high_byte,
                    reversed_low_byte,
                    pixel_bits,
                    x
                );
                cases.emplace_back(t);
            }
        }
    }

    for (auto& c : cases) {
        uint8_t high_byte = std::get<0>(c);
        uint8_t low_byte = std::get<1>(c);
        uint8_t expected_pixel_bits = std::get<2>(c);
        uint8_t x = std::get<3>(c);
        ppu.background_state.pattern_table_high_byte = high_byte;
        ppu.background_state.pattern_table_low_byte = low_byte;

        uint8_t pixel_bits = _get_pixel_bits_from_pattern_table(ppu, x, 0);
        if (expected_pixel_bits != pixel_bits) {
            printf("Failed %x %x %d.\n"
                   "Expected %x got %x\n",
                   high_byte, low_byte, x, expected_pixel_bits, pixel_bits);
        }
        assert(expected_pixel_bits == pixel_bits);
    }
}

int
main() {
    test_resolve_register();
    test_maybe_resolve_nametable_address();
    test_maybe_resolve_palette_address();
    test_get_pixel_bits_from_pattern_table();
    return 0;
}
