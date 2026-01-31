#include "PPUUtils.h"
#include "PPU.h"

#pragma mark - PPU Memory Utils

PPURegister
resolve_register_from_instruction(
    Instruction instruction,
    uint8_t* instruction_bytes
) {
    // TODO
    // PPU registers are only ever accessed with absolute addressing modes
    // because of how they're memory mapped on the CPU?
    if (AddressingMode::ABSOLUTE == instruction.addressing_mode) {
        uint8_t low = instruction_bytes[1];
        uint16_t high = instruction_bytes[2] << 0x8;
        uint16_t address = high + low;
        return resolve_register(address);
    }
    return PPURegister::NONE;
}

PPURegister
resolve_register(uint16_t address) {
    // If the instruction is referencing a PPU address, this will
    // determine if so and which one.

    // "The PPU exposes eight memory-mapped registers to the CPU.
    // These nominally sit at $2000 through $2007 in the CPU's address
    // space, but because they're incompletely decoded, they're
    // mirrored in every 8 bytes from $2008 through $3FFF, so a write
    // to $3456 is the same as a write to $2006. "
    // Probably with modulo and a check on the range
    // A nice way to handle this is (target_address - register_address) % 8 == 0.
    // If that's true, then we're writing to a certain register.
    // For instance, if 0x3456 is meant to write to 0x2006, then
    // (0x3456-0x2006) % 0x8 should be zero. Any of the other registers
    // shouldn't work:
    // (0x3456 - 0x2000) % 8 == 6
    // (0x3456 - 0x2001) % 8 == 5
    // (0x3456 - 0x2002) % 8 == 4
    // (0x3456 - 0x2003) % 8 == 3
    // (0x3456 - 0x2004) % 8 == 2
    // (0x3456 - 0x2005) % 8 == 1
    // (0x3456 - 0x2006) % 8 == 0 <--
    // (0x3456 - 0x2007) % 8 == 7
    // etc.
    //
    // That said, this can all be replaced by masking with the original
    // address and seeing if the address, after applying the mask, is still
    // the original address.
    // E.g.:
    // 0x3000 & 0x2000 == 0x2000 ? it does.
    // 0x3ff8 & 0x2000 == 0x2000 ? it does.
    // 0x3ff8 & 0x2001 == 0x2001 ? it doesn't.

    PPURegister reg = PPURegister::NONE;

    // Special case, technically resides in the CPU but the data must be
    // transferred to internal PPU memory.
    if (address == (uint16_t)PPUAddress::OAMDMA_ADDRESS) {
        return PPURegister::OAMDMA;
    }

    if (address < 0x2000 || address >= 0x4000) {
        // We don't map addresses in this range to any register in particular,
        // see the comment above.
        return reg;
    }

    // FIXME
    // Returning early or if/elsing here breaks a tonne of tests, namely to do
    // with writing to certain registers. This should be fixed. Maybe multiple
    // conditions end up being met which causes problems?
    // The reason this fails at times is for NON MIRRORED addresses, where
    // for example 0x2001 & 0x2000 will be 0x2000 so we'll think that PPUMASK
    // is for PPUCTRL, which is why we need this 'fall through' behaviour.
    // This could be fixed by a lookup or maybe some kind of normalization?
    if ((address & (uint16_t)PPUAddress::PPUCTRL_ADDRESS) ==
        (uint16_t)PPUAddress::PPUCTRL_ADDRESS) {
        reg = PPURegister::PPUCTRL;
    }
    if ((address & (uint16_t)PPUAddress::PPUMASK_ADDRESS) ==
        (uint16_t)PPUAddress::PPUMASK_ADDRESS) {
        reg = PPURegister::PPUMASK;
    }
    if ((address & (uint16_t)PPUAddress::PPUSTATUS_ADDRESS) ==
        (uint16_t)PPUAddress::PPUSTATUS_ADDRESS) {
        reg = PPURegister::PPUSTATUS;
    }
    if ((address & (uint16_t)PPUAddress::OAMADDR_ADDRESS) ==
        (uint16_t)PPUAddress::OAMADDR_ADDRESS) {
        reg = PPURegister::OAMADDR;
    }
    if ((address & (uint16_t)PPUAddress::OAMDATA_ADDRESS) ==
        (uint16_t)PPUAddress::OAMDATA_ADDRESS) {
        reg = PPURegister::OAMDATA;
    }
    if ((address & (uint16_t)PPUAddress::PPUSCROLL_ADDRESS) ==
        (uint16_t)PPUAddress::PPUSCROLL_ADDRESS) {
        reg = PPURegister::PPUSCROLL;
    }
    if ((address & (uint16_t)PPUAddress::PPUADDR_ADDRESS) ==
        (uint16_t)PPUAddress::PPUADDR_ADDRESS) {
        reg = PPURegister::PPUADDR;
    }
    if ((address & (uint16_t)PPUAddress::PPUDATA_ADDRESS) ==
        (uint16_t)PPUAddress::PPUDATA_ADDRESS) {
        reg = PPURegister::PPUDATA;
    }
    return reg;
}

