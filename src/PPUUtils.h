#ifndef PPU_UTILS_H
#define PPU_UTILS_H

#include "Constants.h"
#include "Opcodes.h"
#include "PPUMemory.h"
#include <stdint.h>

class PPU;

PPURegister resolve_register(uint16_t address);

PPURegister resolve_register_from_instruction(
    Instruction instruction,
    uint8_t* instruction_bytes
);

uint16_t
maybe_resolve_nametable_address(
    uint16_t address,
    NametableMirroring mirroring
);

uint16_t
maybe_resolve_palette_address(uint16_t address);

uint8_t
_nametable_byte_from_pixel(PPU& ppu, uint16_t x, uint16_t y);

uint8_t
_attribute_table_byte_from_pixel(PPU& ppu, uint16_t x, uint16_t y);

bool
_pattern_table_bytes(
    PPU& ppu,
    uint16_t x,
    uint16_t y,
    uint8_t* high_byte,
    uint8_t* low_byte
);

uint8_t
_get_pixel_bits_from_pattern_table(PPU& ppu, uint16_t x, uint16_t y);

uint32_t
_palette_bytes_from_attribute_table(PPU& ppu, uint16_t x, uint16_t y);

uint8_t
_background_colour_for_pixel(
    PPU& ppu,
    uint16_t x,
    uint16_t y,
    bool use_cache
);

uint8_t
colour_for_pixel(PPU& ppu, uint16_t x, uint16_t y);

void
_pixel_bits_for_sprite(
    PPU& ppu,
    uint8_t sprite_tile,
    uint8_t* grid_output
);

bool
_render_sprite(PPU& ppu);

void
render_sprites(PPU& ppu);

#endif
