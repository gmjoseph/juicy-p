#import "PPUWindow.h"

@implementation PPUWindow

// For a HexEditor / viewer
// http://spec-zone.ru/RU/OSX/samplecode/TextEdit/Listings/DocumentWindowController_m.html
// with
// https://developer.apple.com/documentation/uikit/nslayoutmanager?language=objc

// For most of the UI widgets
// https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CocoaViewsGuide/WhatAreViews/WhatAreViews.html#//apple_ref/doc/uid/TP40002978-CH5-SW1
// https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ControlCell/ControlCell.html
// https://developer.apple.com/documentation/appkit/views_and_controls?language=objc
// https://www.raywenderlich.com/2782-core-controls-in-mac-os-x-part-1-2
// https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/TableView/TableViewOverview/TableViewOverview.html#//apple_ref/doc/uid/10000026i-CH2-SW1

// Layout:
// https://www.hackingwithswift.com/articles/140/the-auto-layout-cheat-sheet
// https://github.com/PureLayout/PureLayout
// https://books.google.com/books?id=e35JCAAAQBAJ&pg=PT881&lpg=PT881&dq=osx+programmatic+layout&source=bl&ots=VGVulqLpH4&sig=ACfU3U2i-Uv2b7gRYER8JaFbTt1AIAJeWQ&hl=en&sa=X&ved=2ahUKEwj42vnp0pjpAhXzOX0KHeFtA10Q6AEwCHoECAoQAQ#v=onepage&q=osx%20programmatic%20layout&f=false
// https://www.avanderlee.com/swift/auto-layout-programmatically/
// https://stackoverflow.com/questions/31651022/how-to-create-layout-constraints-programmatically

// Laying out text:
// https://developer.apple.com/documentation/uikit/nslayoutmanager?language=objc

// Scrollview for hex editor?
// https://developer.apple.com/documentation/appkit/nsscrollview?language=objc

- (id)init {
    NSRect contentSize = NSMakeRect(0, 0, 2000, 1000);
    NSUInteger windowStyleMask = NSWindowStyleMaskTitled | NSWindowStyleMaskResizable | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable;
    // For no title, border, close buttons etc.
    // NSUinteger windowStyleMask = NSWindowStyleMaskBorderless;
    self = [super initWithContentRect:contentSize
                  styleMask:windowStyleMask
                  backing:NSBackingStoreBuffered
                  defer:NO];
    if (self) {
        self.model = [[PPUWindowModel alloc] init];
        [self setBackgroundColor:[NSColor blueColor]];
        [self makeKeyAndOrderFront:NSApp];
        [self setTitle:@"Palettes"];
        [self setDelegate:self];
        [self setContentView:[[NSView alloc] initWithFrame:contentSize]];
        [self setupTextView];
        [self setupTogglesView];
        [self setupPatternsView];
        [self setupPalettesView];
    }

    return self;
}

- (void)setupTextView {
    // Top left.
    self.textView = [[NSTextView alloc] initWithFrame:CGRectMake(0, 500, 500, 500)];
    [self.contentView addSubview:self.textView];
}

- (void)setupTogglesView {
    // Top right.
    self.togglesView = [[NSView alloc] initWithFrame:CGRectMake(500, 500, 500, 500)];
    self.togglesView.wantsLayer = YES;
    self.togglesView.layer.backgroundColor = [[NSColor redColor] CGColor];
    [self.contentView addSubview:self.togglesView];
    [self.togglesView setNeedsDisplay:YES];
}

- (void)setupPatternsView {
    // Bottom right.
    self.patternsView = [[NSView alloc] initWithFrame:CGRectMake(0, 0, 256, 512)];
    self.patternsView.wantsLayer = YES;
    self.patternsView.layer.backgroundColor = [[NSColor greenColor] CGColor];
    [self.contentView addSubview:self.patternsView];
    [self.patternsView setNeedsDisplay:YES];
}

- (void)setupPalettesView {
    self.palettesView = [[NSView alloc] initWithFrame:CGRectMake(1000, 500, 500, 500)];
    self.palettesView.wantsLayer = YES;
    self.palettesView.layer.backgroundColor = [[NSColor purpleColor] CGColor];
    [self.contentView addSubview:self.palettesView];
    [self.palettesView setNeedsDisplay:YES];

    // A swatch for each palette colour. We can use something
    // better for colours in future.
    for (int y = 0; y < 2; y++) {
        for (int x = 0; x < 16; x++) {
            NSView* palette = [[NSView alloc] initWithFrame:CGRectMake(x * 30,  y * 30, 30, 30)];
            palette.wantsLayer = YES;
            NSColor* colour = nil;
            if (x % 2 == 0) {
                colour = [NSColor blackColor];
            } else {
                colour = [NSColor purpleColor];
            }
            palette.layer.backgroundColor = [colour CGColor];
            [self.palettesView addSubview:palette];
            [palette setNeedsDisplay:YES];
        }
    }
}

- (void)updateViews {
    // NSLog(@"Need to update %p", ppu);
    self.textView.string = self.model.ppuStatus;
    [self updatePatternsView];
    [self updatePalettesView];
}

- (void)updatePatternsView {
    size_t width = 128;
    size_t height = 256;
    // RGB * 1 byte per colour * width.
    uint8_t pixelSize = sizeof(uint8_t) * 3;
    uint32_t bytesPerRow = pixelSize * width;
    uint8_t* buffer = self.model.patterns;
    // TODO
    // The buffer isn't RGB yet.
    NSBitmapImageRep* rep = [[NSBitmapImageRep alloc] initWithBitmapDataPlanes:&buffer
                                                      pixelsWide:width
                                                      pixelsHigh:height
                                                      bitsPerSample:8
                                                      // 3 * 8 = 24 bits because we have 3 byte pixels.
                                                      samplesPerPixel:3
                                                      // No Alpha channel for this, maybe in future?
                                                      hasAlpha:NO
                                                      isPlanar:NO
                                                      colorSpaceName:NSDeviceRGBColorSpace
                                                      bytesPerRow:bytesPerRow
                                                      bitsPerPixel:pixelSize * 8];
    NSImage* image = [[NSImage alloc] initWithSize:NSMakeSize(width, height)];
    [image addRepresentation:rep];
    self.patternsView.layer.contents = image;
    [self.patternsView setNeedsDisplay:YES];
}

- (void)updatePalettesView {
    // 32 = 8 palettes, 4 colours per palette.
    for (int i = 0; i < 32; i++) {
        NSView* palette = self.palettesView.subviews[i];
        NSColor* colour = self.model.paletteColours[i];
        palette.layer.backgroundColor = [colour CGColor];
    }
}

@end