uint16_t
maybe_resolve_nametable_address(
    uint16_t address,
    NametableMirroring mirroring
) {
    // The full range of addresses. There could be multiple levels of mirroring,
    // e.g. the address is in the nametable_mirrors but then maps back to
    // an address that is horizontally mirrored from 0x2400 back to 0x2000.
    uint16_t output_address = address;

    // FIXME
    // Use constants
    // Nametable range start
    uint16_t start = 0x2000;
    // Nametable range end
    uint16_t end = 0x3eff;
    if (address < start || address > end) {
        // Out of the nametable range.
        return output_address;
    }

    // FIXME
    // Use constants
    uint16_t mirrors_start = 0x3000;
    uint16_t mirrors_end = 0x3eff;
    if (address >= mirrors_start && address <= mirrors_end) {
        // Resolve the mirrored address to an actual nametable address.
        // Since this mirrors 0x2000 - 0x2EFF in 0x3000 to 0x3EFF
        // we can just subtract down.
        output_address = address - 0x1000;
    }

    // From this point on, check on output_address in case `address` was
    // a mirrored one.

    if (mirroring == NametableMirroring::HORIZONTAL) {
        // "Horizontal mirroring: $2000 equals $2400 and $2800 equals $2C00
        // (e.g. Kid Icarus)"
        // Top right and bottom right.
        // 'nametable_1':     (0x2400, 0x27FF),
        // 'nametable_3':     (0x2C00, 0x2FFF),
        bool mirror_1 = 0x2400 <= output_address && output_address <= 0x27ff;
        bool mirror_3 = 0x2c00 <= output_address && output_address <= 0x2fff;
        if (mirror_1 || mirror_3) {
            // E.g. 0x2400 back to 0x2000 is a difference of the nametable
            // size.
            output_address -= NametableSize;
        }
    }

    if (mirroring == NametableMirroring::VERTICAL) {
        // "Vertical mirroring: $2000 equals $2800 and $2400 equals $2C00
        // (e.g. Super Mario Bros.)"
        // 'nametable_2':     (0x2800, 0x2BFF),
        // 'nametable_3':     (0x2C00, 0x2FFF),
        bool mirror_2 = 0x2800 <= output_address && output_address <= 0x2bff;
        bool mirror_3 = 0x2c00 <= output_address && output_address <= 0x2fff;
        if (mirror_2 || mirror_3) {
            // E.g. 0x2800 back to 0x2000 is a difference of double
            // the name table size.
            output_address -= NametableSize * 2;
        }
    }

    return output_address;
}

