// Native private-use installer. No Python, Homebrew or shell automation is required.
#import <Cocoa/Cocoa.h>

static NSString *Join(NSString *a, NSString *b) { return [a stringByAppendingPathComponent:b]; }
static void Fail(NSString *message) { @throw [NSException exceptionWithName:@"InstallError" reason:message userInfo:nil]; }
static BOOL Panda(NSString *path) {
    NSDictionary *p = [NSDictionary dictionaryWithContentsOfFile:Join(path, @"Contents/Info.plist")];
    return [p[@"CFBundleExecutable"] isEqual:@"RedPandaIDE"] || [p[@"CFBundleIdentifier"] isEqual:@"net.redpanda-cpp.RedPandaIDE"];
}
static NSArray *FindApps(NSArray *roots, NSString *source) {
    NSMutableArray *found = [NSMutableArray array];
    NSFileManager *fm = NSFileManager.defaultManager;
    for (NSString *root in roots) {
        NSDirectoryEnumerator *walk = [fm enumeratorAtURL:[NSURL fileURLWithPath:root]
            includingPropertiesForKeys:@[NSURLIsSymbolicLinkKey, NSURLIsDirectoryKey]
            options:NSDirectoryEnumerationSkipsHiddenFiles errorHandler:^BOOL(NSURL *url, NSError *error) {
                // Unreadable directories cannot be certified free of old installations.
                NSLog(@"Not scanned: %@ (%@)", url.path, error.localizedDescription);
                return YES;
            }];
        for (NSURL *url in walk) {
            NSNumber *link, *dir;
            [url getResourceValue:&link forKey:NSURLIsSymbolicLinkKey error:nil];
            [url getResourceValue:&dir forKey:NSURLIsDirectoryKey error:nil];
            if (link.boolValue) { [walk skipDescendants]; continue; }
            if (!dir.boolValue) continue;
            if ([url.lastPathComponent isEqual:@"Library"]) { [walk skipDescendants]; continue; }
            if ([url.pathExtension.lowercaseString isEqual:@"app"]) {
                [walk skipDescendants];
                if (![url.path isEqual:source] && Panda(url.path) && ![found containsObject:url.path]) [found addObject:url.path];
            }
        }
    }
    return found;
}
static void Install(NSString *source, NSString *home, BOOL test) {
    NSFileManager *fm = NSFileManager.defaultManager;
    NSString *dest = Join(home, @"Applications/RedPandaIDE.app");
    if (!Panda(source)) Fail(@"安装包中的应用不存在或不完整。");
    if (!test) for (NSRunningApplication *app in NSWorkspace.sharedWorkspace.runningApplications) {
        if ([app.executableURL.lastPathComponent isEqual:@"RedPandaIDE"]) Fail(@"请保存代码并退出正在运行的 Red Panda C++，然后再次点击安装。");
    }
    if ([fm fileExistsAtPath:dest] && !Panda(dest)) Fail(@"安装位置存在其他文件，已停止安装以保护原有内容。");
    NSError *error = nil;
    if (![fm createDirectoryAtPath:Join(home, @"Applications") withIntermediateDirectories:YES attributes:nil error:&error]) Fail(error.localizedDescription);
    NSString *stage = Join(home, [@"Applications/.RedPanda-install-" stringByAppendingString:NSUUID.UUID.UUIDString]);
    if (![fm copyItemAtPath:source toPath:stage error:&error]) Fail(error.localizedDescription);
    NSMutableArray *moved = [NSMutableArray array];
    NSArray *roots = test ? @[home] : @[home, @"/Applications"];
    @try {
        for (NSString *old in FindApps(roots, source)) {
            NSURL *trashURL = nil;
            if (test) {
                NSString *trash = Join(home, @"Trash");
                [fm createDirectoryAtPath:trash withIntermediateDirectories:YES attributes:nil error:nil];
                trashURL = [NSURL fileURLWithPath:Join(trash, NSUUID.UUID.UUIDString)];
                if (![fm moveItemAtURL:[NSURL fileURLWithPath:old] toURL:trashURL error:&error]) Fail(error.localizedDescription);
            } else if (![fm trashItemAtURL:[NSURL fileURLWithPath:old] resultingItemURL:&trashURL error:&error]) {
                Fail([NSString stringWithFormat:@"无法将旧版本移到废纸篓：%@\n%@", old, error.localizedDescription]);
            }
            [moved addObject:@{@"from":old, @"to":trashURL.path}];
        }
        if (![fm moveItemAtPath:stage toPath:dest error:&error]) Fail(error.localizedDescription);
    } @catch (NSException *exception) {
        for (NSDictionary *item in moved.reverseObjectEnumerator) [fm moveItemAtPath:item[@"to"] toPath:item[@"from"] error:nil];
        [fm removeItemAtPath:stage error:nil];
        @throw exception;
    }
    NSString *settings = Join(home, @"Library/Application Support/Red Panda C++/redpandacpp.ini");
    [fm createDirectoryAtPath:settings.stringByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:nil];
    NSString *template = [NSString stringWithContentsOfFile:Join(dest, @"Contents/Resources/standalone.ini") encoding:NSUTF8StringEncoding error:&error];
    if (!template) Fail(error.localizedDescription);
    if ([fm fileExistsAtPath:settings]) {
        NSString *old = [NSString stringWithContentsOfFile:settings encoding:NSUTF8StringEncoding error:&error];
        if (!old) Fail(error.localizedDescription);
        NSString *backup = [settings stringByAppendingFormat:@".backup-%@", NSUUID.UUID.UUIDString];
        if (![fm copyItemAtPath:settings toPath:backup error:&error]) Fail(error.localizedDescription);
        NSMutableString *preserved = [NSMutableString string];
        BOOL compiler = NO;
        for (NSString *line in [old componentsSeparatedByCharactersInSet:NSCharacterSet.newlineCharacterSet]) {
            if ([line hasPrefix:@"["]) compiler = [line isEqual:@"[CompilerSets]"] || [line hasPrefix:@"[CompilerSet_"];
            if (!compiler) [preserved appendFormat:@"%@\n", line];
        }
        NSRange range = [template rangeOfString:@"[CompilerSets]"];
        template = [preserved stringByAppendingString:[template substringFromIndex:range.location]];
    }
    if (![template writeToFile:settings atomically:YES encoding:NSUTF8StringEncoding error:&error]) Fail(error.localizedDescription);
    NSData *manifest = [NSJSONSerialization dataWithJSONObject:moved options:NSJSONWritingPrettyPrinted error:nil];
    [manifest writeToFile:Join(settings.stringByDeletingLastPathComponent, @"last-install-moved-apps.json") atomically:YES];
}

