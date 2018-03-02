import socket
import pickle
import thread
import select
import Tkinter
from random import randint
import pygame



class Battleship(object):
    def __init__(self, surface, x, y, width):
        self.surface = surface
        self.rect = pygame.Rect(x, y, width * slotwidth - 4, slotwidth - 4)
        self.text = str(width)

    def draw(self):
        pygame.draw.rect(self.surface, (255, 255, 255), self.rect, 0)
        pygame.draw.rect(self.surface, (190,190,190), self.rect, 1)

        myFont = pygame.font.SysFont("Calibri", 30)
        myText = myFont.render(self.text, 1, (0, 0, 0))
        self.surface.blit(myText, ((self.rect[0] + self.rect[2] / 2) - myText.get_width() / 2, (self.rect[1] + self.rect[3] / 2) - myText.get_height() / 2))


def present_board(ships, guesses, offset):
    for ship in ships:
        temp = Battleship(screen, offset[0] + ship[0][0] * slotwidth, offset[1] + ship[0][1] * slotwidth, ship[2])
        if not ship[1]:
            temp.rect[2], temp.rect[3] = temp.rect[3], temp.rect[2]
        temp.draw()
    for x in xrange(10):
        for y in xrange(10):
            if guesses[y][x] == "hit":
                screen.blit(signs[0], (x * slotwidth + offset[0] - 2, y * slotwidth + offset[1] - 2))
            elif guesses[y][x] == "miss":
                screen.blit(signs[1], (x * slotwidth + offset[0] - 2, y * slotwidth + offset[1] - 2))
    for ship in guesses[10:]:
        temp = pygame.Rect(ship[0][0] * slotwidth + offset[0] - 3, ship[0][1] * slotwidth + offset[1] - 3, ship[2] * slotwidth + 1, slotwidth + 1)
        if not ship[1]:
            temp[2], temp[3] = temp[3], temp[2]
        pygame.draw.rect(screen, (255, 0, 0), temp, 2)


def turn(shooter, watcher, guesses, board, ships):
    shooter.sendall("shoot")
    watcher.sendall("watch")

    coords = pickle.loads(shooter.recv(1024))

    if board[coords[1]][coords[0]] == "":
        guesses[coords[1]][coords[0]] = "miss"
        board[coords[1]][coords[0]] = "miss"
        state = "miss"
    else:
        guesses[coords[1]][coords[0]] = "hit"
        ID = board[coords[1]][coords[0]]
        board[coords[1]][coords[0]] = "hit"
        found = False
        for row in board:
            if ID in row:
                found = True
        if not found:
            guesses.append(ships[ID])
            found = False
            for row in board:
                for slot in row:
                    if slot != "" and slot != "hit" and slot != "miss":
                        found = True
            if not found:
                state = "win"
            else:
                state = "ship is down"
        else:
            state = "hit"

    shooter.sendall(pickle.dumps(guesses))
    watcher.sendall(pickle.dumps(board))

    if shooter.recv(1024) == "updated" and watcher.recv(1024) == "updated":
        map(lambda sock: sock.sendall(state), [shooter, watcher])

    if state != "win":
        if shooter.recv(1024) == "ready" and watcher.recv(1024) == "ready":
            pass

    return state == "win"


def game(sockets, adresses, names, playingNames, playersListbox, gamesListBox, games):
    gameID = names[0] + " vs " + names[1]
    gamesListbox.insert(Tkinter.END, gameID)
    print "Game: " + gameID
    games[gameID] = {}
    game = games[gameID]

    game['guesses'] = [[], []]
    for x in xrange(10):
        game['guesses'][0].append([])
        game['guesses'][1].append([])
        for y in xrange(10):
            game['guesses'][0][-1].append("")
            game['guesses'][1][-1].append("")
    try:
        map(lambda sock: sock.sendall("start"), sockets)

        boards = [pickle.loads(sockets[0].recv(1024)), pickle.loads(sockets[1].recv(1024))]


        map(lambda sock: sock.sendall("start"), sockets)

        game['ships'] = [pickle.loads(sockets[0].recv(1024)), pickle.loads(sockets[1].recv(1024))]

        sockets[0].send(names[1])
        sockets[1].send(names[0])

        if sockets[0].recv(1024) == "got name" and sockets[1].recv(1024) == "got name":
            pass

        finish = False

        shooter = randint(0, 1)
        while not finish:
            game['shooter'] = names[shooter]
            finish = turn(sockets[shooter], sockets[1-shooter], game['guesses'][shooter], boards[1-shooter], game['ships'][1-shooter])
            shooter = 1 - shooter
        sockets[0].send(pickle.dumps(game['ships'][1]))
        sockets[1].send(pickle.dumps(game['ships'][0]))
    finally:
        map(lambda sock: sock.shutdown(socket.SHUT_RDWR), sockets)
        print names[0], str(adresses[0]), "disconnected"
        print names[1], str(adresses[1]), "disconnected"
        playingNames.remove(names[0])
        playingNames.remove(names[1])
        for i in xrange(playersListbox.size()):
            if playersListbox.get(i) == names[0]:
                playersListbox.delete(i)
                playersListbox.delete(i)
        for i in xrange(gamesListBox.size()):
            if gamesListBox.get(i):
                gamesListBox.delete(i)
        del games[gameID]


