import openai
import os
import pathlib
from dotenv import load_dotenv, set_key
from pynput import keyboard
import subprocess
import rumps
import threading
import json

load_dotenv()
starting_language = os.getenv('TRANSLATE_LAN')
KEY = os.getenv('API_KEY')
SYSTEM = os.name
ICON_PATH = pathlib.Path(__file__).parent.parent / "assets" / "icon.png"
LAN_MENU_PATH = pathlib.Path(__file__).parent.parent / "assets" / "language_menu.json"

#There you can specifty your shortcut for translation of the clipboard [Default: CTRL + SHIFT + T]
COMBINATION = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.KeyCode.from_char('t')}

pressed_keys = set()

openai.api_key = KEY

class macOS_app(rumps.App):

    def __init__(self, lan):

        super(macOS_app, self).__init__("AiTranslator", icon=str(ICON_PATH))
        self.selected_language = lan
        self.load_lan_menu()
        self.setup_lan_menu()
        self.menu = ["Insert GPT-KEY", "Add Language"]

    @rumps.clicked("Insert GPT-KEY")
    def inserting_api_key(self, _):

        response = rumps.Window(title="Insert GPT API KEY: ", ok="ok", cancel="cancel", dimensions=(100, 20)).run()

        if response.clicked:

            input_text = response.text
            openai.api_key = input_text
            set_key("./.env", "API_KEY", input_text)
    
    def setup_lan_menu(self):

        lan_menu = rumps.MenuItem("Select Language")

        for language in self.lan_menu:

            language_item = rumps.MenuItem(language, callback=self.select_language)
            lan_menu.add(language_item)
        self.save_lan_menu()
        self.menu.add(lan_menu)


    def select_language(self, sender): #TODO Transfer language selection to .json file and remove this from .env

        self.selected_lan = sender.title
        
    
    def save_lan_menu(self):

        with open(LAN_MENU_PATH, 'w') as f:
            json.dump(self.lan_menu, f)


    def load_lan_menu(self):

        f = open(LAN_MENU_PATH, 'r')
        self.lan_menu = json.load(f)



#collecting and adding data to ours clipboards
def collecting_clipboard_macos():

    return subprocess.run('pbpaste', capture_output=True, text=True).stdout


def collecting_clipboard_windows():

    return subprocess.run(['powershell', '-command', 'Get-Clipboard'], capture_output=True, text=True).stdout


def copying_to_clipboard_win(translated_text: str):

    subprocess.run('clip', universal_newlines=True, input=translated_text, shell=True)


def copying_to_clipboard_macos(translated_text: str):

    subprocess.run('pbcopy', universal_newlines=True, input=translated_text)


def macos_notify(title: str, message: str):

    try:

        pattern = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", pattern])
        subprocess.run(["afplay", "/System/Library/Sounds/Submarine.aiff"])

    except:

        print("A problem had occured while sending notification")


def win_notify():

    try:

        subprocess.run(["powershell", "-c", "(New-Object Media.SoundPlayer 'C:\\Windows\\Media\\notify.wav').PlaySync();"], shell=True)

    except:
        print("An error has occured while playing notification sound, propably bad file path.")


#keyboard recording and checking stuff
def pressing_buttons(key):

    if key in COMBINATION:

        pressed_keys.add(key)

        if all(keys in pressed_keys for keys in COMBINATION):

            if SYSTEM == "posix":
                print(starting_language)
                translated = ai_translation(collecting_clipboard_macos(), starting_language)
                copying_to_clipboard_macos(translated)
                macos_notify("AI Translator", f'Clipboard has been translated to {starting_language}')

            else:

                translated = ai_translation(collecting_clipboard_windows(), starting_language)
                copying_to_clipboard_win(translated)


def releasing_buttons(key):

    try:

        pressed_keys.remove(key)
    
    except KeyError:
        pass

#Ai translation function
def ai_translation(clipboard: str, language: str):

    try:

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
            {"role": "user", "content": f"As my assistant please translate: {clipboard} to {language}. Please leave only clear translated text without any definitions"}]
        )

    except:
        print("There is a problem with the API key, please check its validity.")
        return ""
    
    return response.choices[0].message.content.strip()


def keyboard_listening():
    
    with keyboard.Listener(on_press=pressing_buttons, on_release=releasing_buttons) as keyboard_listener:

        keyboard_listener.join()


if __name__ == "__main__":

    k_thread = threading.Thread(target=keyboard_listening)
    k_thread.start()
    app = macOS_app(starting_language)
    app.run()