@interface Installer : NSObject <NSApplicationDelegate>
@property NSWindow *window;
@property NSTextField *status;
@property NSButton *button;
@end
@implementation Installer
- (void)applicationDidFinishLaunching:(NSNotification *)note {
    self.window = [[NSWindow alloc] initWithContentRect:NSMakeRect(0,0,600,310) styleMask:NSWindowStyleMaskTitled|NSWindowStyleMaskClosable backing:NSBackingStoreBuffered defer:NO];
    self.window.title = @"Red Panda C++ · Apple Silicon 安装器";
    self.status = [NSTextField wrappingLabelWithString:@"将安装到 ~/Applications/RedPandaIDE.app\n\n包含 GCC 15、万能头文件、LLDB 调试器和开发工具。\n保留个人设置，旧版本移到废纸篓；请先保存代码并退出 IDE。\n\n仅供本人控制的 Mac 自用；此包未经过 Apple 公证。\n当前版本要求 Apple 芯片、macOS 26 或更新版本。"];
    self.status.frame = NSMakeRect(30,85,540,195);
    [self.window.contentView addSubview:self.status];
    self.button = [NSButton buttonWithTitle:@"安装 / 更新" target:self action:@selector(install:)];
    self.button.frame = NSMakeRect(415,25,155,40);
    self.button.bezelStyle = NSBezelStyleRounded;
    [self.window.contentView addSubview:self.button];
    [self.window center]; [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
}
- (void)install:(id)sender {
    self.button.enabled = NO; self.status.stringValue = @"正在复制应用、迁移设置和清理旧版本，请稍候……";
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0), ^{
        NSString *problem = nil;
        @try { Install(Join(NSBundle.mainBundle.resourcePath, @"RedPandaIDE.app"), NSHomeDirectory(), NO); }
        @catch (NSException *e) { problem = e.reason; }
        dispatch_async(dispatch_get_main_queue(), ^{
            self.button.enabled = YES;
            if (problem) { self.status.stringValue = problem; return; }
            self.status.stringValue = @"安装完成！\n\n已安装到用户的“应用程序”目录。旧版应用已移到废纸篓。\n\n若 macOS 拦截首次启动，请到“系统设置 → 隐私与安全”选择“仍要打开”。\n首次调试可能需要开发者授权，详见磁盘映像中的说明。";
            self.button.title = @"打开 Red Panda C++";
            self.button.action = @selector(launch:);
        });
    });
}
- (void)launch:(id)sender {
    NSURL *url = [NSURL fileURLWithPath:Join(NSHomeDirectory(), @"Applications/RedPandaIDE.app")];
    [NSWorkspace.sharedWorkspace openApplicationAtURL:url configuration:NSWorkspaceOpenConfiguration.configuration completionHandler:nil];
}
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender { return YES; }
@end
int main(int argc, const char **argv) {
    @autoreleasepool {
        if (argc == 4 && !strcmp(argv[1], "--test-install")) {
            @try { Install(@(argv[2]), @(argv[3]), YES); return 0; }
            @catch (NSException *e) { fprintf(stderr, "%s\n", e.reason.UTF8String); return 1; }
        }
        NSApplication *app = NSApplication.sharedApplication;
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        Installer *delegate = [Installer new]; app.delegate = delegate; [app run];
    }
    return 0;
}
