import tkinter as tk
import random
from util import *
import math

root = tk.Tk()
root.title("Snake")

# constants
safe_zone = 250  # radius around snake head where rocks will not spawn
bullet_size = Vector(100, 100)
rock_size = (230, 330)  # size interval for rocks
rock_time_interval = [15, 30]  # time intervals between spawns
win_buff_head = 1  # how many windows to buffer under the snake head
win_buff_offscr = 14  # off-screen window buffer size to wait out open animation
grid_square = 30
rock_images = [tk.PhotoImage(file=f"images/rocks/rock{i}.png") for i in range(9)]
max_rocks = 6  # rocks before player loses

rock_spawn_rate = tk.IntVar()
spawn_rocks = tk.IntVar()
snake_speed = tk.IntVar()
bullet_count = tk.IntVar()
bullet_speed = tk.IntVar()
difficulty = tk.IntVar()
difficulty.set(2)

difficulty_table = [
    {"label": {"text": "Custom", "fg": "black"},
     "vars": ()},

    {"label": {"text": "Very easy", "fg": "blue"},
     "vars": ((rock_spawn_rate, 20), (spawn_rocks, 0), (snake_speed, 3), (bullet_count, 0), (bullet_speed, 1))},

    {"label": {"text": "Easy", "fg": "darkgreen"},
     "vars": ((rock_spawn_rate, 20), (spawn_rocks, 1), (snake_speed, 2), (bullet_count, 1), (bullet_speed, 1))},

    {"label": {"text": "Medium", "fg": "orange"},
     "vars": ((rock_spawn_rate, 12), (spawn_rocks, 1), (snake_speed, 3), (bullet_count, 1), (bullet_speed, 2))},

    {"label": {"text": "Hard", "fg": "red"},
     "vars": ((rock_spawn_rate, 5), (spawn_rocks, 1), (snake_speed, 3), (bullet_count, 2), (bullet_speed, 2))},

    {"label": {"text": "Impossible", "fg": "darkred"},
     "vars": ((rock_spawn_rate, 0), (spawn_rocks, 1), (snake_speed, 4), (bullet_count, 4), (bullet_speed, 3))}
]

monitor_height = root.winfo_screenheight()
monitor_width = root.winfo_screenwidth()

root.update()
topbar_height = root.winfo_rooty() - root.winfo_y()
window_border = root.winfo_rootx() - root.winfo_x() - 1  # windows adds offsets on windows - 7px "shadow" border + 1px invisible border
init_utils(window_border, topbar_height)

apple_size = Vector(int(topbar_height * (90 / 38)), topbar_height)
snake_size = Vector(int(topbar_height * (175 / 38)), topbar_height + grid_square)
grid_size = (Vector(monitor_width, monitor_height) - snake_size + grid_square) // grid_square


