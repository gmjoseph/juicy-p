#import <Appkit/Appkit.h>
#import <Foundation/Foundation.h>
#import "NES.h"
#import "MainView.h"
#import "PPUWindow.h"

@interface AppDelegate : NSObject <NSApplicationDelegate, NSWindowDelegate, MainViewDelegate>

@property NSWindow* window;
@property PPUWindow* ppuWindow;
@property MainView* mainView;
@property NES* nes;
@property NSThread* nesThread;
@property Boolean paused;

@end
