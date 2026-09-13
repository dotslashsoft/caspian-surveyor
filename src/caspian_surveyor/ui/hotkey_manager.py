import keyboard

class HotkeyManager:
    def __init__(self, bindings):
        self.bindings = bindings
        self.counter = 0

    def register_hotkeys(self):
        for hotkey, callback in self.bindings.items():
            keyboard.add_hotkey(hotkey, callback)