#ifndef NES_H
#define NES_H

#include "Cartridge.h"
#include <string>
#include "Clock.h"
#include "CPU.h"
#include "IO_DB.h"
#include "OAM.h"
#include "PPU.h"

enum class Input;

class NES {

public:
    Clock clock = Clock();
    IO_DB bus = IO_DB();
    OAM oam = OAM();
    Cartridge cartridge;
    CPU cpu;
    PPU ppu;

public:
    NES(std::string filepath);
    void next_frame();
    void handle_input(Input input);
};

#endif
