#import <string>
#import "AppDelegate.h"
#import "Constants.h"
#import "MainView.h"
#import "NES.h"
#import "PPUWindow.h"

@implementation AppDelegate {
    NES* _nes;
}

- (id)init {
    if (self = [super init]) {
        // TODO
        // Leak this for now, it runs for the duration of the program
        // anyways.
        std::string filepath = "../roms/donkey_kong/donkey_kong.nes";
        self.nes = new NES(filepath);

        NSRect contentSize = NSMakeRect(0, 0, 256, 240);
        NSUInteger windowStyleMask = NSWindowStyleMaskTitled | NSWindowStyleMaskResizable | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable;
        // For no title, border, close buttons etc.
        // NSUinteger windowStyleMask = NSWindowStyleMaskBorderless;
        self.window = [[NSWindow alloc] initWithContentRect:contentSize
                    styleMask:windowStyleMask
                    backing:NSBackingStoreBuffered
                    defer:NO];
        [self.window setDelegate:self];
        [self.window setBackgroundColor:[NSColor blueColor]];
        [self.window makeKeyAndOrderFront:NSApp];
        [self.window setTitle:@"JUICY"];

        [self createMenu];
        // Create a view
        self.mainView = [[MainView alloc] initWithFrame:CGRectMake(0, 0, 256, 240)];
        self.mainView.delegate = self;
    }
    return self;
}

- (void)dealloc {
    [self.nesThread cancel];
    // Release the display link
    // CVDisplayLinkRelease(displayLink);
    delete self.nes;
}

# pragma mark - Menu Setup

- (void)createMenu {
    // https://blog.rachelbrindle.com/2015/08/14/osx-programming-programmatic-menu-buttons/
    // Notice one menuItem them menu them menuItem. The first menuItem
    // is what is part of the menu bar at the top. They are the clickable
    // buttons. The menu is then added to each of those menuItems.
    // Finally the last menuItem is the button seen when the menu
    // is expanded.

    // Main Menu
    NSMenu* menu = [[NSMenu alloc] init];
    NSMenuItem* menuItem = [[NSMenuItem alloc] init];
    [menu addItem:menuItem];
    [NSApp setMainMenu:menu];
    NSMenu* submenu = [[NSMenu alloc] init];
    NSMenuItem* quitMenuItem = [[NSMenuItem alloc] initWithTitle:@"Quit"
                                                   action:@selector(terminate:)
                                                   keyEquivalent:@"q"];
    [submenu addItem:quitMenuItem];
    [menuItem setSubmenu:submenu];

    // Debug Menu
    NSMenuItem* debug = [[NSMenuItem alloc] init];
    [debug setTitle:@"Debug"];
    NSMenu* debugMenu = [[NSMenu alloc] initWithTitle:@"Debug"];
    // Each row in the debug sub menu.
    NSMenuItem* palettes = [[NSMenuItem alloc] initWithTitle:@"PPU"
                                               action:@selector(handleDebug:)
                                               keyEquivalent:@"p"];
    NSMenuItem* patternTables = [[NSMenuItem alloc] initWithTitle:@"Pattern Tables"
                                                    action:@selector(handleDebug:)
                                                    keyEquivalent:@"r"];                                            

    [debugMenu addItem:palettes];
    [debugMenu addItem:patternTables];
    [debug setSubmenu:debugMenu];
    [menu addItem:debug];
}

- (void)createToolbar {
    NSToolbar* mainToolbar = [[NSToolbar alloc] initWithIdentifier:@"mainToolbar"];
    [self.window setToolbar:mainToolbar];
}

# pragma mark - NSApplicationDelegate

- (void)applicationWillFinishLaunching:(NSNotification*)notification {
    [self.window setContentView:self.mainView];
    [self.window makeKeyAndOrderFront:self];
}

# pragma mark - NES

- (void)drawPixels {
    // https://stackoverflow.com/questions/24442017/fast-alternative-to-drawinrect
    // https://stackoverflow.com/questions/12799920/drawing-on-nsbitmapimagerep
    // size_t width = self.window.contentView.bounds.size.width;
    // size_t height = self.window.contentView.bounds.size.height;
    size_t width = 256;
    size_t height = 240;
    // RGB * 1 byte per colour * width.
    uint8_t pixelSize = sizeof(uint8_t) * 3;
    uint32_t bytesPerRow = pixelSize * width;
    uint8_t* buffer = self.nes->ppu.renderer.pixels;
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
    self.window.contentView.wantsLayer = YES;
    self.window.contentView.layer.contents = image;
    [self.window.contentView setNeedsDisplay:YES];
}

