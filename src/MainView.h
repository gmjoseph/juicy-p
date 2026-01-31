#import <Appkit/Appkit.h>
#import <Foundation/Foundation.h>

@protocol MainViewDelegate <NSObject>
@optional
- (void)handleKeyEvent:(NSEvent*)event;
@end

@interface MainView : NSView

@property (nonatomic, weak) id <MainViewDelegate> delegate;

@end
