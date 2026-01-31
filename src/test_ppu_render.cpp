#include <string>
#include <tuple>
#include <vector>
#include <stdio.h>
#include <stdint.h>
#include "Clock.h"
#include "IO_DB.h"
#include "OAM.h"
#include "PPU.h"
#include "PPUUtils.h"
#include "Renderer.h"


typedef std::tuple<const char*, uint32_t, uint32_t> PathMemoryLocation;

void
_load_data_to_ppu(
    PPU& ppu,
    std::vector<PathMemoryLocation>& path_and_memory_location
) {
    // Enough to read in any of the dumps without dynamic allocation.
    uint8_t buffer[0x4000] = {};

    for (auto& pml : path_and_memory_location) {
        auto path = std::get<0>(pml);
        auto start = std::get<1>(pml);
        auto end = std::get<2>(pml);
        FILE* f = fopen(path, "rb");
        if (NULL == f) {
            printf("Failed to open path %s\n", path);
            exit(1);
        }
        fread(buffer, end - start, 1, f);
        ppu.memory.write_ppu_memory(start, end - start, buffer);
        fclose(f);
    }
}

void
test_title_frame() {
    /*
     * Uses the title screen of Donkey Kong as a seed for the memory
     * of the nametable, pattern table, attribute table and palettes
     * to produce one single frame in colour.
     */
    auto clock = Clock();
    auto bus = IO_DB();
    auto oam = OAM();
    auto ppu = PPU(bus, clock, oam);
    ppu.renderer.file_prefix = "donkey_kong_title";
    ppu.renderer.render_type = RenderType::FILE;

    std::vector<PathMemoryLocation> path_and_memory_location = {
        std::make_tuple("../roms/donkey_kong/donkey_kong_title_nametable.bin", 0x2000, 0x2400),
        std::make_tuple("../roms/donkey_kong/donkey_kong_title_palette.bin", 0x3f00, 0x3f20),
        std::make_tuple("../roms/donkey_kong/donkey_kong_title_pattern.bin", 0x0, 0x2000)
    };
    _load_data_to_ppu(ppu, path_and_memory_location);

    // TODO
    // Add the OAM dump and render the sprite as well.
    std::string oam_path = "../roms/donkey_kong/OAM_DUMP.txt";

    // Use the 0x1000+ pattern table.
    ppu.set_PPUCTRL(0x10);

    while (ppu.frames < 1) {
        ppu.next();
    }
    // TODO
    // It should've written a frame to disk but it helps to confirm
    // that the pixel buffer was filled with the right contents and
    // can be compared to a hash of the contents.
    // import hashlib
    // m = hashlib.md5()
    // m.update(bytearray(128).decode('latin-1'))
}

void
test_demo_frame() {
    /*
     * Uses the demo screen of Donkey Kong as a seed for the memory
     * of the nametable, pattern table, attribute table and palettes
     * to produce one single frame in colour.
     */
    auto clock = Clock();
    auto bus = IO_DB();
    auto oam = OAM();
    auto ppu = PPU(bus, clock, oam);
    ppu.renderer.file_prefix = "donkey_kong_demo";
    ppu.renderer.render_type = RenderType::FILE;

    std::vector<PathMemoryLocation> path_and_memory_location = {
        std::make_tuple("../roms/donkey_kong/donkey_kong_demo_nametable.bin", 0x2000, 0x2400),
        std::make_tuple("../roms/donkey_kong/donkey_kong_demo_palette.bin", 0x3f00, 0x3f20),
        std::make_tuple("../roms/donkey_kong/donkey_kong_demo_pattern.bin", 0x0, 0x2000)
    };
    _load_data_to_ppu(ppu, path_and_memory_location);
    // Use the 0x1000+ pattern table.
    ppu.set_PPUCTRL(0x10);

    while (ppu.frames < 1) {
        ppu.next();
    }
}

void
test_ppu_background_colour_for_pixel() {
    /*
     * For a combo of x, y pixel inputs and the PPU memory dumps,
     * test whether the right palette byte was given back.
     */
    auto clock = Clock();
    auto bus = IO_DB();
    auto oam = OAM();
    auto ppu = PPU(bus, clock, oam);

    std::vector<std::tuple<const char*, uint32_t, uint32_t>> path_and_memory_location = {
        std::make_tuple("../roms/donkey_kong/donkey_kong_title_nametable.bin", 0x2000, 0x2400),
        std::make_tuple("../roms/donkey_kong/donkey_kong_title_palette.bin", 0x3f00, 0x3f20),
        std::make_tuple("../roms/donkey_kong/donkey_kong_title_pattern.bin", 0x0, 0x2000)
    };
    _load_data_to_ppu(ppu, path_and_memory_location);

    std::vector<std::tuple<uint8_t, uint8_t, uint8_t>> params = {
        std::make_tuple(12, 0, 0xf),
        std::make_tuple(126, 23, 0x2c),
        std::make_tuple(0, 0, 0xf),
        std::make_tuple(255, 239, 0x2c),
        std::make_tuple(128, 120, 0xf),
        std::make_tuple(56, 120, 0xf),
        std::make_tuple(72, 128, 0xf),
        std::make_tuple(83, 200, 0xf),
        std::make_tuple(83, 204, 0xf),
        std::make_tuple(83, 214, 0x30)
    };

    for (auto& t : params) {
        uint16_t x = (uint16_t)std::get<0>(t);
        uint16_t y = (uint16_t)std::get<1>(t);
        uint8_t expected_colour = (uint16_t)std::get<2>(t);
        auto colour = _background_colour_for_pixel(ppu, x, y, false);
        if (colour != expected_colour) {
            printf("Failed on colour %x, got %x (%d, %d)\n",
                expected_colour, colour, x, y
            );
        }
    }
}

int
main() {
    test_demo_frame();
    test_title_frame();
    test_ppu_background_colour_for_pixel();
    return 0;
}
