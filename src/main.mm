#import <Cocoa/Cocoa.h>
#import "AppDelegate.h"

int
main(int argc, const char* argv[]) {
    NSApplication* application = [NSApplication sharedApplication];
    AppDelegate* applicationDelegate = [[AppDelegate alloc] init];
    [application setDelegate:applicationDelegate];
    // Required for the application to get its Menu and to allow
    // it to be tabbed to.
    // "In Snow Leopard, programs without application bundles and
    // Info.plist files don't get a menubar and can't be brought
    // to the front unless the presentation option is changed"
    [application setActivationPolicy:NSApplicationActivationPolicyRegular];
    [application activateIgnoringOtherApps:YES];
    // Main loop.
    [application run];
    return 0;
}
