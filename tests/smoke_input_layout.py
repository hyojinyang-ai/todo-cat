#!/usr/bin/env python3
"""Check long-input containment in the real WKWebView without changing app data."""
import json
from pathlib import Path
import threading
import time

from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
from Foundation import NSObject, NSURL
from PyObjCTools import AppHelper
from WebKit import WKWebView, WKWebViewConfiguration


ROOT = Path(__file__).resolve().parents[1]


class MessageSink(NSObject):
    def userContentController_didReceiveScriptMessage_(self, controller, message):
        pass


app = NSApplication.sharedApplication()
app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
sink = MessageSink.alloc().init()
conf = WKWebViewConfiguration.alloc().init()
conf.userContentController().addScriptMessageHandler_name_(sink, "app")
web = WKWebView.alloc().initWithFrame_configuration_(((0, 0), (300, 334)), conf)
web.loadFileURL_allowingReadAccessToURL_(
    NSURL.fileURLWithPath_(str(ROOT / "app" / "panel.html")),
    NSURL.fileURLWithPath_(str(ROOT)))
failures = []


def evaluate(code):
    completed = threading.Event()
    result = {}

    def callback(value, error):
        result.update(value=value, error=error)
        completed.set()

    AppHelper.callAfter(
        lambda: web.evaluateJavaScript_completionHandler_(code, callback))
    if not completed.wait(10):
        raise AssertionError("WebKit did not finish evaluating the layout check")
    if result["error"]:
        raise AssertionError(str(result["error"]))
    return result["value"]


CHECK = r"""
(() => {
    const errors = [];
    const row = document.getElementById("addrow");
    const input = document.getElementById("inp");
    const select = document.getElementById("catsel");
    const samples = ["A short task", "Long task ".repeat(80),
                     "x".repeat(1000), "\ud55c\uae00".repeat(200)];
    for (const lang of ["en", "ko"]) {
        select.replaceChildren();
        const category = document.createElement("option");
        category.textContent = lang === "en" ? "Personal Growth" : "\uac1c\uc778 \uc131\uc7a5";
        select.appendChild(category);
        input.placeholder = L[lang].inp;
        for (const text of samples) {
            input.value = text;
            input.focus();
            input.setSelectionRange(text.length, text.length);
            input.scrollLeft = input.scrollWidth;
            const box = row.getBoundingClientRect();
            const field = input.getBoundingClientRect();
            const categoryBox = select.getBoundingClientRect();
            const label = `${innerWidth}px ${lang} ${text.length} chars`;
            if (box.left < 0 || box.right > innerWidth ||
                field.right > box.right - 0.5 || field.left < categoryBox.right - 0.5 ||
                field.width < 40 || row.scrollWidth > row.clientWidth + 1 ||
                document.documentElement.scrollWidth > innerWidth + 1)
                errors.push(label + ": input escapes its row or viewport");
            if (input.value !== text)
                errors.push(label + ": input text was truncated");
            if (text.length > 100 && input.scrollLeft <= 0)
                errors.push(label + ": long text cannot scroll inside the input");
        }
    }
    return JSON.stringify(errors);
})()
"""


def scenario():
    try:
        deadline = time.monotonic() + 15
        while evaluate("document.readyState") != "complete":
            if time.monotonic() > deadline:
                raise AssertionError("panel.html did not finish loading")
            time.sleep(0.1)
        for width, height in ((300, 334), (336, 534), (560, 534), (300, 334)):
            resized = threading.Event()

            def resize(w=width, h=height):
                web.setFrame_(((0, 0), (w, h)))
                resized.set()

            AppHelper.callAfter(resize)
            if not resized.wait(10):
                raise AssertionError("WebKit did not resize")
            time.sleep(0.1)
            failures.extend(json.loads(evaluate(CHECK)))
    except Exception as error:
        failures.append(str(error))
    finally:
        AppHelper.callAfter(AppHelper.stopEventLoop)


threading.Thread(target=scenario, daemon=True).start()
AppHelper.runConsoleEventLoop()
if failures:
    raise SystemExit("\n".join(failures))
print("Input stays inside the panel and scrolls internally at all tested sizes.")