uint16_t
maybe_resolve_palette_address(uint16_t address) {
    /*
     * Two mirroring requirements:
     * 1. The addresses in the palette ram that map directly to
     * one another address in the palette ram:
     * "Addresses $3F10/$3F14/$3F18/$3F1C are mirrors of
     * $3F00/$3F04/$3F08/$3F0C. Note that this goes for writing
     * as well as reading. A symptom of not having implemented
     * this correctly in an emulator is the sky being black in
     * Super Mario Bros., which writes the backdrop color
     * through $3F10."
     * 2. The other is for a mirror of the entire contents of
     * palette ram.
     */
    switch (address) {
        case 0x3f10:
        case 0x3f14:
        case 0x3f18:
        case 0x3f1c:
            return address - 0x10;
    }

    // 'palette_ram_mirrors': (0x3F20, 0x3FFF),
    uint16_t palette_ram_mirrors_start = 0x3f20;
    uint16_t palette_ram_mirrors_end = 0x3fff;
    if (palette_ram_mirrors_start <= address &&
        address <= palette_ram_mirrors_end) {
        // Repeats at every 0x20 intervals, or 7 times.
        // 'palette_ram_indexes': (0x3F00, 0x3F1F),
        uint16_t indexes_start = 0x3f00;
        uint16_t delta = address - indexes_start;
        // Determines how many multipliers of 0x20 have been
        // added to the address.
        // 3f20 = 3f00 (0x20 * 1)
        // 3f40 = 3f00 (0x20 * 2)
        // 3f60 = 3f00 (0x20 * 3)
        // ...
        // 3fe0 = 3f00 (0x20 * 7)
        // delta // 0x20 is the same as delta >> 5
        uint16_t multiplier = delta >> 5;
        address = address - 0x20 * multiplier;
    }

    return address;
}

#pragma mark - PPU Instruction Utils

uint8_t
_nametable_byte_from_pixel(PPU& ppu, uint16_t x, uint16_t y) {
    /*
     * "A nametable is a 1024 byte area of memory used by the PPU to
     * lay out backgrounds. Each byte in the nametable controls one
     * 8x8 pixel character cell, and each nametable has 30 rows of
     * 32 tiles each, for 960 ($3C0) bytes; the rest is used by each
     * nametable's attribute table. With each tile being 8x8 pixels,
     * this makes a total of 256x240 pixels in one map, the same size
     * as one full screen."
     * Because we're operating on the lowest level of granularity,
     * the pixel, we need to resolve it to the nametable tile, which
     * is made up of 8x8 pixels.
     * Summarized:
     * * 8x8 pixel tiles.
     * * 30 rows of 32 tiles each in a nametable.
     * * 960 bytes (0x3c0).
     * * each tile is 8x8 so 256x240 pixels in one map.
     */
    // This gives us the row, column of the tile in the 32x30
    // space of tiles, which we then need to convert into an address.
    // E.g. pixel (8, 0) =  tile (8 // 8, 8 // 0) = tile (1, 0).
    // Dividing by 8 is the same as shifting right 3 times (2^3).
    uint16_t tile_x = x >> 3;
    uint16_t tile_y = y >> 3;
    // tile_y increments imply that we've gone through a whole row
    // of tiles, each of which is a byte each. A row of pixels is
    // 256 pixels, so 256/8 bytes = 32 tiles or 32 bytes.
    uint16_t tile_address_offset = tile_x + tile_y * 0x20;
    uint16_t nametable_address = ppu.base_nametable_address() + tile_address_offset;
    uint8_t nametable_byte = ppu.memory.read_one(nametable_address);
    return nametable_byte;
}