- (void)applicationDidFinishLaunching:(NSNotification*)notification {
    self.nesThread = [[NSThread alloc] initWithTarget:self
                                             selector:@selector(runNES)
                                             object:nil];
    [self.nesThread start];
}

// TODO
// I don't think we want this because the NES computes frames and the CVDisplayLink
// would run at maximum at 60 fps but the NES can run faster than that (and can also
// compute frames faster than that).
// Maybe the architecture is kind of wonky in that this should use the display link
// and then the NES computes the entire frame within the call for the display link
// by running until it has a new frame?
// // Display Link to drive running the NES.
// // https://developer.apple.com/library/archive/qa/qa1385/_index.html
// // https://developer.apple.com/documentation/corevideo/cvdisplaylink?language=objc
// // https://stackoverflow.com/questions/53772889/how-to-start-gos-main-function-from-within-the-nsapplication-event-loop
// // https://stackoverflow.com/questions/6649664/cocoa-message-loop-vs-windows-message-loop
- (void)runNES {
    // TODO
    // Pause the thread instead of running it but skipping the
    // most intensive part.
    // https://stackoverflow.com/questions/9916053/ios-objective-c-how-to-stop-nsthread-when-its-waiting
    uint64_t last_frame = 0;
    while (1) {
        if (self.paused) {
            continue;
        }
        self.nes->run();
        if (self.nes->ppu.frames > last_frame) {
            last_frame = self.nes->ppu.frames;
            // May need to make this YES in case we change out pixel
            // data underneath the update? That could be ok though.
            [self performSelectorOnMainThread:@selector(drawPixels)
                                   withObject:nil
                                waitUntilDone:NO];
        }
    }
}

# pragma mark - MainViewDelegate

- (void)handleKeyEvent:(NSEvent*)event {
    uint16_t code = [event keyCode];
    // NSString* chars = [event characters];
    // if ([chars isEqual:@"p"]) {
    //     [self handlePaused:!self.paused];
    // }
    switch (code) {
        // TODO
        // Support configurable key mapping in future.
        case 0: // a
        case 123: // left arrow
            self.nes->handle_input(Input::LEFT); return;
        case 1: // s
        case 125: // down arrow
            self.nes->handle_input(Input::DOWN); return;
        case 2: // d
        case 124: // right arrow
            self.nes->handle_input(Input::RIGHT); return;
        case 13: // w
        case 126: // up arrow
            self.nes->handle_input(Input::UP); return;
        case 36: // enter
            self.nes->handle_input(Input::SELECT); return;
        case 49: // space
            self.nes->handle_input(Input::START); return;
        case 47: // .
        case 30: // ]
            self.nes->handle_input(Input::B); return;
        case 44: // /
        case 42: // \/
            self.nes->handle_input(Input::A); return;
        case 35: // p
            [self handlePaused:!self.paused]; return;
    }
}

# pragma mark - Handlers

- (void)handleDebug:(id)action {
    if ([[action title] isEqual:@"PPU"]) {
        // FIXME
        // There's probably a race condition here.
        // Pause while debugging, the one issue here is that while we're
        // reading the state the other thread may still be executing, so
        // this may need a more precise synchronization mechanism?
        // One way is to break this up into "pauseRequested" and "paused"
        // states, where paused is set from the other thread after it's
        // handled a pauseRequested.
        [self handlePaused:YES];
        // FIXME
        // Only do one. However this one window can be closed which
        // will result in losing the reference i think?
        if (self.ppuWindow == nil) {
            self.ppuWindow = [[PPUWindow alloc] init];
        }
        [self.ppuWindow makeKeyAndOrderFront:self];
        [self.ppuWindow.model updateData:&(self.nes->ppu)];
        [self.ppuWindow updateViews];
    }
    // NSLog(@"%@", action);
}

- (void)handlePaused:(BOOL)paused {
    self.paused = paused;
    if (paused) {
        [self.window setTitle:@"JUICY (paused)"];
    } else {
        [self.window setTitle:@"JUICY"];
    }
}

@end
