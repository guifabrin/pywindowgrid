import threading
import time

from functions import get_screens, on_click, on_move, on_press, on_release

buttons = []
keyboard_keys = []

gui_app, gui_roots, screens = get_screens(10, 5)

last_timestamp = time.time()
last_x, last_y, last_command, last_window = None, None, None, None


def _on_click(x, y, button, pressed):
    global buttons
    buttons = on_click(x, y, button, pressed, buttons)


def thread_mouse_click():
    from pynput.mouse import Listener
    with Listener(on_click=_on_click) as listener:
        listener.join()


def _on_move(x, y):
    global last_x, last_y, last_command, last_timestamp, last_window, gui_roots
    result = on_move(x, y, buttons, keyboard_keys, screens, last_x, last_y, last_command, last_timestamp, last_window,
                     gui_roots)
    if result:
        last_x, last_y, last_command, last_timestamp, last_window = result


def thread_mouse_move():
    from pynput.mouse import Listener
    with Listener(on_move=_on_move) as listener:
        listener.join()


def _on_press(key):
    global keyboard_keys
    keyboard_keys = on_press(key, keyboard_keys)


def _on_release(key):
    global keyboard_keys
    keyboard_keys = on_release(key, keyboard_keys)


def thread_keyboard():
    from pynput.keyboard import Listener
    with Listener(on_press=_on_press, on_release=_on_release) as listener:
        listener.join()


threading.Thread(target=thread_mouse_click).start()
threading.Thread(target=thread_mouse_move).start()
threading.Thread(target=thread_keyboard).start()
gui_app.mainloop()