uint8_t
_attribute_table_byte_from_pixel(PPU& ppu, uint16_t x, uint16_t y) {
    /*
     * See _nametable_byte_from_pixel.
     */
    // "Each byte controls the palette of a 32×32 pixel or 4×4 tile part
    // of the nametable and is divided into four 2-bit areas. Each area
    // covers 16×16 pixels or 2×2 tiles, the size of a [?] block in Super
    // Mario Bros. Given palette numbers topleft, topright, bottomleft,
    // bottomright, each in the range 0 to 3, the value of the byte is
    // ..."
    // Once we have the attribute table byte we can then figure out the
    // colour bits:
    // 7654 3210
    // |||| ||++- Color bits 3-2 for top left quadrant of this byte
    // |||| ++--- Color bits 3-2 for top right quadrant of this byte
    // ||++------ Color bits 3-2 for bottom left quadrant of this byte
    // ++-------- Color bits 3-2 for bottom right quadrant of this byte
    // https://wiki.nesdev.com/w/index.php/PPU_attribute_tables

    // It's at the end of the nametable, so if the nametable
    // starts at 0x2000, then the attribute table starts at
    // 0x23c0 and ends at 0x2400.
    // The attribute table is divided into an 8x8 grid giving us 64
    // bytes (0x40).

    // To figure out the x we just divide with rounding by 32 since we have
    // 32 tiles going horizontally.
    // E.g. 256/32 = 8 (the 8th tile for the last pixel) or 128/32 = 4
    // (the middle tile for the 128th pixel)
    // Dividing by 32 is the same as shifting right by 5 (2^5 = 32)
    uint16_t attrib_x = x >> 5;
    // Technically, we only have 240 pixels vertically which is 30 tiles
    // going down in the nametable. However, the attribute grid is 8x8,
    // we just dont need to lower bits of the attribute bytes on the last
    // row.
    uint16_t attrib_y = y >> 5;

    // 8 bytes per row, where an increment in attrib_y means we've gone
    // down an entire row.
    // So at x = 1, y = 1, we're on byte 9.
    // at x = 7, y = 7 we're on byte 63 (the last one).
    uint16_t attribute_table_offset = attrib_x + attrib_y * 0x8;

    // Don't forget to find the real address in memory by adding it to
    // the nametable base + the offset to the beginning of the attribute
    // table.
    uint16_t attribute_table_address = ppu.base_nametable_address() + 0x3C0;
    attribute_table_address += attribute_table_offset;
    if (!(0x2000 <= attribute_table_address && attribute_table_address <= 0x3000)) {
        printf("Attribute table address out of range (throw exception)\n");
    }
    uint8_t attribute_table_byte = ppu.memory.read_one(attribute_table_address);
    return attribute_table_byte;
}

bool
_pattern_table_bytes(
    PPU& ppu,
    uint16_t x,
    uint16_t y,
    uint8_t* low_byte,
    uint8_t* high_byte
) {
    /*
     * Returns the high and low pattern table byte using the nametable byte's value
     * as an index into the pattern table. This index tells us where in the pattern
     * table we should get enough data for 16x16 pixels worth of information. Because
     * each chunk of data is 16 bytes, we need to multiply the index by 0x10 (16) to
     * get to the next chunk of 16 bytes.
     * The PPUCTRL register also controls the base address of the pattern table so we
     * need to account for that as well. Since a nametable tile is only for 8x8 pixels,
     * we end up with more information than we need.
     * We pull a high and low byte from the pattern table. This is enough for 8 pixels'
     * worth of data since we need to combine the bytes together. The high byte's bits
     * become the high bits for each of the 8 pixels, while the low byte's bits are
     * the low ones.
     * For example:
     * high byte: 0x4, in binary: 0000 0100
     * low byte: 0x3, inbinary: 0000 0011
     * combine bits:
     * 0-0, 0-0, 0-0, 0-0 (upper 4 bits of high and low byte)
     * 0-0, 1-0, 0-1, 0-1 (lower 4 bits of high and low byte)
     *
     * The values that are produced from this combination are the indices into the
     * background palettes. For example if at the pixel we got 0b10, then we know
     * we need to access background palette 3 (0 indexed, so 0, 1, 2, 3).
     * See here for more info:
     * https://wiki.nesdev.com/w/index.php/PPU_programmer_reference#Pattern_tables
     */
    // This value should already be stored in the background_state.
    uint16_t nametable_byte = ppu.background_state.nametable_byte;
    uint16_t pattern_table_start = ppu.background_pattern_table_start();
    uint16_t pattern_table_byte_address = pattern_table_start + nametable_byte * 0x10;

    // We know that the pixel is in one of 32x30 tiles, so if we divide
    // the pixel by 8 on x and y we get back to the tilespace coordinates
    // which we did for the nametable. The next step is to see what the
    // remainder of having done so is because that says how far we've stepped
    // pixelwise (of the 8x8 pixels) into the tile.

    // Also I thought initially it should be (0x1 << x_offset_into_tile)
    // for the mask where x_offset_into_tile is just x % 8 but that actually
    // mirrors every pattern defined in the byte because we then end up
    // reading from right to left, when we know the entire pattern is laid
    // out from left to right. So another option could be to reorder the byte's
    // bits from high -> low, to low -> high where low becomes the upper bits.
    // ANDing by the (modulus - 1) is the same thing as taking the modulus.
    uint8_t modulus = 8 - 1;
    uint8_t x_offset_into_tile = 7 - (x & modulus);
    uint8_t y_offset_into_tile = y & modulus;

    // Get high and low byte so we can combine them together.
    // Most demonstrations show this as getting 16 bytes so
    // we can build a 4x4 (16 byte) grid, but we only need
    // one byte (if that) for the current pattern.
    uint8_t pattern_low_byte = ppu.memory.read_one(pattern_table_byte_address + y_offset_into_tile);
    uint8_t pattern_high_byte = ppu.memory.read_one(pattern_table_byte_address + y_offset_into_tile + 8);
    *low_byte = pattern_low_byte;
    *high_byte = pattern_high_byte;
    return true;
}

