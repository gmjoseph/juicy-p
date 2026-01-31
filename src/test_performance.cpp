#include "NES.h"
#include <string>

int
main() {
    std::string filepath = "../roms/donkey_kong/donkey_kong.nes";
    NES nes = NES(filepath);
    while (nes.ppu.frames < 3000) {
        nes.next_frame();
    }
    return 0;
}
