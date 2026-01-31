#include <tuple>
#include <vector>
#include <assert.h>
#include "Constants.h"
#include "PPUMemory.h"

void
test_nametable_addresses() {
    /*
     * For reads and writes, the PPU should respect mirroring settings.
     * If we write to a mirrored address, we should expect to be able
     * to read the value from the source address and vice versa.
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
        uint16_t address = std::get<0>(c);
        uint16_t mapped_address = std::get<1>(c);
        NametableMirroring mirroring = std::get<2>(c);
        PPUMemory memory;
        memory.nametable_mirroring = mirroring;
        // Ensures that the memory is in a predictable state for the
        // reads and writes to follow.
        memory.write(0x00, address);
        memory.write(0x00, mapped_address);

        memory.write(0xba, mapped_address);
        assert(0xba == memory.read_one(address));

        memory.write(0xbe, address);
        assert(0xbe == memory.read_one(mapped_address));
    }
}

void
test_palette_addresses() {
    /*
     * For reads and writes, the PPU should respect mirroring in the
     * PPU palette.
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
            std::make_tuple(0x3FFF, 0x3F1F),
            // Unaffected
            std::make_tuple(0x2000, 0x2000),
            std::make_tuple(0x3EFF, 0x3EFF),
    };
    for (auto& c : cases) {
        uint16_t address = std::get<0>(c);
        uint16_t mapped_address = std::get<1>(c);
        PPUMemory memory;
        memory.write(0x00, address);
        memory.write(0x00, mapped_address);

        memory.write(0xba, mapped_address);
        assert(memory.read_one(address) == 0xba);

        memory.write(0xbe, address);
        assert(memory.read_one(mapped_address) == 0xbe);
    }
}

int
main() {
    test_nametable_addresses();
    test_palette_addresses();
    return 0;
}
