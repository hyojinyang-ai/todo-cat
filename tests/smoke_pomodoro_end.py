#!/usr/bin/env python3
"""Smoke test: a Pomodoro work session finishing must not crash the app.
Loads the real panel.html into a real WKWebView with the real Bridge, forces the
timer to end in ~2 s (fires pomo_done + pomo_title through WebKit → pyobjc), then exits.
Exit code 0 = survived, 134/SIGABRT = the old crash."""
import sys, threading, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import panel
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
from Foundation import NSURL
from WebKit import WKWebView, WKWebViewConfiguration
from PyObjCTools import AppHelper

app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
bridge = panel.Bridge.alloc().init()
conf = WKWebViewConfiguration.alloc().init()
conf.userContentController().addScriptMessageHandler_name_(bridge, "app")
web = WKWebView.alloc().initWithFrame_configuration_(((0, 0), (320, 500)), conf)
bridge.webview = web
web.loadFileURL_allowingReadAccessToURL_(
    NSURL.fileURLWithPath_(str(panel.HTML)), NSURL.fileURLWithPath_(str(panel.ROOT)))

def js(code):
    AppHelper.callAfter(lambda: web.evaluateJavaScript_completionHandler_(code, None))

def scenario():
    time.sleep(2.0)                     # let the page load and render(state)
    print("[test] finishing a WORK session in 2 s …")
    js('P.mode="work";P.rem=2;pstartgo();')
    time.sleep(4.0)                     # pomo_done(work) → break auto-starts
    print("[test] finishing the BREAK in 2 s …")
    js('P.rem=2;')
    time.sleep(4.0)                     # pomo_done(break)
    print("[test] still alive after both completions ✅")
    AppHelper.callAfter(lambda: app.terminate_(None))

threading.Thread(target=scenario, daemon=True).start()
AppHelper.runEventLoop()