uint32_t
_palette_bytes_from_attribute_table(PPU& ppu, uint16_t x, uint16_t y) {
    /*
     * A nametable tile is subdivided into pixel quadrants of 4x4 pixels in size.
     * Once we know which quadrant the pixel is in, it lets us know which of the
     * four background palettes to use for that entire quadrant's pixels.
     * After that we can take the 0-3 pixel bits as an index into the palette.
     * Quadrants are the bits of the attribute_table_byte:
     *
     * 0 2
     * 1 3
     *
     * So the top left will be the first 2 bits, which is at max 3 (but 4 values
     * including 0) for any pixels in that quadrant.
     */
    // This value should already be in the state.
    uint8_t attribute_table_byte = ppu.background_state.attribute_table_byte;

    // We know the attribute table gives us 8x8 tiles that are then subdivided
    // into these 4 quadrants. By diving by 16 (32 / 2) we'll get that
    // same subdivision on the pixel along the x axis. Only multiply by 2 because
    // there are only 2 quadrants going along x, and another 2 going along y.
    // We do the same thing for y, since we've divided y by 32 even if we're
    // only using 240 out of 256 pixels of data for it.
    // Dividing by 16 is the same as shifting right by 4 (2^4 = 16)
    uint8_t quads_x = x >> 4;
    uint8_t quads_y = y >> 4;

    // We know that along the x we alternate from quadrant 0 and I for even
    // rows, and II and III for odd rows:
    // row 1: 0, 1, 0, 1, 0, 1...
    // row 2: 2, 3, 2, 3, 1, 3...
    // Along the y axis is a similar story, except it's 0, II for even
    // columns and I and III for odd columns.
    // So if the row is odd and the column is odd it's in quadrant III
    // If row is even and column is odd it's in quadrant I.

    // quads_x % 2 == 0 is the same as just checking if the 1 bit is
    // set. Because any number that can't be divided evenly by 2 has
    // to have the 1 bit set since everything else is a 2^n (as is
    // 1, it's 2^0 but it's a special case here...)
    bool even_row = (quads_x & 1) == 0;
    bool even_column = (quads_y & 1) == 0;

    uint8_t background_palette_index = 0x0;
    // FIXME
    // Could be done with bit operations: by figuring out even_row
    // and even_column we could then just use that value as the bit
    // shift to get the quadrant. It would just take some time
    // to figure out on paper.
    // ANDing with 0x3 makes sure to keep all bits that were already
    // set since anything ANDed with 0b11 will preserve the lowest
    // two bits.
    if (even_row && even_column) {
        uint8_t top_left = attribute_table_byte & 0x3;
        background_palette_index = top_left;
    } else if (even_row && !even_column) {
        uint8_t top_right = (attribute_table_byte >> 0x4) & 0x3;
        background_palette_index = top_right;
    } else if (!even_row && even_column) {
        uint8_t bottom_left = (attribute_table_byte >> 0x2) & 0x3;
        background_palette_index = bottom_left;
    } else if (!even_row && !even_column) {
        uint8_t bottom_right = (attribute_table_byte >> 0x6) & 0x3;
        background_palette_index = bottom_right;
    } else {
        // TODO
        // Raise exception.
        // This should never happen.
        // raise Exception("Impossible to get a background palette index.")
        printf("Impossible to get a background palette index.\n");
    }

    // Now that we know which palette index to look at, return the bytes
    // at that index.
    uint32_t palette_bytes = ppu.memory.background_palette(background_palette_index);
    return palette_bytes;
}

