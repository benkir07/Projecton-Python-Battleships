import tkMessageBox
import Tkinter
import socket
from random import randint
import pickle
import select
import pygame
import pygame.gfxdraw


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


class EntryWithPlaceholder(Tkinter.Entry):
    def put_placeholder(self):
        self.delete(0, Tkinter.END)
        self.insert(0, self.placeholder)
        self.config(fg=self.placeholder_color)

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', Tkinter.END)
            self.config(fg=self.default_fg_color)

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

    def __init__(self, placeholder="PLACEHOLDER", placeholder_color="dimgray", defcolor="black", textvariable=None, name=None):
        super(EntryWithPlaceholder, self).__init__(textvariable=textvariable, name=name)

        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_fg_color = defcolor

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()


def connect(client_socket, connected, name, ip, port):
    try:
        if name == "name" or name == "":
            tkMessageBox.showerror("Error", "Insert name please")
        else:
            client_socket.append(socket.create_connection((ip, int(port))))
            connected[0] = True
    except:
        tkMessageBox.showerror("Error", "Could not connect")


def label(text, size, pos, color=(255, 255, 255)):
    myFont = pygame.font.SysFont("Calibri", size)
    myText = myFont.render(text, 1, color)
    screen.blit(myText, pos)


def mini_game(client_socket):
    pygame.display.set_caption("MiniGame")
    background = pygame.image.load("img/MiniGame.png")
    ship = pygame.image.load("img/MiniShip.png")
    pos = (randint(95, 780), randint(150, 440))
    score = 0

    while True:
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
            if data == "":
                raise Exception("Disconnected")
            elif data == "start":
                return


def create_board():
    pygame.display.set_caption("Create Your Board")
    background = pygame.image.load("img/Create.png")
    submit = Button(screen, (30, 60, 200), 80, 444, 160, 75,  "Submit", (255, 255, 255), (30, 60, 100))
    ships = [Battleship(0, screen, 125, 140, 2), Battleship(1, screen, 125-slotwidth/2, 190, 3), Battleship(2, screen, 125-slotwidth/2, 240, 3), Battleship(3, screen, 125-slotwidth, 290, 4), Battleship(4, screen, 125-slotwidth*1.5, 340, 5)]
    #ships = [ships[0]] #line for testing
    focused = None
    board = []
    for x in xrange(10):
        board.append([])
        for y in xrange(10):
            board[-1].append("")

    finish = False
    while not finish:
        screen.blit(background, (0, 0))
        label("Place your battleships", 48, (240, 55))
        submit.draw()
        screen.blit(visualBoard, (430, 140))
        map(Battleship.draw, ships)
        if focused != None:
            focused.draw()
            pygame.draw.rect(screen, (255, 0, 0), focused.rect, 1)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise Exception("Close")
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
        if submit.pressed():
            finish = True
            for ship in ships:
                if ship.place == None:
                    finish = False
    return board, ships


def present_board(ships, board, guesses, opName, opShips = None):
    screen.blit(pygame.image.load("img/Turn.png"), (0, 0))
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


def game():
    client_socket = []
    connected = [False]
    nameEntry.put_placeholder()
    ipEntry.put_placeholder()
    portEntry.put_placeholder()

    if gui.state() == "withdrawn":
        gui.deiconify()
    connectButton.config(command=lambda: connect(client_socket, connected, name.get(), ip.get(), port.get()))


    while (not connected[0]) and (gui.state() != "withdrawn"):
        gui.lift()
        ip.set(ip.get()[:15])
        port.set(port.get()[:5])
        name.set(name.get()[:12])
        gui.update()
    gui.withdraw()

    if connected[0]:
        try:
            client_socket = client_socket[0]
            client_socket.sendall(name.get())
            mini_game(client_socket)
            board, ships = create_board()
            client_socket.sendall(pickle.dumps(board))
            guesses = []
            for x in xrange(10):
                guesses.append([])
                for y in xrange(10):
                    guesses[-1].append("")

            mini_game(client_socket)

            newShips = []
            map(lambda ship: newShips.append((ship.place, ship.horizontal, ship.width)), ships)
            client_socket.sendall(pickle.dumps(newShips))

            opName = client_socket.recv(1024)
            client_socket.sendall("got name")

            finish = False
            while not finish:
                role = client_socket.recv(1024)
                if role == "shoot":
                    shoot(ships, board, guesses, client_socket, opName)

                    guesses = pickle.loads(client_socket.recv(1024))
                    client_socket.sendall("updated")

                    state = "s" + client_socket.recv(1024)
                elif role == "watch":
                    watch(ships, board, guesses, client_socket, opName)

                    board = pickle.loads(client_socket.recv(1024))
                    client_socket.sendall("updated")

                    state = "w" + client_socket.recv(1024)
                if state[1:] == "win":
                    present_board(ships, board, guesses, opName, pickle.loads(client_socket.recv(1024)))
                    show_state(state)
                    con = Button(screen, (30, 60, 200), 750, 40, 160, 60, "Back to main menu", (255, 255, 255), (30, 60, 100), 20)
                    while not finish:
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

        except Exception as ex:
            print repr(ex)
            if ex.message == ("Close"):
                client_socket.close()
                exit()
            tkMessageBox.showerror("Disconnected", "Your opponent has disconnected")
        client_socket.close()
    connected[0] = False


