import tkinter as tk
from ctypes import windll

windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"snake is the best") # for the icon on taskbar

windll.shcore.SetProcessDpiAwareness(1) # so that windows scaling doesnt mess with game windows

# function inspired by this: https://stackoverflow.com/a/47867275

# funkction transient() hides the 🗕 🗖 icons, so this function brings them back
def show_all_icons(window):
    hwnd = windll.user32.GetParent(window.winfo_id()) # get window id
    style = windll.user32.GetWindowLongPtrW(hwnd, -16) # get window style
    windll.user32.SetWindowLongPtrW(hwnd, -16, style | 0x30000) # set new window style
    windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0b100111) # update window


window_border = None
topbar_height = None

# get some values from the main script
def init_utils(wb, th):
    global window_border, topbar_height
    window_border, topbar_height = wb, th

class Vector:
    def __init__(self, x, y=None):
        if y is not None:
            self.x = x
            self.y = y
        else: # object in x parameter is Vector
            self.x = x.x
            self.y = x.y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return Vector(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        return Vector(self.x - other, self.y - other)

    def __pow__(self, power, modulo=None):
        if isinstance(power, Vector):
            return Vector(self.x ** power.x, self.y ** power.y)
        return Vector(self.x ** power, self.y ** power)

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x * other.x, self.y * other.y)
        return Vector(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x / other.x, self.y / other.y)
        return Vector(self.x / other, self.y / other)

    def __floordiv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x // other.x, self.y // other.y)
        return Vector(self.x // other, self.y // other)

    def __eq__(self, other):
        return other.x == self.x and other.y == self.y

    def __str__(self):
        return f"<Vector x={self.x} y={self.y}>"

    def length(self):
        return (self.x**2 + self.y**2) ** 0.5

    def to_int(self):
        return Vector(int(self.x), int(self.y))

    def length_sq(self):
        return self.x**2 + self.y**2

    def set_length(self, new_len):
        return self * (self.length_sq()**-0.5) * new_len

# Wrapper objekt for Toplevel
# Windows messes with window positioning, so this wrapper fixes it
class Window(tk.Toplevel):
    def __init__(self, master, pos, size, **kvargs):
        tk.Toplevel.__init__(self, master, **kvargs)
        self.gometry_configured = False
        if pos:
            self.set_pos(pos, size)

    def set_pos(self, pos, size=None):
        if size is not None:
            self.size = size
            self.geometry(f"{size.x-1}x{size.y-topbar_height}")
        self.pos = pos
        self.geometry(f"+{int(pos.x-window_border)}+{int(pos.y)}")
        self.gometry_configured = True

# For a window without the top part with the icons
class PlainWindow(tk.Toplevel):
    def __init__(self, master, pos, size, **kvargs):
        tk.Toplevel.__init__(self, master, **kvargs)
        self.overrideredirect(1)
        self.set_pos(pos, size)
        self.gometry_configured = False

    def set_pos(self, pos, size=None):
        if size is not None:
            self.size = size
            self.geometry(f"{size.x}x{size.y}")
        self.pos = pos
        self.geometry(f"+{int(pos.x)}+{int(pos.y)}")
        self.gometry_configured = True

def do_rect_overlap(a1, a2, b1, b2):
    return not (a1.x > b2.x or b1.x > a2.x or a1.y > b2.y or b1.y > a2.y)

def stop_dragging(event):
    try:
        win = event.widget
        # prevent infinite loop from .configure() function 
        if win.gometry_configured:
            win.gometry_configured = False
            return
        win.set_pos(event.widget.pos)
    except AttributeError: # if the event is triggered by something else than a toplevel
        pass


def dragging_start(event):
    win = event.widget.winfo_toplevel()
    win.dragging = True
    win.drag_pos = Vector(event.x_root, event.y_root) - win.pos

def dragging(event):
    win = event.widget.winfo_toplevel()
    win.set_pos(Vector(event.x_root, event.y_root) - win.drag_pos)

def dragging_stop(event):
    event.widget.winfo_toplevel().dragging = False

def create_slider(root, var, row, column, from_, to):
    frame = tk.Frame(root)
    frame.grid(column=column, row=row, sticky="news")
    tk.Label(frame, textvariable=var, width=2).grid(sticky="e")
    scale = tk.Scale(frame, from_=from_, to=to, length=150, orient="horizontal", showvalue=False, variable=var)
    scale.grid(column=1, row=0)
    return scale

def center_window(window):
    window.update()
    window.geometry(
        f"+{(window.winfo_screenwidth() - window.winfo_width()) // 2}"
        f"+{(window.winfo_screenheight() - window.winfo_height() - topbar_height) // 2}")

def fade(window, start_opacity):
    for alpha in range(0, 1001, 200):
        window.attributes("-alpha", abs(start_opacity - alpha) / 1000)
        window.update()
        window.after(30)
