#ifndef PPU_DEBUG
#define PPU_DEBUG

#include <vector>

// 512 patterns (laid out in the dimension 128 x 256), each is
// 64 x 64 pixels and each pixel requires 3 bytes for RGB.
static const int PATTERN_TABLE_WIDTH = 128;
static const int PATTERN_TABLE_HEIGHT = 256;
static const int PATTERN_TABLE_BUFFER_SIZE =
    PATTERN_TABLE_WIDTH * PATTERN_TABLE_HEIGHT * 3;

class PPU;

// TODO
// Structure per thing we wanna draw that can then be consumed
// for example a Patterns struct with the data prefilled.
// Same can be applied to the sprites by using PPUUtils and then
// just colouring in the bits that come back from _pixel_bits_for_sprite


// A completely renderable data dump of the pattern table after running
// through patterns().
struct PatternTable {
    uint8_t data[PATTERN_TABLE_BUFFER_SIZE] = {};
};

PatternTable pattern_table(PPU*);

#endif
