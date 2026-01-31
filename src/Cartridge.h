#ifndef CARTRIDGE_H
#define CARTRIDGE_H

#include <string>
#include <stdint.h>

class CPUMemory;
class PPUMemory;

struct header_t {
    uint8_t magic_number[0x4] = { 0 };
    // Number of 16kb (pages) ROM Banks
    uint8_t prg_rom_size;
    // Number of 8kb (pages) VROM banks
    // So if it's 1, we have 1 8kb VROM bank page.
    uint8_t chr_rom_size;
    // TODO
    // Handle flags 6-10
    // https://wiki.nesdev.com/w/index.php/INES#Flags_6
    // For now assuming there's no trainer due to the test file but if
    // we want to handle the trainer, we'll need to look at flags 6
    // not sure which bit.
    // (flag6) bit 4-7   Four lower bits of ROM Mapper Type.
    uint8_t flags_6;
    // (flag7) bit 4-7   Four higher bits of ROM Mapper Type.
    uint8_t flags_7;
    uint8_t flags_8;
    uint8_t flags_9;
    uint8_t flags_1;
    uint8_t padding[0x6];
};

class Cartridge {
public:
    // TODO
    // This is way too big but it'll do for now.
    // (It's 1 mb)
    uint8_t data[1000000] = { 0 };
    header_t header;

private:
    void _check_magic_number();

public:
    Cartridge(std::string filepath);
    // Binary values set from the header.
    bool nametable_mirroring();
    bool battery_backed_memory();
    bool trainer();
    uint16_t rom_type();

    // These have to be references or else we're writing to
    // copies of the memory which won't work at all.
    void store_rom(CPUMemory& memory);
    void store_palette(PPUMemory& memory);
};

#endif