uint8_t
_get_pixel_bits_from_pattern_table(PPU& ppu, uint16_t x, uint16_t y) {
    // TODO
    // This is a candidate for performance optimization.
    // These values should already be in the state.
    uint8_t pattern_low_byte = ppu.background_state.pattern_table_low_byte;
    uint8_t pattern_high_byte = ppu.background_state.pattern_table_high_byte;

    // Also I thought initially it should be (0x1 << x_offset_into_tile)
    // for the mask where x_offset_into_tile is just x % 8. The problem
    // with this is that we work from left to right, which means we
    // work from high bits to low bits. If we reverse all the bits in
    // the byte then we can use this approach. e.g.
    // 0b1000 0000
    // 0b1000 0000
    // x is 0 (so get the higehst bit, working from left to right)
    // Therefore, reverse each byte, leaving us with
    // 0b0000 0001
    // 0b0000 0001
    // Then x & 7 = 0 and we end up with both bits. We don't see the
    // bit reverse because we do it when we cache the high and low byte
    // in state below.
    // ANDing by the (modulus - 1) is the same thing as taking the modulus
    // which is 8 in this case.
    uint8_t x_offset_into_tile = x & 7;

    // Which bit do we want out of the bytes? That depends on the x value
    // of the pixel. The one gotcha is that we work from left to right which
    // means high bits to low bits as x increments. So if x = 0, 8, 16 .. 8 * N
    // we'll be operating from the highest bit.
    uint8_t mask = 0x1 << x_offset_into_tile;
    uint8_t pixel_low_bit = pattern_low_byte & mask;
    uint8_t pixel_high_bit = pattern_high_byte & mask;

    // Shift all the way down that we've cleared out the bits we need.
    pixel_low_bit >>= x_offset_into_tile;
    // The high bit will be one bit to the left of the low bit, because
    // that's how the bits should be combined - side by side. We can't
    // just shift one less than x_offset_into_tile in case it's 0, that's
    // why we bring them both to the lowest position and then bump up the
    // high bit by 1.
    pixel_high_bit >>= x_offset_into_tile;
    pixel_high_bit <<= 1;
    uint8_t pixel_bits = pixel_low_bit + pixel_high_bit;
    return pixel_bits;
}

uint8_t
_background_colour_for_pixel(
    PPU& ppu,
    uint16_t x,
    uint16_t y,
    // TODO
    // Update this to be an enum.
    bool use_cache
) {
    // TODO
    // Somewhat reliably reproducing this with the PPUState (except for pixelbits
    // which can also be improved, we'd just need to know which pixel bit to index
    // into for a given pixel if we had 8 pixels' worth):
    // "Conceptually, the PPU does this 33 times for each scanline:
    // Fetch a nametable entry from $2000-$2FBF.
    // Fetch the corresponding attribute table entry from $23C0-$2FFF and increment the current VRAM address within the same row.
    // Fetch the low-order byte of an 8x1 pixel sliver of pattern table from $0000-$0FF7 or $1000-$1FF7.
    // Fetch the high-order byte of this sliver from an address 8 bytes higher.
    // Turn the attribute data and the pattern table data into palette indices, and combine them with data from sprite data using priority.""

    // Elaborating on the above some more:
    // Based on NTSC timing:
    // It takes 8 cycles of work to fetch all the data that
    // we need to compute one pixel which is why they come in 8
    // pixel chunks.
    if ((x & 7) == 0 || !use_cache) {
        // Byte-size data can be cached for every 8 pixels in a row, since
        // each pixel is only using one bit of it. So at every x % 8 == 0
        // we'll need to fetch a new one rather than reusing them.
        // x & 7 is the same as x % 8 as far as testing for zero.
        uint8_t nametable_byte = _nametable_byte_from_pixel(ppu, x, y);
        ppu.background_state.nametable_byte = nametable_byte;

        uint8_t attribute_table_byte = _attribute_table_byte_from_pixel(ppu, x, y);
        ppu.background_state.attribute_table_byte = attribute_table_byte;

        uint8_t pattern_low_byte = 0;
        uint8_t pattern_high_byte = 0;
        _pattern_table_bytes(ppu, x, y, &pattern_low_byte, &pattern_high_byte);

        // Always store the reverse of these bytes because that's how
        // we'll end up using them in _get_pixel_bits_from_pattern_table
        ppu.background_state.pattern_table_low_byte = ByteReverseTable[pattern_low_byte];
        ppu.background_state.pattern_table_high_byte = ByteReverseTable[pattern_high_byte];

        // Since attribute byte doesn't change, neither should the palette
        // we pull across the 8 pixels. This means we can also cache the
        // palette.
        uint32_t palette = _palette_bytes_from_attribute_table(ppu, x, y);
        ppu.background_state.palette = palette;
    }

    uint8_t pixel_bits = _get_pixel_bits_from_pattern_table(ppu, x, y);
    uint8_t* p_palette = (uint8_t*)&ppu.background_state.palette;

    // We finally get the "colour" for this pixel from the palette.
    // This byte isn't a specific colour, it's actually used later on to look up
    // an RGB value from a palette.
    return p_palette[pixel_bits];
}

