#include "NES.h"
#include "Renderer.h"
#include <string>

int
main() {
    std::string filepath = "../roms/donkey_kong/donkey_kong.nes";

    NES nes = NES(filepath);
    nes.ppu.renderer.render_type = RenderType::FILE;
    // Running for 5 frames is enough to get to the title screen,
    // which should be good enough as a test so far.
    while (nes.ppu.frames < 22) {
        nes.next_frame();
    }
    return 0;
}