class Snake:
    def __init__(self):
        self.window_buffer = []
        self.rocks = []
        self.bullets = []
        self.key_queue = []

    def get_latest_direction(self):
        if len(self.key_queue) > 0:
            return self.key_queue[-1]
        return self.vel

    def on_key_press(self, event):
        key = event.keysym.lower()
        if key == "w" and self.get_latest_direction() != Vector(0, 1):
            snake.key_queue.append(Vector(0, -1))
        elif key == "s" and self.get_latest_direction() != Vector(0, -1):
            snake.key_queue.append(Vector(0, 1))
        elif key == "a" and self.get_latest_direction() != Vector(1, 0):
            snake.key_queue.append(Vector(-1, 0))
        elif key == "d" and self.get_latest_direction() != Vector(-1, 0):
            snake.key_queue.append(Vector(1, 0))

    def start(self):  # start game
        rock_time_interval[0] += rock_spawn_rate.get()
        rock_time_interval[1] += rock_spawn_rate.get()

        root.bind_all("<Key>", self.on_key_press)
        root.geometry(f"+-5000+0")

        a = PlainWindow(root, Vector(-500, 0), apple_size, bg="white", borderwidth=4, relief="raised")
        a.attributes('-topmost', True)
        a.focus_force()
        a.iconbitmap(default="images/transparent.ico")

        tk.Label(a, bg="white", text="Apple").pack(side="left", padx=(4, 0))
        f = tk.Frame(a, bg="white", width=25, height=25)
        f.pack_propagate(0)
        b = tk.Label(f, text="x", bg="#C75050", fg="white")
        b.pack(expand=1, fill="both")
        f.pack(side="right", padx=(0, 1))
        b.bind("<Enter>", lambda e: b.config(bg="#FF4C4C"))
        b.bind("<Leave>", lambda e: b.config(bg="#C75050"))
        b.bind("<1>", lambda e: [b.config(bg="#993D3D"), root.after(150, root.destroy)])

        self.apple = a
        root.update()

        self.reset()

        for _ in range(win_buff_offscr):
            self.window_buffer.append(self.create_new_snake_window())

        self.update()
        self.move_bullets()

        # invisible window to prevent clicking on stuff during a game
        self.background_window = PlainWindow(root, Vector(0, 0), Vector(monitor_width, monitor_height), bg="#7F7F7F")
        self.background_window.attributes("-alpha", 0.002)

    def reset(self):
        for rock in self.rocks:
            rock.destroy()
        for bullet in self.bullets:
            bullet.destroy()

        self.dead = False
        self.rocks = []
        self.bullets = []
        self.rock_counter = 30
        self.key_queue = []
        self.vel = Vector(0, 0)
        self.body = []
        self.length = 5
        self.head = Vector(random.randrange(0, grid_size.x), random.randrange(0, grid_size.y))

        self.make_new_apple()

        for _ in range(bullet_count.get()):
            while True:
                pos = Vector(random.randrange(0, monitor_width - bullet_size.x),
                             random.randrange(0, monitor_height - bullet_size.y))
                if not do_rect_overlap(pos, pos + bullet_size, self.head * grid_square,
                                       self.head * grid_square + snake_size):
                    break
            bullet = PlainWindow(root, pos, bullet_size, cursor="fleur", bg="red")
            bullet.attributes("-topmost", True)
            bullet.dragging = False

            # fake window topbar
            f = tk.Frame(bullet, bg="white")
            f.pack(fill="x", side="top")
            f.columnconfigure(list(range(3)), weight=1)
            for i, ch in enumerate("🗕🗖✕"):
                l = tk.Label(f, text=ch, bg="white", fg="#999999")
                l.grid(column=i, row=0, sticky="news")
                # mouse hover effect
                if i == 2:
                    l.bind("<Enter>", lambda e, label=l: label.configure(bg="red", fg="white"))
                else:
                    l.bind("<Enter>", lambda e, label=l: label.configure(bg="#999999", fg="#000000"))
                l.bind("<Leave>", lambda e, label=l: label.configure(bg="white", fg="#999999"))

            bullet.bind("<1>", dragging_start)
            bullet.bind("<B1-Motion>", dragging)
            bullet.bind("<ButtonRelease-1>", dragging_stop)

            self.bullets.append(bullet)

    def create_new_snake_window(self):
        top = Window(root, Vector(-500, 0), snake_size, bg="green")
        top.protocol("WM_DELETE_WINDOW", root.destroy)
        top.transient(self.apple)  # don't show the windows in the taskbar

        # transient() hides the 🗕 🗖 icons, so bring them back
        root.after(20, lambda t=top: show_all_icons(t))
        return top

    def snake_collides_with_rect(self, point1, point2):
        for part in self.body:
            if do_rect_overlap(part.pos, part.pos + snake_size, point1, point2):
                return True
        return False

    def make_new_apple(self):
        for _ in range(1000):
            apple = Vector(random.randint(0, monitor_width - apple_size.x),
                           random.randint(0, monitor_height - apple_size.y))
            if not self.snake_collides_with_rect(apple, apple + apple_size):
                self.apple.set_pos(apple)
                return
        else:
            print("Apple couldnt find a place")

    def create_rock(self):
        size = Vector(random.randrange(*rock_size), random.randrange(*rock_size))
        point = self.head * grid_square + snake_size / 2
        for _ in range(1000):
            pos = Vector(random.randrange(0, monitor_width - size.x), random.randrange(0, monitor_height - size.y))
            if not (do_rect_overlap(pos, pos + size, point - safe_zone, point + safe_zone) or
                    self.snake_collides_with_rect(pos, pos + size)):
                break
        else:
            print("Rock couldnt find a place")
            return

        rock = Window(root, pos, Vector(size))
        rock.iconbitmap("images/rock.ico")
        rock.transient(self.background_window)
        rock.resizable(False, False)
        rock.bind('<Configure>', stop_dragging)

        rock.variable = 0

        rock.protocol("WM_DELETE_WINDOW", lambda r=rock: [self.rocks.remove(r), r.destroy(), self.update_rock_title()])

        # chose the best rock image
        size.y -= topbar_height
        canvas = tk.Canvas(rock, bg="gray", highlightthickness=0)
        canvas.pack(fill="both", expand=1)
        ratios = {abs(i.width() / i.height() - size.x / size.y): i for i in rock_images}
        canvas.create_image(size.x / 2, size.y / 2, image=ratios[sorted(ratios)[0]])

        self.rocks.append(rock)
        self.update_rock_title()

    def update_rock_title(self):
        remaining = max_rocks - len(self.rocks)
        for r in self.rocks:
            r.title(f"Rock - {remaining} remain")

    def update(self):
        if (not self.dead) and (self.vel != Vector(0, 0) or len(self.key_queue) > 0 or len(self.body) == 0) and len(
                self.rocks) < max_rocks:
            self.rock_counter -= 1
            if self.rock_counter == 0:
                if spawn_rocks.get():
                    self.create_rock()
                self.rock_counter = random.randint(*rock_time_interval)

            if len(self.key_queue) > 0:
                self.vel = self.key_queue.pop(0)

            self.head += self.vel

            top = self.window_buffer.pop()
            top.attributes('-topmost', True)
            top.set_pos(self.head * grid_square, snake_size)
            # prepare new window
            for i in range(1, win_buff_head + 1):
                self.window_buffer[-i].set_pos(self.head * grid_square, snake_size)
            self.body.insert(0, top)
            self.window_buffer.insert(0, self.create_new_snake_window())

            if len(self.body) > self.length:
                self.body.pop().destroy()

            # self collision
            for x in range(1, len(self.body)):
                if self.body[x].pos // grid_square == self.head:
                    self.dead = True
                    break

            # rock collision
            for rock in self.rocks:
                if do_rect_overlap(self.body[0].pos, self.body[0].pos + snake_size,
                                   rock.pos, rock.pos + rock.size):
                    self.dead = True

            # bullet collision
            for bullet in self.bullets:
                if self.snake_collides_with_rect(bullet.pos, bullet.pos + bullet.size):
                    self.dead = True

            # wall collision
            if self.head.x not in range(0, grid_size.x) or self.head.y not in range(0, grid_size.y):
                self.dead = True

            # apple collision
            if do_rect_overlap(self.body[0].pos, self.body[0].pos + snake_size,
                               self.apple.pos, self.apple.pos + apple_size):
                self.length += 1
                self.make_new_apple()

        elif self.dead:
            for i in range(1, win_buff_head + 1):
                self.window_buffer[-i].geometry("+10000+0")

            # window closing animation
            while not len(self.body) == 0:
                self.body.pop(0).destroy()
                root.update()
                root.after(100)

            self.reset()

        elif len(self.rocks) >= max_rocks:  # when player doesnt close rock windows
            self.rocks[0].variable += 1
            hitbox = Vector(10, 10)
            radius = 500 - self.rocks[0].variable * 30
            stred_hlavy = self.head * grid_square + snake_size / 2
            uhol_step = 360 / len(self.rocks)

            for rock in self.rocks:
                rock.title("The end")
                rock.protocol("WM_DELETE_WINDOW", lambda: 0)

            for i, rock in enumerate(self.rocks):
                if self.rocks[0].variable == 1:
                    fade(rock, 1000)
                uhol = math.radians(uhol_step * i)
                bod_na_kruhu = stred_hlavy + Vector(math.cos(uhol), math.sin(uhol)) * radius
                rock.set_pos(bod_na_kruhu - rock.size / 2)
                if self.rocks[0].variable == 1:
                    fade(rock, 0)
                if do_rect_overlap(stred_hlavy - hitbox, stred_hlavy + hitbox, rock.pos, rock.pos + rock.size):
                    self.dead = True
                    break
                root.update()
                root.after(40)

        root.after(((6 - snake_speed.get()) * 10) * 2, self.update)

    def move_bullets(self):
        if (not self.dead) and self.vel != Vector(0, 0) and len(self.rocks) < max_rocks:
            spacing = (len(self.body) - len(self.bullets)) / (len(self.bullets) + 1)
            for i, bullet in enumerate(self.bullets):
                if bullet.dragging:
                    continue
                target_index = round(spacing * (i + 1) + i - 0.5)
                stred = self.body[target_index].pos + snake_size / 2
                stred_bullets = bullet.pos + bullet.size / 2
                posun = (stred - stred_bullets).set_length(bullet_speed.get() * 7)
                bullet.set_pos(bullet.pos + posun)

        root.after(33, self.move_bullets)