uint8_t
colour_for_pixel(PPU& ppu, uint16_t x, uint16_t y) {
    // TODO
    // Assuming everything is a BG pixel for now.
    // There is a way to prioritize which one to fetch:
    // https://wiki.nesdev.com/w/index.php/PPU_rendering#Preface
    // Check out the "Priority multiplexer decision table"
    // sprite_colour = _sprite_colour_for_pixel(ppu, x, y)
    // background_colour = _background_colour_for_pixel(ppu, x, y)
    // return background_colour if not sprite_colour else sprite_colour
    return _background_colour_for_pixel(ppu, x, y, true);
}

# pragma mark - PPU Sprite Colour Utils

void
_pixel_bits_sprite(
    PPU& ppu,
    uint8_t sprite_tile,
    uint8_t* grid_output
) {
    // TODO
    // Get pattern for sprite's 'tile' value:
    // So first we need to know if it's 8x8 or 8x16, if it's 8x8 we just use
    // PPUCTRL for the base address.
    // If it's 8x16 here is the way to get the the sprite pattern:
    // https://wiki.nesdev.com/w/index.php/PPU_OAM#Byte_1
    // "For 8x16 sprites, the PPU ignores the pattern table selection and selects a pattern table from bit 0 of this number.

    // 76543210
    // ||||||||
    // |||||||+- Bank ($0000 or $1000) of tiles
    // +++++++-- Tile number of top of sprite (0 to 254; bottom half gets the next tile)

    // Thus, the pattern table memory map for 8x16 sprites looks like this:

    //     $00: $0000-$001F
    //     $01: $1000-$101F
    //     $02: $0020-$003F
    //     $03: $1020-$103F
    //     $04: $0040-$005F
    //     [...]
    //     $FE: $0FE0-$0FFF
    //     $FF: $1FE0-$1FFF"

    // TODO
    // Distinguish between 8x8 and 8x16 sprites.

    uint16_t pattern_table_start = ppu.sprite_pattern_table_start();
    uint16_t pattern_table_byte_address = pattern_table_start + sprite_tile * 0x10;
    // Unlike the other bit functions we'll get the entire grid of
    // bits since we're just overwriting the existing bg bytes at
    // the end of the frame.
    for (int y = 0; y < 8; y++) {
        uint8_t low_byte = ppu.memory.read_one(pattern_table_byte_address + y);
        uint8_t high_byte = ppu.memory.read_one(pattern_table_byte_address + y + 8);
        // Computes the entire row of pixels, where the first pixel in the
        // row corresponds to the highest bit (since pixels are computed
        // from left to right and the highest bits are on the left too).
        for (int x = 0; x < 8; x++) {
            // The index into the specific colour in the palette is still
            // 0-3 since there are still only 4 colours.
            uint8_t high_bit = (high_byte >> (7 - x)) & 0x1;
            // Put the high bit in the 2's place so that it can be combined
            // with the low bit.
            high_bit = high_bit << 1;
            uint8_t low_bit = (low_byte >> (7 - x)) & 0x1;
            uint8_t bits = high_bit + low_bit;
            grid_output[x + y * 8] = bits;
        }
    }
}

