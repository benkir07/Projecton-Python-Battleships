# -*- coding: utf-8 -*-

import os
import tkMessageBox
import Tkinter
import socket
from random import randint
import pickle
import select
import thread
from ctypes import POINTER, WINFUNCTYPE, windll
from ctypes.wintypes import BOOL, HWND, RECT
import urllib
import zipfile
os.system("pip install pygame")
os.system("pip install psutil")
os.system("pip install ipcalc")
os.system("pip install six")
import pygame
import pygame.gfxdraw
import psutil
import ipcalc


class Button(object):
    def __init__(self, surface, color, x, y, width, height, text, text_color, color2=None, font_size=None):
        self.surface = surface
        self.color = color
        self.color2 = color2
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.text_color = text_color
        if font_size == None:
            self.font_size = int(self.rect[2] // len(self.text))
        else:
            self.font_size = font_size

    def draw(self):
        pygame.draw.rect(self.surface, self.color, self.rect, 0)
        if self.color2 != None and self.highlighted:
            pygame.draw.rect(self.surface, self.color2, self.rect, 0)
        pygame.draw.rect(self.surface, (190,190,190), self.rect, 1)

        myFont = pygame.font.SysFont("Calibri", self.font_size)
        myText = myFont.render(self.text, 1, self.text_color)
        self.surface.blit(myText, ((self.rect[0] + self.rect[2] / 2) - myText.get_width() / 2, (self.rect[1] + self.rect[3] / 2) - myText.get_height() / 2))

    def pressed(self):
        return pygame.mouse.get_pressed()[0] and self.highlighted

    @property
    def highlighted(self):
        x = pygame.mouse.get_pos()[0]
        y = pygame.mouse.get_pos()[1]
        if x > self.rect.topleft[0] and y > self.rect.topleft[1]:
            if x < self.rect.bottomright[0] and y < self.rect.bottomright[1]:
                return True
        return False


class Battleship(Button):
    def __init__(self, ID, surface, x, y, width, name=""):
        if name == "":
            name = str(width)
        super(Battleship, self).__init__(surface, (255, 255, 255), x, y, width * slotwidth - 4, slotwidth-4, name, (0, 0, 0), font_size=30)
        self.defX = x
        self.defY = y
        self.width = width
        self.horizontal = True
        self.place = None
        self.ID = ID

    def default(self, board):
        self.rect[0] = self.defX
        self.rect[1] = self.defY
        if self.rect[2] < self.rect[3]:
            self.rect[2], self.rect[3] = self.rect[3], self.rect[2]
        self.horizontal = True
        self.place = None
        self.remove(board)

    def remove(self, board):
        for row in board:
            for index in xrange(len(row)):
                if row[index] == self.ID:
                    row[index] = ""

    def flip(self):
        self.rect[2], self.rect[3] = self.rect[3], self.rect[2]
        self.horizontal = not self.horizontal


class ConnectionMenu(Tkinter.Tk):
    def __init__(self):
        Tkinter.Tk.__init__(self)
        self.title("Connection Menu")
        self.geometry("200x200")
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        self.name = Tkinter.StringVar()
        self.ip = Tkinter.StringVar()
        self.port = Tkinter.StringVar()
        Tkinter.Label(self, text="Username:").pack()
        self.name_entry = Tkinter.Entry(self, textvariable=self.name)
        self.name_entry.pack()
        Tkinter.Label(self, text="Server ip:").pack()
        self.ip_entry = Tkinter.Entry(self, textvariable=self.ip)
        self.ip_entry.pack()
        Tkinter.Label(self, text="Server port:").pack()
        self.port_entry = Tkinter.Entry(self, textvariable=self.port)
        self.port_entry.pack()
        Tkinter.Button(self, text="Connect", command=self.connect).pack()

    def connect(self):
        try:
            self.name.get().decode("ascii")
            try:
                if self.name.get() == "":
                    tkMessageBox.showerror("Error", "Insert name please")
                else:
                    client_socket[0] = socket.create_connection((self.ip.get(), int(self.port.get())))
                    connected[0] = True
                    client_socket[0].send(self.name.get())
                    self.name.set(client_socket[0].recv(1024))
            except Exception as ex:
                print repr(ex)
                tkMessageBox.showerror("Error", "Could not connect")
        except:
            tkMessageBox.showerror("Error", "Username can be only letters and numbers")

    def limit(self):
        self.ip.set(self.ip.get()[:15])
        self.port.set(self.port.get()[:5])
        self.name.set(self.name.get()[:12])


class LobbyApp(Tkinter.Tk):
    height = 540
    width = 800

    def __init__(self, client_socket):
        Tkinter.Tk.__init__(self)
        self.resizable(0, 0)
        self.client_socket = client_socket
        self.lobbies = Lobby(self, self.height, self.width-200, self.client_socket)
        self.chat = Chat(self, self.height, 200)
        self.lobbies.pack(side=Tkinter.LEFT)
        self.chat.pack(side=Tkinter.RIGHT)
        self.room = ""

    def mainloop(self):
        self.up = True
        self.deiconify()
        self.title("Lobby")
        self.geometry(str(self.width) + "x" + str(self.height))
        self.protocol("WM_DELETE_WINDOW", lambda: self.withdraw())
        self.lobbies.set_lobby()
        while self.up and self.state() != "withdrawn":
            self.update()
            self.chat.update()
            self.lobbies.update()
            rlist, wlist, xlist = select.select([self.client_socket], [], [], 0)
            for sock in rlist:
                data = sock.recv(1024)
                if data == "start":
                    self.up = False
                elif self.room == "":
                    if data.split(";")[0] == "new":
                        self.lobbies.set_lobby()
                else:
                    self.lobbies.room_connected.set("Connected:\n" + data)
                    self.lobbies.ready.place(x=self.lobbies.ready.x, y=self.lobbies.ready.y)
                    if len(data.split("\n")) == 2:
                        self.lobbies.ready.config(state=Tkinter.NORMAL)
                    else:
                        self.lobbies.ready.config(state=Tkinter.DISABLED)
                self.lift()
        if self.state() == "withdrawn":
            self.client_socket.close()
            self.chat.close()
            quit()
        self.withdraw()


class Lobby(Tkinter.Frame):
    def __init__(self, master, height, width, client_socket):
        Tkinter.Frame.__init__(self, master, height=height, width=width)
        self.master = master
        self.client_socket = client_socket
        self.width = width
        self.height = height
        self.room_connected = Tkinter.StringVar(self)
        self.room_connected.set("Connected:\n")

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def new_room(self):
        self.temp_gui = Tkinter.Tk()
        self.temp_gui.geometry("200x200")
        self.temp_gui.resizable(0, 0)
        self.temp_gui.title("New Room")
        self.temp_gui.protocol("WM_DELETE_WINDOW", self.temp_gui.withdraw)
        room = Tkinter.StringVar(self.temp_gui)
        room.set(globals()['connection_menu'].name.get() + "\'s room")
        password = Tkinter.StringVar(self.temp_gui)
        Tkinter.Label(self.temp_gui, text="Room Name:").pack()
        Tkinter.Entry(self.temp_gui, textvariable=room).pack()
        Tkinter.Label(self.temp_gui, text="Password(empty=no password):").pack()
        pass_entry = Tkinter.Entry(self.temp_gui, textvariable=password, show="•")
        pass_entry.pack()
        Tkinter.Button(self.temp_gui, text="Create", command=lambda: self.create(room.get() + ";" + password.get())).pack()
        self.temp_gui.update()
        show = Tkinter.Button(self.temp_gui, text="Show")
        show.bind("<Button-1>", lambda *args: pass_entry.config(show=""))
        show.bind("<ButtonRelease-1>", lambda *args: pass_entry.config(show="•"))
        show.place(x=pass_entry.winfo_x()+pass_entry.winfo_width()-30, y=pass_entry.winfo_y(), width=30, height=pass_entry.winfo_height())
        self.master.withdraw()

        self.temp_gui.lift()
        while self.temp_gui.state() != "withdrawn":
            rlist, wlist, xlist = select.select([self.client_socket], [], [], 0)
            for sock in rlist:
                sock.recv(1024)
            room.set(room.get()[:20])
            password.set(password.get()[:14])
            self.temp_gui.update()
        self.master.deiconify()
        if self.master.room == "":
            self.set_lobby()
        self.master.lift()

    def create(self, data):
        self.client_socket.send("new;" + data)
        self.client_socket.recv(1024)
        self.master.room = data.split(";")[0]
        self.temp_gui.withdraw()
        self.set_room()

    def set_lobby(self):
        self.clear()
        Tkinter.Label(self, text="Open Rooms:").place(height=20)
        Tkinter.Button(self, text="Create Room", command=self.new_room).place(x=3 * (self.width - 15) / 5, height=20)
        Tkinter.Button(self, text="Join Room", command=self.join).place(x=4 * (self.width - 15) / 5, height=20)
        Tkinter.Label(self, text="Room Name:").place(y=20, height=20)
        Tkinter.Label(self, text="Players:").place(x=(self.width - 15) / 3, y=20, height=20)
        Tkinter.Label(self, text="Requires Password?:").place(x=2 * (self.width - 15) / 3, y=20, height=20)
        self.rooms_scrollbar = Tkinter.Scrollbar(self, command=self.rooms_scroll)
        self.rooms_names = Tkinter.Listbox(self, yscrollcommand=self.rooms_mouse_wheel, exportselection=0)
        self.rooms_players = Tkinter.Listbox(self, yscrollcommand=self.rooms_mouse_wheel, exportselection=0)
        self.rooms_password = Tkinter.Listbox(self, yscrollcommand=self.rooms_mouse_wheel, exportselection=0)
        self.rooms_scrollbar.place(x=self.width - 15, y=40, height=(self.height - 60) / 2, width=15)
        self.rooms_names.place(y=40, height=(self.height - 60) / 2, width=(self.width - 15) / 3)
        self.rooms_players.place(x=(self.width - 15) / 3, y=40, height=(self.height - 60) / 2, width=(self.width - 15) / 3)
        self.rooms_password.place(x=2 * (self.width - 15) / 3, y=40, height=(self.height - 60) / 2, width=(self.width - 15) / 3)

        Tkinter.Label(self, text="Ongoing Games:").place(y=40 + (self.height - 60) / 2, height=20)
        self.games_scrollbar = Tkinter.Scrollbar(self)
        self.games_list = Tkinter.Listbox(self, yscrollcommand=self.games_scrollbar.set)
        self.games_scrollbar.config(command=self.games_list.yview)
        self.games_scrollbar.place(x=self.width - 15, y=60 + (self.height - 60) / 2, height=(self.height - 60) / 2, width=15)
        self.games_list.place(y=60 + (self.height - 60) / 2, height=(self.height - 60) / 2, width=self.width - 15)

        self.client_socket.send("get;")
        data = self.client_socket.recv(1024)
        try:
            rooms, games = data.split("@")
        except:
            data = self.client_socket.recv(1024)
            rooms, games = data.split("@")
        if rooms != "empty":
            for room in rooms.split("\n"):
                room = room.split(";")
                self.rooms_names.insert(Tkinter.END, room[0])
                self.rooms_players.insert(Tkinter.END, room[1])
                self.rooms_password.insert(Tkinter.END, room[2])
        if games != "empty":
            for game in games.split("\n"):
                self.games_list.insert(Tkinter.END, game)

    def set_room(self):
        self.clear()
        title = Tkinter.Label(self, text=self.master.room, font="Ariel 24 bold")
        title.place(x=self.width/2)
        self.master.update()
        title.place(x=self.width/2-title.winfo_width()/2)
        connected = Tkinter.Label(self, textvariable=self.room_connected, font="Ariel 18")
        connected.place(x=self.width/2, y=title.winfo_height())
        self.master.update()
        connected.place(x=self.width/2-connected.winfo_width()/2, y=title.winfo_height())
        leave = Tkinter.Button(self, text="Leave Room", command=self.leave)
        leave.place(y=title.winfo_height()+connected.winfo_height()+100)
        self.master.update()
        leave.place(x=self.width/2-leave.winfo_width()/2, y=title.winfo_height()+connected.winfo_height()+100)
        self.ready = Tkinter.Button(self, text="Ready", command=self.ready_click, state=Tkinter.DISABLED)
        self.ready.place(y=title.winfo_height() + connected.winfo_height() + 100)
        self.master.update()
        self.ready.x = self.width/2-self.ready.winfo_width()/2
        self.ready.y = title.winfo_height()+connected.winfo_height()+100+leave.winfo_height()
        self.ready.place(x=self.ready.x, y=self.ready.y)
        self.client_socket.sendall("getRoom;")

    def ready_click(self):
        self.client_socket.sendall("ready;")
        self.ready.place_forget()

    def join(self):
        if len(self.rooms_names.curselection()) > 0:
            if len(self.rooms_players.get(self.rooms_players.curselection()[0]).split(",")) == 1:
                if self.rooms_password.get(self.rooms_password.curselection()[0]) == "True":
                    room = str(self.rooms_names.curselection()[0])
                    self.temp_gui = Tkinter.Tk()
                    self.temp_gui.geometry("200x200")
                    self.temp_gui.resizable(0, 0)
                    self.temp_gui.title("New Room")
                    self.temp_gui.protocol("WM_DELETE_WINDOW", self.temp_gui.withdraw)
                    self.password = Tkinter.StringVar(self.temp_gui)
                    Tkinter.Entry(self.temp_gui, text=self.rooms_names.get(room)+":")
                    Tkinter.Label(self.temp_gui, text="Password:").pack()
                    pass_entry = Tkinter.Entry(self.temp_gui, textvariable=self.password, show="•")
                    pass_entry.pack()
                    Tkinter.Button(self.temp_gui, text="Join", command=lambda: self.send_req(room)).pack()
                    self.temp_gui.update()
                    show = Tkinter.Button(self.temp_gui, text="Show")
                    show.bind("<Button-1>", lambda *args: pass_entry.config(show=""))
                    show.bind("<ButtonRelease-1>", lambda *args: pass_entry.config(show="•"))
                    show.place(x=pass_entry.winfo_x()+pass_entry.winfo_width()-30, y=pass_entry.winfo_y(), width=30,height=pass_entry.winfo_height())
                    self.master.withdraw()

                    self.temp_gui.lift()
                    while self.temp_gui.state() != "withdrawn":
                        rlist, wlist, xlist = select.select([self.client_socket], [], [], 0)
                        for sock in rlist:
                            sock.recv(1024)
                            self.password.set(self.password.get()[:14])
                        self.temp_gui.update()
                    self.master.deiconify()
                    if self.master.room == "":
                        self.set_lobby()
                    self.master.lift()
                else:
                    self.client_socket.sendall("join;"+str(self.rooms_password.curselection()[0]))
                    self.client_socket.recv(1024)
                    self.master.room = self.rooms_names.get(self.rooms_names.curselection()[0])
                    self.set_room()
            else:
                tkMessageBox.showerror("Error", "Room full")

    def send_req(self, room):
        self.client_socket.sendall("join;"+room+";"+self.password.get())
        self.password.set("")
        data = self.client_socket.recv(1024)
        if data == "True":
            self.master.room = self.rooms_names.get(self.rooms_names.curselection()[0])
            self.temp_gui.withdraw()
            self.set_room()
        else:

            tkMessageBox.showerror("Error", "Wrong password")

    def leave(self):
        self.client_socket.sendall("leave;")
        self.client_socket.recv(1024)
        self.set_lobby()
        self.master.room = ""
        self.master.gui_room = False

    def rooms_scroll(self, *args):
        self.rooms_names.yview(*args)
        self.rooms_players.yview(*args)
        self.rooms_password.yview(*args)

    def rooms_mouse_wheel(self, *args):
        self.rooms_scrollbar.set(*args)
        self.rooms_scroll("moveto", str(args[0]))

    def update(self):
        if self.focus_get() == self.rooms_names or self.focus_get() == self.rooms_players or self.focus_get() == self.rooms_password:
            if len(self.focus_get().curselection()) > 0:
                num = self.focus_get().curselection()[0]
                self.rooms_names.selection_clear(0, Tkinter.END)
                self.rooms_players.selection_clear(0, Tkinter.END)
                self.rooms_password.selection_clear(0, Tkinter.END)
                self.rooms_names.select_set(num)
                self.rooms_players.select_set(num)
                self.rooms_password.select_set(num)


class Chat(Tkinter.Frame):
    def __init__(self, master, height, width):
        Tkinter.Frame.__init__(self, master, height=height, width=width, name="chat")
        self.master = master
        self.chat_socket = socket.create_connection((connection_menu.ip.get(), 12347))
        self.chat_socket.send(connection_menu.name.get())
        self.message_scroll = Tkinter.Scrollbar(self)
        self.messages = Tkinter.Listbox(self, yscrollcommand=self.message_scroll.set)
        self.message_scroll.config(command=self.messages.yview)
        self.message_scroll.place(x=width - 15, height=height - 20, width=15)
        self.messages.place(height=height - 20, width=width - 15)

        self.message = Tkinter.StringVar(self)
        self.message_box = Tkinter.Entry(self, textvariable=self.message)
        self.message_box.place(y=height - 20, height=20, width=width * 0.6)
        self.message_box.bind("<Return>", self.send)

        self.length = Tkinter.StringVar(self)
        self.length_box = Tkinter.Label(self, textvariable=self.length)
        self.length_box.place(x=width * 0.6, y=height - 20, height=20, width=width * 0.2)

        self.send_button = Tkinter.Button(self, text="Send", command=self.send)
        self.send_button.place(x=width * 0.8, y=height - 20, height=20, width=width * 0.2)
        self.send_button.bind("<Return>", self.send)

    def send(self, event=None):
        if self.message.get().replace(" ", "") != "":
            self.chat_socket.send(self.message.get().encode("utf-8"))
        self.message.set("")

    def update(self):
        rlist, wlist, xlist = select.select([self.chat_socket], [], [], 0)
        for current_socket in rlist:
            data = current_socket.recv(1024).decode("utf-8")
            if data == "":
                tkMessageBox.showerror("Disconnect", "Disconnected from server")
                self.master.withdraw()
            else:
                for msg in data.split("\n")[:-1]:
                    self.messages.insert(Tkinter.END, msg)
                    self.messages.select_set(Tkinter.END)
                    self.messages.yview(Tkinter.END)
        self.message.set(self.message.get()[:50])
        self.length.set(str(50 - len(self.message.get())) + "/50")
        self.messages.selection_clear(0, Tkinter.END)

    def close(self):
        self.chat_socket.close()


def label(text, size, pos, color=(255, 255, 255)):
    myFont = pygame.font.SysFont("Calibri", size)
    myText = myFont.render(text, 1, color)
    screen.blit(myText, pos)


def mini_game(client_socket):
    pygame.display.set_caption("MiniGame")
    background = pygame.image.load("media/MiniGame.png")
    ship = pygame.image.load("media/MiniShip.png")
    pos = (randint(95, 780), randint(150, 440))
    score = 0

    while True:
        game_chat()
        screen.blit(background, (0, 0))
        label("Score: " + str(score), 20, (120, 150), (0, 0, 0))
        label("Waiting for other player", 48, (240, 50))
        label("Catch the ship", 20, (400, 460), (0, 0, 0))
        screen.blit(ship, pos)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise Exception("Close")
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.pos[0] > pos[0] and event.pos[0] < pos[0] + ship.get_width():
                    if event.pos[1] > pos[1] and event.pos[1] < pos[1] + ship.get_height():
                        score += 1
                        pos = (randint(95, 780), randint(150, 440))
        rlist, wlist, xlist = select.select([client_socket], [], [], 0)
        for sock in rlist:
            data = sock.recv(1024)
            if data == "disconnect;":
                raise Exception
            elif data == "start":
                return


def create_board_helper(finish, ships, board):
    global focused, exit
    while not finish[0]:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit = True
                if event.type == pygame.MOUSEBUTTONUP:
                    if focused == None:
                        for ship in ships:
                            if ship.highlighted:
                                ship.flip()
                                focused = ship
                                break
                    if focused != None:
                        focused.remove(board)
                        if focused.rect[0] + slotwidth / 4 < 430 or focused.rect[1] + slotwidth / 4 < 140 or focused.rect[
                            0] + focused.rect[2] - slotwidth / 4 > 430 + slotwidth * 10 or focused.rect[1] + focused.rect[
                            3] - slotwidth / 4 > 140 + slotwidth * 10:
                            focused.default(board)
                        else:
                            focused.place = (int(round((focused.rect[0] - 430.0)) / slotwidth),
                                             int(round((focused.rect[1] - 140.0) / slotwidth)))
                            legal = True
                            for x in xrange(focused.width):
                                if focused.horizontal:
                                    if board[focused.place[1]][focused.place[0] + x] != "":
                                        legal = False
                                elif board[focused.place[1] + x][focused.place[0]] != "":
                                    legal = False
                            if legal:
                                for x in xrange(focused.width):
                                    if focused.horizontal:
                                        board[focused.place[1]][focused.place[0] + x] = focused.ID
                                    else:
                                        board[focused.place[1] + x][focused.place[0]] = focused.ID
                                focused.rect[0] = focused.place[0] * slotwidth + 432
                                focused.rect[1] = focused.place[1] * slotwidth + 142
                            else:
                                focused.default(board)
                    focused = None
                if event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                    if focused == None:
                        for ship in ships:
                            if ship.pressed():
                                focused = ship
                    else:
                        focused.rect[0] += event.rel[0]
                        focused.rect[1] += event.rel[1]
        except:
            pass


def create_board(client_socket):
    pygame.display.set_caption("Create Your Board")
    background = pygame.image.load("media/Create.png")
    submit = Button(screen, (30, 60, 200), 80, 444, 160, 75,  "Submit", (255, 255, 255), (30, 60, 100))
    ships = [Battleship(0, screen, 125, 140, 2), Battleship(1, screen, 125-slotwidth/2, 190, 3), Battleship(2, screen, 125-slotwidth/2, 240, 3), Battleship(3, screen, 125-slotwidth, 290, 4), Battleship(4, screen, 125-slotwidth*1.5, 340, 5)]
    #ships = [ships[0]] #line for testing
    global focused
    focused = None
    board = []
    for x in xrange(10):
        board.append([])
        for y in xrange(10):
            board[-1].append("")

    finish = [False]
    global exit
    exit = False
    thread.start_new_thread(create_board_helper, (finish, ships, board))
    while not finish[0]:
        game_chat()
        rlist, wlist, xlist = select.select([client_socket], [], [], 0)
        for sock in rlist:
            if sock.recv(1024) == "disconnect;":
                finish[0] = True
                raise Exception
        screen.blit(background, (0, 0))
        label("Place your battleships", 48, (240, 55))
        submit.draw()
        screen.blit(visualBoard, (430, 140))
        map(Battleship.draw, ships)
        if focused != None:
            pygame.draw.rect(screen, (255, 0, 0), focused.rect, 1)
        pygame.display.update()
        if submit.pressed():
            finish[0] = True
            for ship in ships:
                if ship.place == None:
                    finish[0] = False
        if exit:
            raise Exception("Close")
    return board, ships


def present_board(ships, board, guesses, opName, opShips = None):
    screen.blit(pygame.image.load("media/Turn.png"), (0, 0))
    label("Your board", 20, (165, 110))
    label(str((12 - len(opName)) * " " + "{}'s board" + (12 - len(opName)) * " ").format(opName), 20, (650, 110))
    screen.blit(visualBoard, (45, 150))
    screen.blit(visualBoard, (555, 150))
    for ship in ships:
        ship.rect[0] = 47 + ship.place[0] * slotwidth
        ship.rect[1] = 152 + ship.place[1] * slotwidth
        ship.draw()
    if opShips != None:
        for ship in opShips:
            temp = pygame.Rect(ship[0][0] * slotwidth + 557, ship[0][1] * slotwidth + 152, ship[2] * slotwidth - 4, slotwidth - 4)
            if not ship[1]:
                temp[2], temp[3] = temp[3], temp[2]
            pygame.gfxdraw.box(screen, temp, (255, 255, 255, 127))
    for x in range(10):
        for y in range(10):
            if board[y][x] == "hit":
                screen.blit(signs[0], (x * slotwidth + 45, y * slotwidth + 150))
            elif board[y][x] == "miss":
                screen.blit(signs[1], (x * slotwidth + 45, y * slotwidth + 150))
    for x in range(10):
        for y in range(10):
            if guesses[y][x] == "hit":
                screen.blit(signs[0], (x * slotwidth + 555, y * slotwidth + 150))
            elif guesses[y][x] == "miss":
                screen.blit(signs[1], (x * slotwidth + 555, y * slotwidth + 150))
    for ship in guesses[10:]:
        x = ship[0][0] * slotwidth + 555
        y = ship[0][1] * slotwidth + 150
        if ship[1]:
            width = ship[2] * slotwidth
            height = slotwidth
        else:
            width = slotwidth
            height = ship[2] * slotwidth
        pygame.draw.rect(screen, (255, 0, 0), pygame.Rect(x - 1, y - 1, width + 1, height + 1), 2)


def shoot(ships, board, guesses, client_socket, opName):
    pygame.display.set_caption("Shoot")
    present_board(ships, board, guesses, opName)
    label("Where would you like to shoot?", 24, (300, 80))
    show_state("s")
    pygame.display.update()

    while True:
        game_chat()
        rlist, wlist, xlist = select.select([client_socket], [], [], 0)
        for sock in rlist:
            if sock.recv(1024) == "disconnect;":
                raise Exception
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise Exception("Close")
            if event.type == pygame.MOUSEBUTTONDOWN:
                if 555 < event.pos[0] < 555 + slotwidth * 10:
                    if 150 < event.pos[1] < 150 + slotwidth * 10:
                        x = int(round((event.pos[0] - 555) / slotwidth))
                        y = int(round((event.pos[1] - 150) / slotwidth))
                        if guesses[y][x] == "":
                            for image in EXPLOSION_IMAGES:
                                image = pygame.transform.scale(image, (slotwidth, slotwidth))
                                screen.blit(image, (x * slotwidth + 555, y * slotwidth + 150))
                                pygame.display.update()
                                pygame.time.Clock().tick(10)
                            client_socket.sendall(pickle.dumps((x, y)))
                            return


def watch(ships, board, guesses, client_socket, opName, state="w"):
    pygame.display.set_caption("Watch")
    present_board(ships, board, guesses, opName)
    show_state(state)
    pygame.display.update()

    while True:
        game_chat()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise Exception("Close")
        rlist, wlist, xlist = select.select([client_socket], [], [], 0)
        if len(rlist):
            return True


def show_state(state):
    if state[0] == "s":
        label("Your Turn", 36, (400, 45))
        if state[1:] == "miss":
            label("You missed!", 20, (420, 85))
        elif state[1:] == "hit":
            label("You've hit an enemy ship!", 20, (370, 85))
        elif state[1:] == "ship is down":
            label("Ship is down!", 20, (415, 85))
        elif state[1:] == "win":
            label("Victory!", 28, (430, 80))
    else:
        label("Opponent's turn", 36, (330, 45))
        if state[1:] == "miss":
            label("Your opponent missed!", 20, (360, 85))
        elif state[1:] =="hit":
            label("A ship has been damaged!", 20, (330, 85))
        elif state[1:] == "ship is down":
            label("Ship is down!", 20, (405, 85))
        elif state[1:] == "win":
            label("Defeat!", 28, (410, 80))
    if state[1:] != "":
        if state[1:] == "miss":
            pygame.mixer.music.load("media/splash.mp3")
        else:
            pygame.mixer.music.load("media/boom.mp3")
        pygame.mixer.music.play(1, 0.0)


def game_chat():
    rect = GetWindowRect(pygame.display.get_wm_info()["window"])
    lobby_gui.geometry("200x540+" + str(rect.right) + "+" + str(rect.top))
    lobby_gui.update()
    lobby_gui.chat.update()


def game(client_socket):
    lobby_gui.title("Chat")
    lobby_gui.lobbies.pack_forget()
    lobby_gui.chat.pack_forget()
    lobby_gui.overrideredirect(1)
    lobby_gui.geometry("200x540")
    lobby_gui.chat.pack()
    lobby_gui.deiconify()

    global screen
    pygame.init()
    screen = pygame.display.set_mode((960, 540))
    try:
        board, ships = create_board(client_socket)
        temp = []
        map(lambda ship: temp.append((ship.place, ship.horizontal, ship.width)), ships)
        client_socket.sendall(pickle.dumps(temp))
        mini_game(client_socket)

        client_socket.sendall(pickle.dumps(board))
        guesses = []
        for x in xrange(10):
            guesses.append([])
            for y in xrange(10):
                guesses[-1].append("")

        opName = client_socket.recv(1024)
        if opName == "disconnect;":
            raise Exception
        client_socket.sendall("got name")

        finish = False
        while not finish:
            role = client_socket.recv(1024)
            if role == "disconnect;":
                raise Exception
            elif role == "shoot":
                shoot(ships, board, guesses, client_socket, opName)

                guesses = pickle.loads(client_socket.recv(1024))
                if guesses == "disconnect;":
                    raise Exception
                client_socket.sendall("updated")

                state = "s" + client_socket.recv(1024)
                if state == "sdisconnect;":
                    raise Exception
            elif role == "watch":
                watch(ships, board, guesses, client_socket, opName)

                board = pickle.loads(client_socket.recv(1024))
                client_socket.sendall("updated")

                state = "w" + client_socket.recv(1024)
                if state == "disconnect;":
                    raise Exception
            if state[1:] == "win":
                present_board(ships, board, guesses, opName, pickle.loads(client_socket.recv(1024)))
                show_state(state)
                con = Button(screen, (30, 60, 200), 750, 40, 160, 60, "Back to main menu", (255, 255, 255), (30, 60, 100), 20)
                while not finish:
                    game_chat()
                    con.draw()
                    pygame.display.update()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            finish = True
                            pygame.event.post(pygame.event.Event(pygame.QUIT))
                    if con.pressed():
                        finish = True
            else:
                present_board(ships, board, guesses, opName)
                show_state(state)
                pygame.display.update()
                client_socket.sendall("ready")
                watch(ships, board, guesses, client_socket, opName, state)
        pygame.quit()
        lobby_gui.withdraw()
    except Exception as ex:
        print repr(ex)
        if ex.message == ("Close"):
            client_socket.close()
            quit()
        client_socket.sendall("no!")
        pygame.quit()
        lobby_gui.withdraw()
        tkMessageBox.showerror("Disconnected", "Your opponent has disconnected")

    lobby_gui.chat.pack_forget()
    lobby_gui.lobbies.pack(side=Tkinter.LEFT)
    lobby_gui.chat.pack(side=Tkinter.RIGHT)
    lobby_gui.overrideredirect(0)

if not os.path.exists("media"):
    urllib.urlretrieve("https://drive.google.com/uc?authuser=0&id=1u4Ji-unFkUNDYHJV98pIVaP8en6p8ce-&export=download", "media.zip")
    file = zipfile.ZipFile("media.zip")
    file.extractall()
    file.close()
    os.remove("media.zip")

#constants
slotwidth = 36
visualBoard = pygame.Surface((slotwidth*10 ,slotwidth*10))
for y in xrange(0, slotwidth*10, slotwidth):
    for x in xrange(0, slotwidth*10, slotwidth):
        pygame.draw.rect(visualBoard, (30, 60, 200), pygame.Rect(x, y, slotwidth, slotwidth))
        pygame.draw.rect(visualBoard, (255, 255, 255), pygame.Rect(x, y, slotwidth, slotwidth), 1)
EXPLOSION_IMAGES = (pygame.image.load("media/blowup1.png"), pygame.image.load("media/blowup2.png"), pygame.image.load("media/blowup3.png"), pygame.image.load("media/blowup4.png"), pygame.image.load("media/blowup5.png"), pygame.image.load("media/blowup6.png"))
signs = (pygame.image.load("media/Hit.png"), pygame.image.load("media/Miss.png"))
GetWindowRect = WINFUNCTYPE(BOOL, HWND, POINTER(RECT))(("GetWindowRect", windll.user32), ((1, "hwnd"), (2, "lprect")))
#
try:
    client_socket = [None]
    connected = [False]
    connection_menu = ConnectionMenu()


    tempSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tempSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, True)
    tempSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    tempSock.settimeout(1)
    addrs = psutil.net_if_addrs()
    keys = []
    for addr in addrs:
        if "Pseudo" in addr or "Virtual" in addr or "169.254" in addrs[addr][1].address:
            keys.append(addr)
    for key in keys:
        del addrs[key]
    addr = addrs[addrs.keys()[0]][1]
    tempSock.sendto("battleships?", (str(ipcalc.Network(addr.address, addr.netmask).broadcast()), 12346))
    tempSock.sendto("battleships?", ("37.142.182.218", 12346))
    tempSock.sendto("battleships?", ("rabinonline.ddns.net", 12346))
    try:
        data = tempSock.recvfrom(1024)
        if data[0] == "indeed":
            connection_menu.ip.set(data[1][0])
            connection_menu.port.set(12345)
    except:
        pass

    while not connected[0] and connection_menu.state() != "withdrawn":
        connection_menu.lift()
        connection_menu.limit()
        connection_menu.update()
    connection_menu.withdraw()
    if connected[0]:
        lobby_gui = LobbyApp(client_socket[0])

    while connected[0]:
        lobby_gui.mainloop()
        lobby_gui.room = ""
        game(client_socket[0])
except Exception as ex:
    print repr(ex)