def insert_name(name, names, playingNames):
    if name not in names + playingNames:
        names.append(name)
    else:
        i = 0
        while name + str(i) in names + playingNames:
            i += 1
        names.append(name + str(i))


def shutdown():
    global online
    online = False


def label(text, size, pos, color=(255, 255, 255)):
    myFont = pygame.font.SysFont("Calibri", size)
    myText = myFont.render(text, 1, color)
    screen.blit(myText, pos)


server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(5)

width = 200
height = 500

gui = Tkinter.Tk()
gui.title("Battleships server")
gui.geometry("%sx%s+200+200" % (str(width), str(height)))
gui.resizable(0, 0)
gui.protocol("WM_DELETE_WINDOW", shutdown)

Tkinter.Label(text="Players:").place(x=0, y=0, height=20)
playersScroll = Tkinter.Scrollbar()
playersScroll.place(x=width-15, y=20, width=15, height=height/3)
playersListbox = Tkinter.Listbox(yscrollcommand=playersScroll.set)
playersListbox.place(x=0, y=20, width=width-15, height=height/3)
playersScroll.config(command=playersListbox.yview)

Tkinter.Label(text="Games:").place(x=0, y=25+height/3, height=20)
gamesScroll = Tkinter.Scrollbar()
gamesScroll.place(x=width-15, y=45+height/3, width=15, height=height/3)
gamesListbox = Tkinter.Listbox(yscrollcommand=gamesScroll.set)
gamesListbox.place(x=0, y=45+height/3, width=width-15, height=height/3)
gamesScroll.config(command=gamesListbox.yview)

shutdownButton = Tkinter.Button(text="Stop server", command=shutdown)
shutdownButton.place(x=width/4, y=50+2*height/3, width=width/2, height=25)

slotwidth = 36
pygame.init()

screen = pygame.display.set_mode((960, 540))
background = pygame.image.load("img/Turn.png")
signs = (pygame.image.load("img/Hit.png"), pygame.image.load("img/Miss.png"))

visualBoard = pygame.Surface((slotwidth*10, slotwidth*10))
for y in xrange(0, slotwidth*10, slotwidth):
    for x in xrange(0, slotwidth*10, slotwidth):
        pygame.draw.rect(visualBoard, (30, 60, 200), pygame.Rect(x, y, slotwidth, slotwidth))
        pygame.draw.rect(visualBoard, (255, 255, 255), pygame.Rect(x, y, slotwidth, slotwidth), 1)

players = []
addresses = []
names = []
playingNames = []
games = {}

online = True
while online:
    screen.blit(background, (0, 0))
    screen.blit(visualBoard, (45, 150))
    screen.blit(visualBoard, (555, 150))
    if len(gamesListbox.curselection()) > 0:
        gameID = gamesListbox.get(gamesListbox.curselection()[0])
        pygame.display.set_caption(gameID)
        names = gameID.split(" vs ")
        try:
            label(str((12 - len(names[0])) * " " + "{}'s board" + (12 - len(names[0])) * " ").format(names[0]), 20, (110, 110))
            label(str((12 - len(names[1])) * " " + "{}'s board" + (12 - len(names[1])) * " ").format(names[1]), 20, (650, 110))
            present_board(games[gameID]['ships'][0], games[gameID]['guesses'][1], (47, 152))
            present_board(games[gameID]['ships'][1], games[gameID]['guesses'][0], (557, 152))
            text = "{}'s Turn".format(games[gameID]['shooter'])
            label((40 - len(text)) / 2 * " " + text + (40 - len(text)) / 2 * " ", 48, (190, 50))
        except Exception as ex:
            print repr(ex)
            label("Players creating boards", 48, (220, 45))
    else:
        pygame.display.set_caption("Battleships")
        label("Choose a game in the", 32, (315, 45))
        label("games menu to watch it", 32, (300, 75))
    pygame.display.update()

    gui.update()
    rlist, wlist, xlist = select.select([server_socket] + players, [], [], 0)
    for sock in rlist:
        if sock == server_socket:
            newSock, addr = server_socket.accept()
            players.append(newSock)
            addresses.append(addr)
            insert_name(newSock.recv(1024), names, playingNames)
            playersListbox.insert(Tkinter.END, names[-1])
            print names[-1], "connected from", str(addr)
            if len(players) >= 2:
                thread.start_new_thread(game, (players[:3], addresses[:3], names[:3], playingNames, playersListbox, gamesListbox, games))
                players = players[3:]
                addresses = addresses[3:]
                playingNames += names[:3]
                names = names[3:]
        else:
            print names[players.index(sock)], str(addresses[players.index(sock)]), "disconnected"
            for i in xrange(playersListbox.size()):
                if playersListbox.get(i) == names[players.index(sock)]:
                    playersListbox.delete(i)
                    break
            addresses.pop(players.index(sock))
            names.pop(players.index(sock))
            players.remove(sock)
            sock.close()

server_socket.close()
pygame.quit()
gui.destroy()