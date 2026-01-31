#include "NES.h"
#include "Constants.h"

NES::NES(std::string filepath) :
cartridge(filepath),
cpu(bus, clock, oam),
ppu(bus, clock, oam) {
    cartridge.store_rom(cpu.memory);
    // Need to call reset after th ROM is stored so the start
    // address can be read from the reset vector now that some
    // address is actually there.
    cpu.reset();

    // self.ppu.memory.nametable_mirroring = self.cartridge._header.nametable_mirroring
    cartridge.store_palette(ppu.memory);
}

void
NES::next_frame() {
    uint64_t last_frame = ppu.frames;
    while (ppu.frames <= last_frame) {
        cpu.next(ppu.generated_nmi());
    }
}

void
NES::handle_input(Input input) {
    cpu.nes_controller.handle_input(input);
    // printf("Got input: %s\n", InputToString(input));
}
