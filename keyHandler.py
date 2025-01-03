from pynput import keyboard
import pyclip
import time

import translator
from fileHandlers.configHandler import config
import fileHandlers.layoutHandler as layoutHandler


class Handler:
    controller = keyboard.Controller()
    
    def __init__(self):
        # create hotkey
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(
                config["options"]["translate"]["keybind"]),
            on_activate=self.activate)

        # register listener for it
        self.listener = keyboard.Listener(
            on_press=self.canonical(hotkey.press),
            on_release=self.canonical(hotkey.release))
        self.listener.start()


    # input normalisation
    def canonical(self, func):
        return lambda key: func(self.listener.canonical(key))


    def activate(self):
        text = self.getText()
        if text.strip() == "":
            return

        translatedText = translator.translate(text, *self.getLayouts(text))

        pyclip.copy(translatedText)
        if config["options"]["paste"]["do"]:
            self.pressKeybind(config["options"]["paste"]["keybind"])


    def getText(self) -> str:
        # keybind enabled
        if config["options"]["copy"]["do"]:
            pyclip.copy("")
            text = ""
            
            self.pressKeybind(config["options"]["copy"]["keybind"])
            # simulating keypresses actually takes time
            # waiting for clipboard to update
            copyTime = time.time()
            while text == pyclip.paste().decode():
                if time.time() - copyTime > 2:
                    return ""
                # small speedbump for the loop
                time.sleep(0.05)
            text = pyclip.paste().decode()
        
        # keybind disabled
        else:
            try:
                text = pyclip.paste().decode()
            # as of what i know it can be raised
            # if clipboard contains something other than string
            except Exception as e:
                print("Warning! While getting clipboard data occured an exception:\n"+
                    f"{type(e).__name__}({e})")
                pyclip.copy("")
                text = ""
        
        return text
    
    
    def getLayouts(self, text:str) -> tuple[str, str]:
        inLayout = None
        outLayout = None
        # auto mode
        if config["layouts"]["active"] == "Auto":
            layoutNames = [
                config["layouts"]["auto"][0],
                config["layouts"]["auto"][1]]
            layouts = [
                layoutHandler.getLayout(config["layouts"]["auto"][0]),
                layoutHandler.getLayout(config["layouts"]["auto"][1])]
            
            for char in text:
                if char.isalpha():
                    for layout in layouts:
                        # may fuck up with "implicit" case
                        if char.lower() in layout["lower"]:
                            inLayout = layoutNames.pop(layouts.index(layout))
                            outLayout = layoutNames.pop()
                            break
                if inLayout:
                    break
            if not inLayout:
                return
        # manual mode
        else:
            inLayout, outLayout = config["layouts"]["active"].split(" -> ")
        
        return inLayout, outLayout


    def pressKeybind(self, keybind:str):
        # release already translation keybind buttons
        # so they don't interfiere
        for keyName in keyboard.HotKey.parse(config["options"]["translate"]["keybind"]):
            try:    key = keyboard.Key(keyName)
            except: key = keyName
            self.controller.release(key)

        # parse keybind keys into a digestable form
        # since pynput doesnt want you to press key combos
        keys = []
        for keyName in keyboard.HotKey.parse(keybind):
            try:    key = keyboard.Key(keyName)
            except: key = keyName
            keys.append(key)
        
        # press them fuckers
        for key in keys:
            self.controller.press(key)
        
        for key in reversed(keys):
            self.controller.release(key)