snake = Snake()

root.resizable(False, False)
root.iconbitmap("images/snake.ico")

tk.Label(root, text="Settings", font="Arial 20").grid(columnspan=3, row=0, pady=5)
tk.Label(root, text="Difficulty: ").grid(row=1)


def set_difficulty(i):
    difficulty.set(i)
    difficulty_label.config(cnf=difficulty_table[int(i)]["label"])
    for var, value in difficulty_table[int(i)]["vars"]:
        var.set(value)


slider_frame = tk.Frame(root)
slider_frame.grid(column=1, row=1, sticky="news")
difficulty_label = tk.Label(slider_frame, width=10)
difficulty_label.grid(sticky="e")
set_difficulty(difficulty.get())
tk.Scale(slider_frame, from_=0, to=len(difficulty_table) - 1, length=150, orient="horizontal", showvalue=False,
         variable=difficulty, command=set_difficulty).grid(column=1, row=0)


def dropdown():
    if dropdown_frame.extended:
        dropdown_frame.grid_forget()
        dropdown_label.config(text="⯈" + dropdown_label.cget("text")[1:])
    else:
        dropdown_frame.grid(columnspan=2, row=3, sticky="news", padx=10)
        dropdown_label.config(text="⯆" + dropdown_label.cget("text")[1:])
    dropdown_frame.extended = not dropdown_frame.extended
    center_window(root)


