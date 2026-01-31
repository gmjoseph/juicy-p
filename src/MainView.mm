#import "MainView.h"

@implementation MainView

// https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CocoaViewsGuide/Introduction/Introduction.html#//apple_ref/doc/uid/TP40002978
// Event Handling
// https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/EventOverview/EventHandlingBasics/EventHandlingBasics.html
// https://developer.apple.com/documentation/appkit/nsapplication/1428485-nexteventmatchingmask?language=objc
- (BOOL)acceptsFirstResponder {
    return YES;
}

- (void)keyDown:(NSEvent*)theEvent {
    if (self.delegate) {
        [self.delegate handleKeyEvent:theEvent];
    }
    // If the event wasn't handled pass it up.
    [super keyDown:theEvent];
}

- (void)mouseDown:(NSEvent *)theEvent {
    // NSLog(@"%@", theEvent);
    // If the event wasn't handled pass it up.
    [super mouseDown:theEvent];
}

@end
