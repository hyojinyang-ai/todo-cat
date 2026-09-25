# Pitfalls (each one was hit for real)

## Deploy
- **Stale process wins**: single-instance guard makes a new launch exit if `panel.pid` points to a live process. Always `pkill -f panel.py; rm panel.pid` before `launchctl kickstart`. Symptom: "I changed it but nothing changed".
- Re-signing the bundle (`codesign`) may re-prompt calendar permission; tell the user to allow again.
- Old instances started by `open` or a terminal are **not** under launchd; they survive `kickstart -k`.

## macOS permissions (TCC)
- Calendar access needs `NSCalendarsFullAccessUsageDescription` in an app bundle. Plain `python3` is denied silently (status stays 0 = notDetermined).
- TCC attributes the request to the *responsible process*. Requests from a process spawned by Terminal or Claude Desktop are silently denied. Only test permission flows through the launchd-run bundle (click **[일정 소스 다시 확인]** in the panel).
- `exec` into a binary outside the bundle strips the bundle identity → keep `To-Do-bin` inside `Contents/MacOS`.
- Dock launches the executable with **no arguments** → the executable must be a wrapper that supplies `panel.py`.
- Graph API device-code login can be blocked by corporate Conditional Access (AADSTS 53003, unregistered device). Use Exchange in macOS Calendar + EventKit, or an ICS publish URL.

## Windows
- `hidesOnDeactivate` defaults True for NSPanel → set False or the window vanishes.
- WKWebView swallows drags → leave a native strip (inset the webview) for moving the window.
- Close button is disabled unless `NSWindowStyleMaskClosable` is in the mask.
- Pet must be `NSFloatingWindowLevel + 1` or the panel covers its feet when clicked.
- Two displays: compute pet position from the panel's frame and clamp to that screen's `visibleFrame`; first spawn on "main screen" was invisible to the user.

## Images
- **Palette (P-mode) PNG loses alpha on macOS** → fully transparent or fully opaque. Always RGBA. If shrinking size, quantize RGB only and re-attach the original alpha.
- **macOS NSImage ignores SVG fills** (renders silhouettes). Do not load SVG with NSImage; draw with NSBezierPath or use PNG. (Obsidian renders SVG fine — the heatmap is SVG on purpose.)
- `lockFocus` → TIFF → PNG produced misaligned/noisy pixels once; the reliable path is `NSBitmapImageRep` + `setColor_atX_y_` / drawing into `NSGraphicsContext.graphicsContextWithBitmapImageRep_`.
- Base64 through chat corrupted files twice (alpha loss, duplicated payload). Use files already on the Mac (`~/Downloads`).
- Verify visually: composite on a checkerboard, `sips -Z 700`, `read_file`. Tool results over ~1 MB are rejected.
- Coordinates: SVG/PIL are y-down, AppKit is y-up (`y' = H - y`). Retina `lockFocus` produces 2× pixel reps (`pixelsWide` ≠ `size()`).

## pyobjc
- **Any Python exception inside an ObjC callback (WKScriptMessageHandler, menu actions, delegates) aborts the process** with SIGABRT and *no traceback in the log* — the crash report shows `PyObjCErr_ToObjCWithGILState → objc_exception_throw → abort`. Keep callbacks wrapped in try/except that logs `traceback.print_exc()`; reproduce suspected handlers by calling them directly from a script with a fake `msg.body()`.
- Method names on NSObject subclasses encode arity with trailing underscores: `runjs_(self, code)`. A 1-arg method without `_` raises BadPrototypeError at class creation.
- Draw/UI calls must run on the main thread: wrap with `AppHelper.callAfter`.

## HTML/JS
- `hidden` attribute loses to an explicit `display:flex` on the same element → add `[hidden]{display:none!important}`.
- Adding `L` strings: anchor on the **last existing key** of each language object and add to both ko and en, or labels show `undefined`.
