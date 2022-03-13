import re
import subprocess
import time

import tkinter as tk
from screeninfo import get_monitors

def get_active_window_title():
    root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE)
    stdout, stderr = root.communicate()
    m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)
    if m is None:
        return None
    window_id = m.group(1)
    window = subprocess.Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=subprocess.PIPE)
    stdout, stderr = window.communicate()
    match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
    if match is None:
        return None
    return match.group("name").strip(b'"').decode()


def _execute_command(command):
    process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE)
    (output, err) = process.communicate()
    process.wait()
    return list(filter(lambda line: line, output.decode().split('\n')))


def get_window():
    window_name = get_active_window_title()
    for line in _execute_command("wmctrl -p -G -l"):
        values = list(filter(lambda i: i, line.split(' ')))
        if len(values) > 6:
            name = ' '.join(values[8:])
            if window_name == name:
                return values[0]


def get_screens(columns, lines):
    app = tk.Tk()
    monitors = []
    for monitor in get_monitors():
        app2 = tk.Toplevel(app)
        app2.geometry("{}x{}+{}+{}".format(monitor.width, monitor.height, monitor.x, monitor.y))
        app2.wait_visibility(app2)
        app2.overrideredirect(True)
        monitors.append([app2.winfo_width(), app2.winfo_height(), app2.winfo_x(), app2.winfo_y()])
        app2.withdraw()
        app2.destroy()
    app.destroy()

    roots = []
    screens = []
    app = tk.Tk()
    for monitor in monitors:
        blocks = []
        width, height, x, y = monitor
        root = tk.Toplevel(app)
        root.geometry("{}x{}+{}+{}".format(width, height, x, y))
        root.overrideredirect(True)
        root.wait_visibility(root)
        root.wm_attributes("-alpha", 0.5)
        canvas = tk.Canvas(root, width=width, height=height)
        canvas.pack()
        for w_index in range(0, columns):
            for h_index in range(0, lines):
                size_column = width / columns
                size_line = height / lines
                init_x = x + size_column * w_index
                end_x = init_x + size_column
                init_y = y + size_line * h_index
                end_y = init_y + size_line
                blocks.append([init_x, end_x, init_y, end_y,
                               canvas.create_rectangle(init_x-x, init_y-y, end_x-x, end_y-y, fill="blue")])
            roots.append(root)
        screens.append({
            'blocks': blocks,
            'canvas': canvas
        })
    app.withdraw()
    return app, roots, screens


def on_move(x, y, buttons, keyboard_keys, screens, last_x, last_y, last_command, last_timestamp, last_window,
            gui_roots):
    ctrl = len(list(filter(lambda n: n == 'ctrl', keyboard_keys))) > 0
    right_clicked = len(list(filter(lambda bb: bb.value == 3, buttons))) == 1
    if not ctrl or not right_clicked:
        for root in gui_roots:
            root.withdraw()
        return
    for root in gui_roots:
        root.deiconify()
    if time.time() - last_timestamp < 0.3:
        return
    last_timestamp = time.time()
    for screen in screens:
        for block in screen['blocks']:
            init_x, end_x, init_y, end_y, rectangle = block
            if init_x <= x <= end_x and init_y <= y <= end_y:
                left_clicked = len(list(filter(lambda bb: bb.value == 1, buttons))) == 1
                window = get_window()
                if screen['canvas'].itemconfig(rectangle)['fill'] != 'green':
                    screen['canvas'].itemconfig(rectangle, fill='green')
                if left_clicked:
                    window = get_window()
                    command = "wmctrl -i -r " + window + " -e 0," + str(int(last_x)) + "," + str(
                        int(last_y)) + "," + str(
                        int(end_x - last_x)) + "," + str(int(end_y - last_y))
                    if last_command == command:
                        continue
                    if not last_window or last_window != window:
                        _execute_command("wmctrl -i -r " + window + " -b remove,maximized_vert,maximized_horz")
                        last_window = last_window
                    _execute_command(command)
                else:
                    last_x = init_x
                    last_y = init_y
                    command = "wmctrl -i -r " + window + " -e 0," + str(int(last_x)) + "," + str(
                        int(last_y)) + "," + str(
                        int(end_x - init_x)) + "," + str(int(end_y - init_y))
                    if last_command == command:
                        continue
                    last_command = command
                    if not last_window or last_window != window:
                        _execute_command("wmctrl -i -r " + window + " -b remove,maximized_vert,maximized_horz")
                        last_window = last_window
                    _execute_command(command)
                continue
            else:
                if screen['canvas'].itemconfig(rectangle)['fill'] != 'blue':
                    screen['canvas'].itemconfig(rectangle, fill='blue')
    return last_x, last_y, last_command, last_timestamp, last_window


def on_click(_x, _y, button, pressed, buttons):
    if pressed:
        buttons.append(button)
        return buttons
    return list(filter(lambda _button: _button.value != button.value, buttons))


def on_press(key, keyboard_keys):
    try:
        if key not in keyboard_keys:
            keyboard_keys.append(key.name)
        return keyboard_keys
    except:
        return keyboard_keys


def on_release(key, keyboard_keys):
    try:
        return list(filter(lambda k: k != key.name, keyboard_keys))
    except:
        return keyboard_keys
