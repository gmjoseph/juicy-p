#include <exception>
#include <map>
#include <stdexcept>
#include "Cartridge.h"
#include "CPUMemory.h"
#include "PPUMemory.h"

// TODO
// Move to constants
uint8_t _MAGIC_NUMBER[0x4] = {'N', 'E', 'S', 0x1a};
uint8_t _HEADER_SIZE = 0x10;
// 16kb
uint16_t _ROM_SIZE = 0x4000;
// 8kb
uint16_t _PALETTE_SIZE = 0x2000;

// https://wiki.nesdev.com/w/index.php/Mapper
// On where to map the physical data to virtual memory.
struct mapper_t {
    uint16_t high;
    uint16_t low;
};

std::map<uint16_t, mapper_t> mappers = {
    // NROM
    {
        0x0, {
            // TODO
            // Distinguish between NROM-128 and NROM-256.
            // https://wiki.nesdev.com/w/index.php/NROM
            // "Your program is mapped into $8000-$FFFF (NROM-256) or both $8000-$BFFF and
            // $C000-$FFFF (NROM-128). Most NROM-128 games actually run in $C000-$FFFF rather
            // than $8000-$BFFF because it makes the program easier to assemble and link"
            // CPU $C000-$FFFF: Last 16 KB of ROM (NROM-256) or mirror of $8000-$BFFF (NROM-128).
            // For a mapper of type '0' (NROM-256)...
            // We're dealing with NROM-128 for the testing ROM because it's only 16kb
            // (128kilobit i.e. 128/8 = 16kb), so let's just hardcode that for now.
            .high = 0xc000,
            .low = 0x8000
        }
    }
};

Cartridge::Cartridge(std::string filepath) {
    FILE* f = fopen(filepath.c_str(), "rb");
    if (NULL == f) {
        std::throw_with_nested(
            std::runtime_error("Couldn't read cartridge file.\n")
        );
    }

    // FIXME
    // This should be enough and it's the same of the buffer anyway
    // but this should be smarter in future (read header first, then
    // sections, etc.);
    fread(data, 1000000, 1, f);
    memcpy(&header, data, sizeof(header_t));
    fclose(f);
}

void
Cartridge::_check_magic_number() {
    if (memcmp(header.magic_number, _MAGIC_NUMBER, 0x4)) {
        std::throw_with_nested(
            std::runtime_error("Magic number mismatch.\n")
        );
    }
}

bool
Cartridge::nametable_mirroring() {
    // Description of these properties:
    // 76543210
    // ||||||||
    // |||||||+- Mirroring: 0: horizontal (vertical arrangement) (CIRAM A10 = PPU A11)
    // |||||||              1: vertical (horizontal arrangement) (CIRAM A10 = PPU A10)
    // ||||||+-- 1: Cartridge contains battery-backed PRG RAM ($6000-7FFF) or other persistent memory
    // |||||+--- 1: 512-byte trainer at $7000-$71FF (stored before PRG data)
    // ||||+---- 1: Ignore mirroring control or above mirroring bit; instead provide four-screen VRAM
    // ++++----- Lower nybble of mapper number
    // FIXME
    // Interpret this binary value correctly
    // NametableMirroring.HORIZONTAL if bool(self.flags_6 & 0x1) else NametableMirroring.VERTICAL
    // FIXME
    // This works for NROMs, there are more possible
    // mirroring configurations.
    return header.flags_6 & 0x1;
}

bool
Cartridge::battery_backed_memory() {
    return header.flags_6 & 0x2;
}

bool
Cartridge::trainer() {
    return header.flags_6 & 0x4;
}

uint16_t
Cartridge::rom_type() {
    uint8_t low = header.flags_6 >> 4;
    uint16_t high = header.flags_7 >> 4;
    return low + (high << 4);
}


void
Cartridge::store_rom(CPUMemory& memory) {
    // We'll be doing this:
    // https://wiki.nesdev.com/w/index.php/NROM#Banks
    // CPU $8000-$BFFF: First 16 KB of ROM.
    // CPU $C000-$FFFF: Last 16 KB of ROM (NROM-256) or mirror of $8000-$BFFF (NROM-128).
    // That is, since we're hardcoding this to NROM-128, 0x8000-0xBFFF
    // and 0xC000-0xFFFF should be duplicates of each other.
    mapper_t mapper = mappers[rom_type()];
    // TODO
    // We may need a function per mapper strategy. This might not be needed
    // depending on how much in common there is between mappers and how
    // much can be derived from the configuration data.
    uint64_t data_address = (uint64_t)((uint8_t*)data);
    uint8_t* start_address = (uint8_t*)(data_address + _HEADER_SIZE);
    memory.write_cpu_memory(mapper.low, 0x4000, start_address);
    memory.write_cpu_memory(mapper.high, 0x4000, start_address);
}

void
Cartridge::store_palette(PPUMemory& memory) {
    if (header.chr_rom_size > 0) {
        uint64_t start = _HEADER_SIZE + _ROM_SIZE;
        uint64_t end = start + _PALETTE_SIZE;
        uint64_t data_address = (uint64_t)((uint8_t*)data);
        uint8_t* start_address = (uint8_t*)(data_address + start);
        // Write palette beginning at 0 always.
        memory.write_ppu_memory(0, _PALETTE_SIZE, start_address);
    }
}
