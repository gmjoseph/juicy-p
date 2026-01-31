#include "PPUDebug.h"
#include "PPU.h"


struct Pattern {
    // The entire pattern table is 0x2000 bytes.
    // "Each tile in the pattern table is 16 bytes, made of two planes.
    // The first plane controls bit 0 of the color; the second plane
    // controls bit 1."
    // So basically each pattern should have 16 bytes in total. However,
    // because the high and low bytes combine we have 8 bytes x 8 bytes
    // worth of pixels, or 64 pixels in the pattern. Each pixel then
    // gets mapped to a byte identifier for its colour, so the end
    // result is a 8x8 pixel tile 
    uint8_t data[8][8] = { 0xff };
};

std::vector<Pattern>
patterns(PPU* ppu) {
    std::vector<Pattern> patterns = {};
    int i = 0;

    // TODO
    // This is more applicable to drawing than anything.
    // 32 patterns per row of 8 pixels each, once we can divide i
    // by this with no remainder it's time to increase the row we're
    // on for the next series of sprites.
    // int sprites_per_row = 0x8 * 0x20;
    uint8_t LUT[4] = {
        // black
        // 0x0f,
        0x00,
        // white
        // 0x30,
        0xff,
        // light grey
        // 0x10,
        0xaa,
        // dark grey
        // 0x00,
        0x55,
    };
    while (i < 0x2000) {
        // Each iteration produces a 8x8 field of colours but
        // that's not practical for writing because we want several
        // sprites on one row.
        Pattern pattern;
        for (int y = 0; y < 8; y++) {
            // Handling the high and low byte
            // row_for_pixels = row + y
            // if row_for_pixels >= len(grid):
            //     grid.append([])
            uint8_t low_byte = ppu->memory.ppu_memory[i + y];
            uint8_t high_byte = ppu->memory.ppu_memory[i + y + 0x8];

            for (int x = 0; x < 8; x++) {
                // Now we're handling the bits from the high and low byte
                // Start from the left hand most side and read to the right.
                uint8_t high_bit = (high_byte >> (7 - x)) & 0x1;
                high_bit = high_bit << 1;
                uint8_t low_bit = (low_byte >> (7 - x)) & 0x1;
                uint8_t bits = high_bit + low_bit;
                pattern.data[y][x] = LUT[bits];
            }
        }
        // 16 bytes at a time because it took 8 bytes combined with
        // another 8 bytes to make the 8x8 grid.
        i += 0x10;
        patterns.emplace_back(pattern);
    }
    return patterns;
}

PatternTable
pattern_table(PPU* ppu) {
    /*     
     *                        COLUMN
     *  
     *  PIXELS PER COLUMN       +
     *                          |
     *    +---+---+---+         |
     *    |   |   |   |         |
     *    v   v   v   v         v
     *  +-+---+---+-+-+-+-------+-------+--------------------------+
     *  |RGB|RGB|   |   |               |                          | <--+
     *  +-----------+----------------------------------------------+    |
     *  |               |               |                          | <--+  SUBROWS IN ROW
     *  +----------------------------------------------------------+    |
     *  |               |               |                          | <--+
     *  +----------------------------------------------------------+
     *  +----------------------------------------------------------+
     *  |               |               |                          |
     *  |               |               |                          |
     *  |               |               |                          | <--+  ROW
     *  |               |               |                          |
     *  |               |               |                          |
     *  +---------------+---------------+--------------------------+
     */
    // TODO
    // This is painful to reason about. The tiles really can be split
    // up into their own mini pixelbuffers so that they can be clicked
    // on one by one in the debug window.
    std::vector<Pattern> ps = patterns(ppu);
    PatternTable pt;

    // Draw the first tile.
    int tiles_per_row = 16;
    // A tile has 8 pixels going across, each of which is 3 bytes.
    int bytes_per_tile_x = 8 * 3;
    // A subrow is a single row of pixels within a row.
    // It has 8 pixels per tile, and each pixel is 3 bytes.
    // so it ends up being 16 * 8 * 3 or 128 * 3.
    int bytes_per_sub_row = tiles_per_row * bytes_per_tile_x;

    // 32 rows with 16 tiles each draws the entirety of the tiles
    // which is 512 of them.
    int total_tiles = 512;
    int row_count = total_tiles / tiles_per_row;
    for (int row = 0; row < row_count; row++) {
        // Each row will be made up of 128 pixels going across,
        // where each pixel is 3 bytes. The row itself has sub rows
        // of 8 pixels each (as a result we get the 8x8 tiles).
        int start_offset = row * 8 * bytes_per_sub_row;
        for (int column = 0; column < tiles_per_row; column++) {
            int tile_index = column + row * tiles_per_row;
            Pattern& tile = ps[tile_index];
            for (int y = 0; y < 8; y++) {
                // Draw out all 8 rows of the tiles pixels. This involves jumping
                // row by row in the buffer quite a distance. We need to know
                // how many bytes are within a single row
                for (int x = 0; x < 8; x++) {
                    // 3 bytes per pixel. Each row is 128 pixels * 3 bytes per pixel.
                    int sub_row_offset = y * tiles_per_row * bytes_per_tile_x;
                    sub_row_offset += start_offset;
                    // x must be multiplied by 3 because each x value is 3 bytes
                    // worth of data. It also needs to be offset by which byte
                    // we're currently drawing for r, g, and b which is why 1 and
                    // 2 are added to it.
                    int x_offset = x * 3;
                    pt.data[x_offset + column * bytes_per_tile_x + sub_row_offset] = tile.data[y][x];
                    pt.data[x_offset + column * bytes_per_tile_x + sub_row_offset + 1] = tile.data[y][x];
                    pt.data[x_offset + column * bytes_per_tile_x + sub_row_offset + 2] = tile.data[y][x];
                }
            }
        }
    }
    return pt;
}

