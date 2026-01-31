#import "PPUWindowModel.h"
#import "PPUDebug.h"
#import "Palettes.h"
#import <stdint.h>

@implementation PPUWindowModel

- (id)init {
    if (self = [super init]) {
        self.patterns = (uint8_t*)malloc(PATTERN_TABLE_BUFFER_SIZE);
        // 8 palettes, 4 colours per palette, RGB values per colour.
        self.palettes = (uint8_t*)malloc(8 * 4 * 3);
        self.paletteColours = [[NSMutableArray alloc] init];
    }
    return self;
}

- (void)updateData:(PPU*)ppu {
    [self updatePPUStatus:ppu];
    [self updatePatterns:ppu];
    [self updatePalettes:ppu];
}

- (void)updatePPUStatus:(PPU*)ppu {
        // TODO
    // Implement some kind of data provider that provides all this
    // stuff in a consistent interface so we don't have to wrangle data
    // separately, just convert it.


    // NSLog(@"Need to update %p", ppu);
    self.ppuStatus = [NSString stringWithFormat:@"PPU: %p\n"
                                                 "Frames: %llu\n"
                                                 "Scanline: %d\n"
                                                 "Pixel: x %d y %d\n"
                                                 "Cycle: %llu\n"
                                                 "\n"
                                                 "BG Palette 1 %x\n"
                                                 "BG Palette 2 %x\n"
                                                 "BG Palette 3 %x\n"
                                                 "BG Palette 4 %x\n"
                                                 "Sprite Palette 1 %x\n"
                                                 "Sprite Palette 2 %x\n"
                                                 "Sprite Palette 3 %x\n"
                                                // Comma must be on lthe last for string concat.
                                                 "Sprite Palette 4 %x\n",
                                                 ppu,
                                                 ppu->frames,
                                                 ppu->scanline,
                                                 ppu->x(),
                                                 ppu->y(),
                                                 ppu->clock.ppu_cycles,
                                                 ppu->memory.background_palette(0),
                                                 ppu->memory.background_palette(1),
                                                 ppu->memory.background_palette(2),
                                                 ppu->memory.background_palette(3),
                                                 ppu->memory.sprite_palette(0),
                                                 ppu->memory.sprite_palette(1),
                                                 ppu->memory.sprite_palette(2),
                                                 ppu->memory.sprite_palette(3)];
}

- (void)updatePatterns:(PPU*)ppu {
    PatternTable pt = pattern_table(ppu);
    memcpy(self.patterns, pt.data, PATTERN_TABLE_BUFFER_SIZE);
}

- (void)updatePalettes:(PPU*)ppu {
    // TODO
    // Move this to Constants.h
    uint8_t paletteCount = 8;
    uint8_t coloursPerPalette = 4;
    uint8_t bytesPerColour = 3;

    for (int i = 0; i < paletteCount; i++) {
        uint32_t palette = 0;
        if (i < 4) {
            palette = ppu->memory.background_palette(i);
        } else {
            palette = ppu->memory.sprite_palette(i - 4);
        }
        uint8_t* p_palette = (uint8_t*)(&palette);
        // Each colour in the palette. There are four of them.
        for (int j = 0; j < coloursPerPalette; j++) {
            // 4 * 3 because there are 4 colours per palette with
            // 3 byte values each (RGB). We also need to account
            // for that in the j value.
            uint8_t output_index = i * coloursPerPalette * bytesPerColour;
            output_index += j * bytesPerColour;
            // printf("output index %d\n", output_index);
            // printf("\t r %d\n", output_index + 0);
            // printf("\t g %d\n", output_index + 1);
            // printf("\t b %d\n", output_index + 2);
            self.palettes[output_index + 0] = LUT[p_palette[j]][0];
            self.palettes[output_index + 1] = LUT[p_palette[j]][1];
            self.palettes[output_index + 2] = LUT[p_palette[j]][2];
        }
    }

    // Clear existing since we'll override them.
    [self.paletteColours removeAllObjects];
    // If we need to iterate over the palettes again and
    // get their colours
    uint8_t total_bytes = paletteCount * coloursPerPalette * bytesPerColour;
    for (int i = 0; i < total_bytes; i += bytesPerColour) {
        // TODO
        // Could be moved into the loop above.
        CGFloat r = (float)self.palettes[i] / 255.0;
        CGFloat g = (float)self.palettes[i + 1] / 255.0;
        CGFloat b = (float)self.palettes[i + 2] / 255.0;
        NSColor* colour = [NSColor colorWithRed:r
                                          green:g
                                           blue:b
                                          alpha:1.0];
        [self.paletteColours addObject:colour];
    }
}

@end