bool
_render_sprite(PPU& ppu, uint8_t index) {
    uint32_t sprite_bytes = ppu.oam.sprite_at_index(index);
    uint8_t* p_sprite_bytes = (uint8_t*)&sprite_bytes;
    uint8_t sprite_y = p_sprite_bytes[0];
    uint8_t tile = p_sprite_bytes[1];
    uint8_t attribute = p_sprite_bytes[2];
    uint8_t sprite_x = p_sprite_bytes[3];

    if (sprite_y == 0xff) {
        // There's nothing to be done with the sprite if this is the y value.
        // As a result, the sprite wasn't rendered.
        return false;
    }

    // Get the palette:
    // Attributes
    // 76543210
    // ||||||||
    // ||||||++- Palette (4 to 7) of sprite
    // |||+++--- Unimplemented
    // ||+------ Priority (0: in front of background; 1: behind background)
    // |+------- Flip sprite horizontally
    // +-------- Flip sprite vertically
    // Two lowest bits, then shift

    uint8_t palette_index = attribute & 0x3;
    uint32_t palette_bytes = ppu.memory.sprite_palette(palette_index);
    uint8_t* p_palette_bytes = (uint8_t*)&palette_bytes;

    uint8_t flip_horizontally = (attribute >> 0x6) & 0x1;
    uint8_t flip_vertically = (attribute >> 0x7) & 0x1;

    // This is the pattern that then lets us know what to colour each
    // pixel. The sprite_x and sprite_y are the top left offset to let
    // us know where to start relative to the frame 'origin'.

    // Confirm - this might be overkill since a sprite is 8x8 pixels
    // and to generate each pixel needs 2 bits which we're storing in 1
    // byte, so actually this might be the right amount.
    uint8_t bits_grid[64] = {};
    _pixel_bits_sprite(ppu, tile, bits_grid);

    // TODO
    // This might be overkill in terms of storage.
    uint16_t pixel_x = sprite_x;
    uint16_t pixel_y = sprite_y;

    for (int y = 0; y < 8; y++) {
        int y_idx = flip_vertically ? 7 - y : y;
        for (int x = 0; x < 8; x++) {
            // Must account for horizontal flip, which would affect
            // the order we index into this buffer.
            // Another option is just to set up the bits correctly
            // based on the flipping option.
            int x_idx = flip_horizontally ? 7 - x : x;
            uint8_t palette_index = bits_grid[x_idx + y_idx * 8];
            // Universal BG colour, just let the BG through if we don't
            // have a sprite colour.
            if (palette_index != 0) {
                uint8_t colour = p_palette_bytes[palette_index];
                // Where to draw the colour?
                uint32_t pixel_index = pixel_x + pixel_y * 0x100;
                ppu.pixels[pixel_index] = colour;
            }
            pixel_x += 1;
        }
        // Reset it to the beginning of where the sprite should be drawn
        // because a row of pixels was just coloured in.
        pixel_x = sprite_x;
        pixel_y += 1;
    }

    // TODO
    // Handle priority between sprite and BG?

    // The sprite was rendered.
    return true;
}

void
render_sprites(PPU& ppu) {
    // FIXME
    // This just renders over the background at the end of the frame. That is,
    // it's basically 'blitting' the sprite in over whatever we already rendered
    // from the BG which is inefficient and not how the PPU sprite rendering
    // even works.
    // This'll maybe work for now 
    // In any case it should be good enough for now on the way to accuracy
    // and compatibility.

    // Start from highest in memory to lowest. Those lower in memory get
    // drawn in front of those higher so this forces that ordering.
    // It may not be accurate but it should be compatible.
    for (int8_t i = 63; i >= 0; i--) {
        _render_sprite(ppu, i);
    }
}
