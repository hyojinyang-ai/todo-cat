#!/usr/bin/env python3
"""Synthesise loaf frames (loaf1..loaf8 + _flip) for a cat from its sitting image.
The cat eases down into a compact loaf: lower, a little wider, feet anchored.
Usage: python3 tools/mkloaf.py <cat-folder>   (e.g. assets/pets/sprout)
Replace with hand-drawn frames any time — same file names."""
import sys, math
from pathlib import Path
from AppKit import (NSImage, NSBitmapImageRep, NSGraphicsContext, NSColor,
                    NSCompositingOperationSourceOver, NSRectFill, NSAffineTransform,
                    NSBitmapImageFileTypePNG, NSCalibratedRGBColorSpace)
from Foundation import NSMakeRect

if len(sys.argv) < 2:
    sys.exit(__doc__)
folder = Path(sys.argv[1]).expanduser()
src = NSImage.alloc().initWithContentsOfFile_(str(folder / "cat.png"))
W, H = int(src.size().width), int(src.size().height)
FRAMES = 8

def ease(t):                       # ease-in-out
    return 0.5 - 0.5 * math.cos(math.pi * t)

def render(scale_x, scale_y, flip, out):
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, W, H, 8, 4, True, False, NSCalibratedRGBColorSpace, 0, 0)
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.setCurrentContext_(ctx)
    NSColor.clearColor().setFill(); NSRectFill(NSMakeRect(0, 0, W, H))
    if flip:
        t = NSAffineTransform.transform(); t.translateXBy_yBy_(W, 0); t.scaleXBy_yBy_(-1, 1); t.concat()
    dw, dh = W * scale_x, H * scale_y            # anchored at the bottom, centred horizontally
    src.drawInRect_fromRect_operation_fraction_(
        NSMakeRect((W - dw) / 2, 0, dw, dh), NSMakeRect(0, 0, W, H),
        NSCompositingOperationSourceOver, 1.0)
    NSGraphicsContext.restoreGraphicsState()
    rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, None).writeToFile_atomically_(str(out), True)

for i in range(1, FRAMES + 1):
    t = ease(i / FRAMES)
    sy = 1.0 - 0.30 * t                          # settle to 70 % height
    sx = 1.0 + 0.14 * t                          # spread to 114 % width
    render(sx, sy, False, folder / f"loaf{i}.png")
    render(sx, sy, True, folder / f"loaf{i}_flip.png")
print(f"wrote {FRAMES*2} loaf frames to {folder}")