def rules():
    page = 0
    back = Button(screen, (30, 60, 200), 225, 400, 500, 70, "Back to main menu", (255, 255, 255), (30, 60, 100), 40)
    finish = False
    while not finish:
        screen.blit(RULES[page], (0, 0))
        if page == 2:
            back.draw()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                finish = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Surface.get_at(screen, event.pos) == (91, 155, 213):
                    if event.pos[0] > 888:
                        page += 1
                    if event.pos[0] < 70:
                        page -= 1
        if back.pressed():
            finish = True


#constants
slotwidth = 36
visualBoard = pygame.Surface((slotwidth*10 ,slotwidth*10))
for y in xrange(0, slotwidth*10, slotwidth):
    for x in xrange(0, slotwidth*10, slotwidth):
        pygame.draw.rect(visualBoard, (30, 60, 200), pygame.Rect(x, y, slotwidth, slotwidth))
        pygame.draw.rect(visualBoard, (255, 255, 255), pygame.Rect(x, y, slotwidth, slotwidth), 1)
RULES = (pygame.image.load("img/Rules1.png"), pygame.image.load("img/Rules2.png"),
    pygame.image.load("img/Rules3.png"))
EXPLOSION_IMAGES = (pygame.image.load("img/blowup1.png"), pygame.image.load("img/blowup2.png"),
    pygame.image.load("img/blowup3.png"), pygame.image.load("img/blowup4.png"),
    pygame.image.load("img/blowup5.png"), pygame.image.load("img/blowup6.png"))
signs = (pygame.image.load("img/Hit.png"), pygame.image.load("img/Miss.png"))
gui = Tkinter.Tk()
gui.title("Connection Menu")
gui.geometry("200x200+200+200")
gui.protocol("WM_DELETE_WINDOW", lambda: gui.withdraw())
name = Tkinter.StringVar()
ip = Tkinter.StringVar()
port = Tkinter.StringVar()
Tkinter.Label(text="Username:").pack()
nameEntry = EntryWithPlaceholder(placeholder="name", textvariable=name)
nameEntry.pack()
Tkinter.Label(text="Server ip:").pack()
ipEntry = EntryWithPlaceholder(placeholder="127.0.0.1", textvariable=ip)
ipEntry.pack()
Tkinter.Label(text="Server port:").pack()
portEntry = EntryWithPlaceholder(placeholder="12345", textvariable=port)
portEntry.pack()
connectButton = Tkinter.Button(text="Connect")
connectButton.pack()
#

pygame.init()
screen = pygame.display.set_mode((960, 540))
title = Button(screen, (0, 0, 0), 300, 25, 360, 100, "Battleships", (255, 255, 255), font_size=80)
play = Button(screen, (30, 60, 200), 380, 165, 190, 70, "Play", (255, 255, 255), (30, 60, 100), 65)
rulesButton = Button(screen, (30, 60, 200), 380, 275, 190, 70, "Rules", (255, 255, 255), (30, 60, 100), 65)
exitButton = Button(screen, (30, 60, 200), 380, 375, 190, 70, "Exit", (255, 255, 255), (30, 60, 100), 65)

finish = False
while not finish:
    pygame.display.set_caption("Battleships")
    screen.blit(pygame.image.load("img/Main.png"), (0, 0))
    map(Button.draw, [title, play, rulesButton, exitButton])
    pygame.display.update()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            finish = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if play.highlighted:
                game()
            elif rulesButton.highlighted:
                rules()
            elif exitButton.highlighted:
                finish = True

pygame.quit()
