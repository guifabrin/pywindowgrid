import re
import subprocess
import threading
from subprocess import Popen, PIPE

keys = []
buttons = []
lock_x = 0
lock_y = 0

width_sizes = 10
height_sizes = 5


def _execute_command(command):
    process = Popen(command.split(" "), stdout=PIPE)
    (output, err) = process.communicate()
    process.wait()
    lines = list(filter(lambda line: line, output.decode().split('\n')))
    return lines


avaliable_size_response = _execute_command('xprop -root _NET_WORKAREA')
avaliable_size = re.split('=|,', avaliable_size_response[0])[1:5]
init_x = int(avaliable_size[0])
init_y = int(avaliable_size[1])
width = int(avaliable_size[2])
height = int(avaliable_size[3])
block_size_w = width / width_sizes
block_size_h = height / height_sizes

screens = []
screens_lines = _execute_command("xrandr --listmonitors")
for s_line in screens_lines:
    parts = s_line.split(' ')
    if s_line and len(parts) >= 4:
        size_position = parts[3]
        size, x, y = size_position.split('+')
        w, h = size.split('x')
        screens.append({
            'w': w.split('/')[0],
            'h': h.split('/')[0],
            'x': x,
            'y': y
        })

def get_active_window_title():
    root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE)
    stdout, stderr = root.communicate()

    m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)
    if m != None:
        window_id = m.group(1)
        window = subprocess.Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=subprocess.PIPE)
        stdout, stderr = window.communicate()
    else:
        return None

    match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
    if match != None:
        return match.group("name").strip(b'"').decode()

    return None

def get_window():
    lines = _execute_command("wmctrl -p -G -l")
    window_name = get_active_window_title()
    for line in lines:
        values = list(filter(lambda i: i, line.split(' ')))
        if len(values) > 6:
            name = ' '.join(values[8:])
            if window_name == name:
                return values[0]


def on_move(x, y):
    global buttons, lock_x, lock_y, width_sizes, height_sizes, block_size_w, block_size_h, init_x, init_y, keys
    ctrl = len(list(filter(lambda n: n == 'ctrl', keys))) > 0
    shift = len(list(filter(lambda n: n == 'shift', keys))) > 0
    if not ctrl:
        return
    right_clicked = len(list(filter(lambda bb: bb.value == 3, buttons))) == 1
    if not right_clicked:
        return
    _break = False
    block_x_init = 0
    block_x_end = 0
    block_y_init = 0
    block_y_end = 0
    for w_index in range(0, width_sizes):
        for h_index in range(0, height_sizes):
            block_x_init = init_x + block_size_w * w_index
            block_x_end = block_x_init + block_size_w
            block_y_init = init_y + block_size_h * h_index
            block_y_end = block_y_init + block_size_h
            if block_x_init <= x <= block_x_end and block_y_init <= y <= block_y_end:
                _break = True
                break
        if _break:
            break
    window = get_window()
    if shift:
        window = get_window()
        _execute_command("wmctrl -i -r " + window + " -b remove,maximized_vert,maximized_horz")
        _execute_command(
            "wmctrl -i -r " + window + " -e 0," + str(int(lock_x)) + "," + str(int(lock_y)) + "," + str(
                int(block_x_end - lock_x)) + "," + str(int(block_y_end - lock_y)))
    else:
        if lock_x != block_x_init or lock_y != block_y_init:
            lock_x = block_x_init
            lock_y = block_y_init
            _execute_command("wmctrl -i -r " + window + " -b remove,maximized_vert,maximized_horz")
            _execute_command(
                "wmctrl -i -r " + window + " -e 0," + str(int(lock_x)) + "," + str(int(lock_y)) + "," + str(
                    int(block_size_w)) + "," + str(int(block_size_h)))


def on_click(_x, _y, button, pressed):
    global buttons
    if pressed:
        buttons.append(button)
    else:
        buttons = list(filter(lambda _button: _button.value != button.value, buttons))


def on_press(key):
    global keys
    try:
        if key not in keys:
            keys.append(key.name)
    except:
        pass


def on_release(key):
    global keys
    try:
        keys = list(filter(lambda k: k != key.name, keys))
    except:
        pass


def thread_mouse_click():
    from pynput.mouse import Listener
    with Listener(on_click=on_click) as listener:
        listener.join()


def thread_mouse_move():
    from pynput.mouse import Listener
    with Listener(on_move=on_move) as listener:
        listener.join()


def thread_keyboard():
    from pynput.keyboard import Listener
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


threading.Thread(target=thread_mouse_click).start()
threading.Thread(target=thread_mouse_move).start()
threading.Thread(target=thread_keyboard).start()
