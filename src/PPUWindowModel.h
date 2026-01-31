#import <Appkit/Appkit.h>
#import <Foundation/Foundation.h>
#import "PPU.h"

@interface PPUWindowModel : NSObject

@property NSString* ppuStatus;
@property uint8_t* patterns;
@property uint8_t* palettes;
@property NSMutableArray<NSColor*>* paletteColours;

- (void)updateData:(PPU*)ppu;

@end
