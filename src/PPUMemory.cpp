#include "PPUMemory.h"
#include "PPUUtils.h"

uint16_t
PPUMemory::_run_address_preprocessors(uint16_t address) {
    // Lots of potential places for mirroring, so each address needs
    // to be processed to find its physical location.
    uint16_t original_address = address;
    if (address > 0x4000) {
        // The valid range of addresses we can write to on the PPU is
        // 0x0 -> 0x3fff, higher addresses are mirrored down which just
        // means in terms of the implementation that we can wrap them
        // back around.
        address %= 0x4000;
    }

    // FIXME
    // Update mirroring to pull real value.
    address = maybe_resolve_nametable_address(address, nametable_mirroring);
    address = maybe_resolve_palette_address(address);

#ifdef PPU_ADDRESS_CACHING
    _address_cache[original_address] = address;
#endif
    return address;
}

void
PPUMemory::write_ppu_memory(uint16_t at_address, uint16_t amount, uint8_t* in_buffer) {
    uint64_t ppu_memory_address = (uint64_t)(ppu_memory);
    uint8_t* write_to = (uint8_t*)(ppu_memory_address + at_address);
    memcpy(write_to, in_buffer, amount);
}