dropdown_label = tk.Label(root, text="⯈ More options", cursor="hand2", anchor="w", width=42)
dropdown_label.grid(columnspan=2, sticky="news", padx=10)
dropdown_label.bind("<1>", lambda x: dropdown())

dropdown_frame = tk.Frame(root, relief="sunken", bd=2)
dropdown_frame.extended = False

tk.Label(dropdown_frame, text="Rocks: ").grid(row=0)
tk.Checkbutton(dropdown_frame, variable=spawn_rocks, command=lambda: set_difficulty(0)).grid(row=0, column=1)

tk.Label(dropdown_frame, text="Rock spawn interval: ").grid(row=1)
create_slider(dropdown_frame, rock_spawn_rate, 1, 1, 0, 20).config(command=lambda x: set_difficulty(0))

tk.Label(dropdown_frame, text="Snake speed: ").grid(row=2)
create_slider(dropdown_frame, snake_speed, 2, 1, 1, 5).config(command=lambda x: set_difficulty(0))

tk.Label(dropdown_frame, text="Bullet count: ").grid(row=3)
create_slider(dropdown_frame, bullet_count, 3, 1, 0, 5).config(command=lambda x: set_difficulty(0))

tk.Label(dropdown_frame, text="Bullet speed: ").grid(row=4)
create_slider(dropdown_frame, bullet_speed, 4, 1, 1, 5).config(command=lambda x: set_difficulty(0))

tk.Button(root, text="START", command=snake.start).grid(row=4, columnspan=2, pady=10)

center_window(root)

root.mainloop()
