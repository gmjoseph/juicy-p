#import <Appkit/Appkit.h>
#import "PPUWindowModel.h"

@interface PPUWindow : NSWindow <NSWindowDelegate>

@property NSTextView* textView;
@property NSView* togglesView;
@property NSView* patternsView;
@property NSView* palettesView;
@property PPUWindowModel* model;

- (void)updateViews;

@end
