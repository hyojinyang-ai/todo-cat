from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
import panel


class Window:
    def __init__(self, x=140, y=360, width=160, height=108):
        self.rect = panel.NSMakeRect(x, y, width, height)
        self.visible = True
        self.miniaturized = False
        self.children = []
        self.level_value = panel.NSNormalWindowLevel
        self.autosave = "catPet3"
        self.draggable = True

    def frame(self):
        return self.rect

    def frameAutosaveName(self):
        return self.autosave

    def setFrameAutosaveName_(self, name):
        self.autosave = name

    def setFrameOrigin_(self, origin):
        self.rect = panel.NSMakeRect(
            origin[0], origin[1], self.rect.size.width, self.rect.size.height)

    def screen(self):
        return self

    def visibleFrame(self):
        return panel.NSMakeRect(-1440, 60, 1440, 840)

    def isVisible(self):
        return self.visible

    def isMiniaturized(self):
        return self.miniaturized

    def orderOut_(self, sender):
        self.visible = False
        for child in self.children:
            child.visible = False

    def orderFrontRegardless(self):
        self.visible = True

    def makeKeyAndOrderFront_(self, sender):
        self.visible = True
        for child in self.children:
            child.visible = True

    def deminiaturize_(self, sender):
        self.miniaturized = False
        self.makeKeyAndOrderFront_(sender)

    def removeChildWindow_(self, child):
        self.children.remove(child)

    def addChildWindow_ordered_(self, child, order):
        self.children.append(child)

    def level(self):
        return self.level_value

    def setLevel_(self, level):
        self.level_value = level

    def setMovableByWindowBackground_(self, enabled):
        self.draggable = enabled


class SproutParkingTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "pet_enabled": True, "pets": ["sprout", "ham"], "pet_walk": True}
        for target, replacement in (
                ("get_settings", lambda: self.settings),
                ("cached_events", lambda: []),
                ("AppHelper.callAfter", lambda fn, *args: fn(*args))):
            patcher = patch("panel." + target, replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.bridge = panel.Bridge.alloc().init()
        self.bridge.panel = Window()
        self.view = Mock()
        self.images = {"idle": object(), "parked": object(), "happy": object()}
        self.sprout = panel.Pet("sprout", Window(), self.view, self.images)
        self.other = panel.Pet("ham", Window(), Mock(), {"idle": object()})
        self.bridge.pets = [self.sprout, self.other]
        self.bridge.panel.children = [self.sprout.win, self.other.win]
        self.delegate = panel.AppDelegate.alloc().init()
        self.delegate.panel = self.bridge.panel
        self.delegate.bridge = self.bridge
        self.origin = (self.sprout.win.frame().origin.x,
                       self.sprout.win.frame().origin.y)

    def test_close_parks_only_sprout_above_the_dock(self):
        self.sprout.timer = Mock()
        timer = self.sprout.timer
        self.delegate.windowWillClose_(None)
        self.bridge.panel.orderOut_(None)
        self.assertTrue(self.sprout.parked)
        self.assertTrue(self.sprout.win.visible)
        self.assertFalse(self.other.win.visible)
        self.assertEqual(self.bridge.panel.children, [self.other.win])
        frame = self.sprout.win.frame()
        self.assertEqual((frame.origin.x, frame.origin.y), (-176, 76))
        self.assertEqual(self.sprout.win.level(), panel.NSFloatingWindowLevel)
        self.assertEqual(self.sprout.win.autosave, "")
        self.assertFalse(self.sprout.win.draggable)
        timer.cancel.assert_called_once()
        self.view.setImage_.assert_called_with(self.images["parked"])

    def test_minimize_and_reopen_restores_position_and_parent(self):
        self.settings["pet_walk"] = False
        self.delegate.windowWillMiniaturize_(None)
        self.bridge.panel.miniaturized = True
        self.bridge.panel.orderOut_(None)
        self.assertTrue(self.sprout.parked)
        self.delegate.applicationShouldHandleReopen_hasVisibleWindows_(None, False)
        self.assertFalse(self.bridge.panel.miniaturized)
        self.assertFalse(self.sprout.parked)
        self.assertTrue(self.sprout.win.visible)
        self.assertIn(self.sprout.win, self.bridge.panel.children)
        frame = self.sprout.win.frame()
        self.assertEqual((frame.origin.x, frame.origin.y), self.origin)
        self.assertEqual(self.sprout.win.autosave, "catPet3")
        self.assertEqual(self.sprout.win.level(), panel.NSNormalWindowLevel)
        self.assertTrue(self.sprout.win.draggable)
        self.view.setImage_.assert_called_with(self.images["idle"])

    def test_repeated_parking_does_not_replace_the_return_position(self):
        self.bridge.park_sprout()
        self.bridge.park_sprout()
        self.bridge.show_panel()
        self.delegate.windowDidDeminiaturize_(None)
        frame = self.sprout.win.frame()
        self.assertEqual((frame.origin.x, frame.origin.y), self.origin)
        self.assertEqual(self.bridge.panel.children.count(self.sprout.win), 1)

    def test_disabled_or_unselected_sprout_is_not_parked(self):
        for enabled, chosen in ((False, ["sprout"]), (True, ["ham"])):
            with self.subTest(enabled=enabled, chosen=chosen):
                self.settings.update(pet_enabled=enabled, pets=chosen)
                self.bridge.park_sprout()
                self.assertFalse(self.sprout.parked)
                self.assertIn(self.sprout.win, self.bridge.panel.children)

    def test_menu_hide_and_show_uses_the_same_parking_behavior(self):
        self.bridge.togglePanel_(None)
        self.assertFalse(self.bridge.panel.visible)
        self.assertTrue(self.sprout.parked)
        self.bridge.togglePanel_(None)
        self.assertTrue(self.bridge.panel.visible)
        self.assertFalse(self.sprout.parked)

    def test_parked_image_survives_expressions_and_queued_updates(self):
        pending = []
        with patch("panel.AppHelper.callAfter", lambda fn: pending.append(fn)):
            self.sprout.apply_image()
            self.bridge.park_sprout()
            self.sprout.set("happy")
            for fn in pending:
                fn()
        self.view.setImage_.assert_called_with(self.images["parked"])


if __name__ == "__main__":
    unittest.main()
