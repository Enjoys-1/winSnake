import tkinter as tk
from pygame.math import Vector2 as vec
from pynput import keyboard
import collections
import random

#TODO close app on snake body part close
#TODO prevent apple from being moved by mouse
#TODO make snake head larger

sqSize = 30
fps = 30  # 30 - nice and stable, 31 - 55 snake gets visually shorter and longer randomly 56 - 102 some windows don't render,
          # 103+ almost no windows render

def getSnakeDir(snake):
    if len(snake.keyQueue) > 0:
        return snake.keyQueue[-1]
    return snake.vel


def on_press(key):
    if key == keyboard.Key.up and not getSnakeDir(snake) == vec(0, 1):
        snake.keyQueue.append(vec(0, -1))
    elif key == keyboard.Key.down and not getSnakeDir(snake) == vec(0, -1):
        snake.keyQueue.append(vec(0, 1))
    elif key == keyboard.Key.left and not getSnakeDir(snake) == vec(1, 0):
        snake.keyQueue.append(vec(-1, 0))
    elif key == keyboard.Key.right and not getSnakeDir(snake) == vec(-1, 0):
        snake.keyQueue.append(vec(1, 0))


def doRectOverlap(a1, a2, b1, b2):
    if a1.x > b2.x or b1.x > a2.x:
        return False
    if a1.y > b2.y or b1.y > a2.y:
        return False
    return True


def isRectInRect(a1, a2, b1, b2):
    return b1.x >= a1.x and a2.x >= b2.x and b1.y >= a1.y and a2.y >= b2.y

def getApple(body):
    gridSize = vec(int((root.winfo_screenwidth() - 90) / sqSize), int((root.winfo_screenheight() - 39) / sqSize))
    apple = vec(random.randint(0, int(gridSize.x)), random.randint(0, int(gridSize.y)))
    while apple in body:
        apple = vec(random.randint(0, int(gridSize.x)), random.randint(0, int(gridSize.y)))
    return apple


def genNewTop():
    top = tk.Toplevel(root)
    # top.overrideredirect(True) # to disable the toolbar (but with it the snake looks better)
    top.geometry("170x%s+%s+%s" % (sqSize, 2000, 500))
    ac = tk.Canvas(top, bg="green", highlightthickness=0)
    ac.pack(fill="both", expand=True)
    top.iconbitmap("ico.ico") # transparent empty icon to hide the default icon
    return top


class Snake:
    def reset(self):
        self.dead = False
        self.keyQueue = []
        self.head = vec(0, 0)
        self.vel = vec(0, 0)
        self.body = collections.deque()
        self.length = 5
        self.apple = getApple([self.head])
        self.appleTop.geometry("90x0+%s+%s" % (int(self.apple.x * sqSize), int(self.apple.y * sqSize)))

    def __init__(self):
        self.dead = False
        self.keyQueue = []
        self.head = vec(0, 0)  # head coordinates
        self.vel = vec(0, 0)  # where the snake is heading
        # body: [head, tail, tail,...,end]
        self.body = collections.deque()
        self.length = 5
        self.apple = getApple([self.head])
        a = tk.Toplevel(root)
        a.geometry("90x0+%s+%s" % (int(self.apple.x * sqSize), int(self.apple.y * sqSize)))
        a.attributes('-topmost', 'true')
        a.focus()
        a.title("Apple")
        a.attributes("-toolwindow", True)
        self.appleTop = a
        self.toplevels = collections.deque()
        # creating new windows has a short animation which makes the snake look kinda weird, so we need a buffer off screen
        self.topBuffer = collections.deque()
        for _ in range(5):
            self.topBuffer.append(genNewTop())
        self.update()

    def update(self):
        if (not self.dead) and (self.vel != vec(0, 0) or len(self.keyQueue) > 0 or len(self.body) == 0):
            if len(self.keyQueue) > 0:
                self.vel = self.keyQueue.pop(0)
            # append new part of snake
            self.head += self.vel
            self.body.appendleft(vec(self.head))
            # moving windows from off screen causes them to blink white for one frame, which in real time causes flicker
            # so one window is moved to the head of the snake while an another window is covering it, so the flicker isn't seen
            top = self.topBuffer.pop()
            top.attributes('-topmost', True)  # .ATTRIBUTES MUST BE CALLED BEFORE .GEOMETRY (TOOK ME 1 HOUR TO FIGURE OUT)
            top.geometry("170x%s+%s+%s" % (sqSize, int(self.head.x) * sqSize, int(self.head.y) * sqSize))
            self.topBuffer[-1].geometry("170x%s+%s+%s" % (sqSize, int(self.head.x) * sqSize, int(self.head.y) * sqSize))
            self.toplevels.appendleft(top)
            self.topBuffer.appendleft(genNewTop())
            # shorten snake if too long
            if len(self.body) > self.length:
                self.body.pop()
                top = self.toplevels.pop()
                top.destroy()
            #check if snake collides with itself
            for x in range(1, len(self.body)):
                if self.body[x] == self.head:
                    self.dead = True  # Use this instead of self.reset to trigger the nice death animation
                    break
            # to detect when the snake leaves the screen
            if not isRectInRect(vec(-1, -1), vec(root.winfo_screenwidth(), root.winfo_screenheight()),
                                self.head * sqSize, self.head * sqSize + vec(170, 69)):
                self.dead = True
            # collision detection for apple
            if doRectOverlap(self.head * sqSize, self.head * sqSize + vec(170, 69),
                             self.apple * sqSize, self.apple * sqSize + vec(90, 38)):
                self.length += 1
                self.apple = getApple(self.body)
                self.appleTop.geometry("+%s+%s" % (int(self.apple.x * sqSize), int(self.apple.y * sqSize)))
        elif self.dead:
            # for a nice death animation
            self.topBuffer[-1].geometry("+10000+0")
            top = self.toplevels.popleft()
            # destroy one window per 70ms
            top.destroy()
            if not len(self.toplevels) == 0:
                root.after(70, self.update)
                return
            else:
                self.reset()
        root.after(int(1000 / fps), self.update)

if __name__ == '__main__':
    # start collecting keyboard events
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    root = tk.Tk()
    snake = Snake()
    root.withdraw() # hide root window
    root.mainloop()
