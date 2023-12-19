import openai
import os
from dotenv import load_dotenv
from pynput import keyboard
import subprocess

load_dotenv()
LANGUAGE = os.getenv('TRANSLATE_LAN')
KEY = os.getenv('API_KEY')
SYSTEM = os.name

#There you can specifty your shortcut for translation of the clipboard [Default: CTRL + SHIFT + T]
COMBINATION = {keyboard.Key.ctrl, keyboard.Key.shift, keyboard.KeyCode.from_char('t')}

pressed_keys = set()

openai.api_key = KEY

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
                translated = ai_translation(collecting_clipboard_macos(), LANGUAGE)
                copying_to_clipboard_macos(translated)
                macos_notify("AI Translator", f'Clipboard has been translated to {LANGUAGE}')

            else:

                translated = ai_translation(collecting_clipboard_windows(), LANGUAGE)
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

with keyboard.Listener(on_press=pressing_buttons, on_release=releasing_buttons) as keyboard_listener:

    keyboard_listener.join()

