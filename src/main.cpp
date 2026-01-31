#include "NES.h"
#include <stdio.h>

int
main(int argc, const char* argv[]) {
    std::string filepath = "../roms/donkey_kong/donkey_kong.nes";
    NES nes = NES(filepath);
    while (1) {
        nes.run();
        // Quit if we made it to the demo screen past title.
        if (nes.cpu.pc == 0xc955) {
            printf("Going to demo, took %llu frames to get here\n", nes.ppu.frames);
        }
    }
    return 0;
}
