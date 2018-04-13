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


class Player(object):
    def __init__(self, socket, address, name):
        self.socket = socket
        self.address = address
        self.name = name

    def __repr__(self):
        return self.name + " " + str(self.address)


class ServerGUI(Tkinter.Tk):
    width = 200
    height = 300

    def __init__(self):
        Tkinter.Tk.__init__(self)
        self.title("Battleships server")
        self.geometry(str(self.width) + "x" + str(self.height))
        self.resizable(0, 0)
        self.protocol("WM_DELETE_WINDOW", shutdown)

        Tkinter.Label(text="Players:").place(x=0, y=0, height=20)
        self.playersScroll = Tkinter.Scrollbar()
        self.playersScroll.place(x=self.width-15, y=20, width=15, height=self.height/3)
        self.playersListbox = Tkinter.Listbox(yscrollcommand=self.playersScroll.set)
        self.playersListbox.place(x=0, y=20, width=self.width-15, height=self.height/3)
        self.playersScroll.config(command=self.playersListbox.yview)

        Tkinter.Label(text="Games:").place(x=0, y=25+self.height/3, height=20)
        self.gamesScroll = Tkinter.Scrollbar()
        self.gamesScroll.place(x=self.width-15, y=45+self.height/3, width=15, height=self.height/3)
        self.gamesListbox = Tkinter.Listbox(yscrollcommand=self.gamesScroll.set)
        self.gamesListbox.place(x=0, y=45+self.height/3, width=self.width-15, height=self.height/3)
        self.gamesScroll.config(command=self.gamesListbox.yview)

        self.shutdownButton = Tkinter.Button(text="Stop server", command=shutdown)
        self.shutdownButton.place(x=self.width/4, y=50+2*self.height/3, width=self.width/2, height=25)

    @property
    def curr_game(self):
        if len(self.gamesListbox.curselection()) > 0:
            return self.gamesListbox.get(self.gamesListbox.curselection()[0])
        return False


class Room(object):
    def __init__(self, name, player, hidden, password):
        self.name = name
        self.password = password
        self.players = [player]
        self.hidden = hidden
        self.ready = 0

    def update(self):
        sockets = []
        for pl in self.players:
            sockets.append(pl.socket)
        rlist, wlist, xlist = select.select(sockets, [], [], 0)
        for sock in rlist:
            for pl in self.players:
                if pl.socket == sock:
                    player = pl
            try:
                data = sock.recv(1024)
                if data == "":
                    print player, "disconnected"
                    self.players.remove(player)
                    if len(self) == 0:
                        rooms.remove(self)
                    for i in xrange(gui.playersListbox.size()):
                        if gui.playersListbox.get(i) == player.name:
                            gui.playersListbox.delete(i)
                            break
                    names.remove(player.name)
                    sock.close()
                    map(lambda sock: sock.sendall("new;"), players.keys())
                else:
                    data = data.split(";")
                    if data[0] == "ready":
                        self.ready += 1
                        if self.ready == 2:
                            thread.start_new_thread(game, (self.players, gui.playersListbox, gui.gamesListbox, games))
                            rooms.remove(self)
                    if data[0] == "getRoom":
                        data = ""
                        for player in self.players:
                            data += player.name + "\n"
                        sock.sendall(data[:-1])
                    if data[0] == "leave":
                        self.ready = 0
                        sock.sendall("ack")
                        players[sock] = player
                        self.players.remove(player)
                        if len(self) == 0:
                            rooms.remove(self)
                        else:
                            data = ""
                            for player in self.players:
                                data += player.name + "\n"
                            self.players[0].socket.send(data[:-1])
                        map(lambda sock: sock.sendall("new;"), players.keys())
            except Exception as ex:
                print repr(ex)
                self.ready = 0
                print player, "disconnected"
                self.players.remove(player)
                if len(self) == 0:
                    rooms.remove(self)
                for i in xrange(gui.playersListbox.size()):
                    if gui.playersListbox.get(i) == player.name:
                        gui.playersListbox.delete(i)
                        break
                names.remove(player.name)
                sock.close()
                map(lambda sock: sock.sendall("new;"), players.keys())


    def __len__(self):
        return len(self.players)

    def __getitem__(self, item):
        return self.players[item]

    def __repr__(self):
        if len(self.players) == 2:
            return self.name+";"+self.players[0].name+","+self.players[1].name+";"+str(self.password != "")
        return self.name+";"+self.players[0].name+";"+str(self.password != "")


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

    wait = True
    while wait:
        rlist, wlist, xlist = select.select([shooter, watcher], [], [], 0)
        for sock in rlist:
            data = sock.recv(1024)
            if data == "":
                raise Exception
            else:
                wait = False

    coords = pickle.loads(data)

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


def game(players, playersListbox, gamesListBox, games):
    try:
        gameID = players[0].name + " vs " + players[1].name
        gamesListBox.insert(Tkinter.END, gameID)
        games[gameID] = {}
        game = games[gameID]

        map(lambda sock: sock.sendall("new;"), globals()['players'].keys())

        game['guesses'] = [[], []]
        for x in xrange(10):
            game['guesses'][0].append([])
            game['guesses'][1].append([])
            for y in xrange(10):
                game['guesses'][0][-1].append("")
                game['guesses'][1][-1].append("")
        try:
            players[0].socket.sendall("start")
            players[1].socket.sendall("start")

            game['ships'] = [None, None]
            while game['ships'][0] == None or game['ships'][1] == None:
                rlist, wlist, xlist = select.select([players[0].socket, players[1].socket], [], [], 0)
                for sock in rlist:
                    data = sock.recv(1024)
                    if data == "":
                        raise Exception
                    if sock == players[0].socket:
                        game['ships'][0] = pickle.loads(data)
                    else:
                        game['ships'][1] = pickle.loads(data)

            players[0].socket.sendall("start")
            players[1].socket.sendall("start")

            boards = [pickle.loads(players[0].socket.recv(1024)), pickle.loads(players[1].socket.recv(1024))]

            players[0].socket.sendall(players[1].name)
            players[1].socket.sendall(players[0].name)

            if players[0].socket.recv(1024) == "got name" and players[1].socket.recv(1024) == "got name":
                pass

            finish = False

            shooter = randint(0, 1)
            while not finish:
                game['shooter'] = players[shooter].name
                finish = turn(players[shooter].socket, players[1-shooter].socket, game['guesses'][shooter], boards[1-shooter], game['ships'][1-shooter])
                shooter = 1 - shooter
            players[0].socket.sendall(pickle.dumps(game['ships'][1]))
            players[1].socket.sendall(pickle.dumps(game['ships'][0]))

            globals()["players"][players[0].socket] = players[0]
            globals()["players"][players[1].socket] = players[1]
        except:
            global names
            try:
                players[0].socket.send("disconnect;")
                players[0].socket.recv(1024)
                globals()['players'][players[0].socket] = players[0]
            except:
                for i in xrange(playersListbox.size()):
                    if playersListbox.get(i) == players[0].name:
                        playersListbox.delete(i)
                print players[0], "disconnected"
                names.remove(players[0].name)
            try:
                players[1].socket.sendall("disconnect;")
                players[1].socket.recv(1024)
                globals()['players'][players[1].socket] = players[1]
            except:
                for i in xrange(playersListbox.size()):
                    if playersListbox.get(i) == players[1].name:
                        playersListbox.delete(i)
                print players[1], "disconnected"
                names.remove(players[1].name)
        finally:
            for i in xrange(gamesListBox.size()):
                if gamesListBox.get(i) == gameID:
                    gamesListBox.delete(i)
            games.pop(gameID)
            map(lambda sock: sock.sendall("new;"), globals()['players'].keys())
    except:
        pass


def insert_name(name, names):
    if name not in names:
        names.append(name)
    else:
        i = 0
        while name + str(i) in names:
            i += 1
        names.append(name + str(i))


def shutdown():
    global online
    online = False


def label(text, size, pos, color=(255, 255, 255)):
    myFont = pygame.font.SysFont("Calibri", size)
    myText = myFont.render(text, 1, color)
    screen.blit(myText, pos)


def identify():
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    udp_server.bind(("0.0.0.0", 12346))
    udp_server.setblocking(False)
    while online:
        try:
            data = udp_server.recvfrom(1024)
            if data[0] == "battleships?":
                udp_server.sendto("indeed", data[1])
        except:
            pass
    udp_server.close()


def chat():
    chat_server = socket.socket()
    chat_server.bind(('0.0.0.0', 12347))
    chat_server.listen(5)
    open_client_sockets = []
    names = {}
    while online:
        try:
            rlist, wlist, xlist = select.select([chat_server] + open_client_sockets, [], [], 0)
            for current_socket in rlist:
                if current_socket is chat_server:
                    newSock, addr = chat_server.accept()
                    open_client_sockets.append(newSock)
                    names[newSock] = newSock.recv(1024)
                else:
                    data = current_socket.recv(1024).decode("utf-8")
                    if data == "":
                        names.pop(current_socket)
                        open_client_sockets.remove(current_socket)
                    else:
                        for client in open_client_sockets:
                            client.send((names[current_socket] + ": " + data + "\n").encode("utf-8"))
        except:
            names.pop(current_socket)
            open_client_sockets.remove(current_socket)
    chat_server.close()


def lobby_data(rooms, games):
    ret = ""
    if len(rooms) == 0:
        ret = "empty@"
    else:
        for room in rooms:
            if not room.hidden:
                ret += repr(room) + "\n"
        ret = ret[:-1] + "@"
    if len(games) == 0:
        return ret+"empty"
    for game in games.keys():
        ret += game + "\n"
    ret = ret[:-1]
    return ret


def maintain_gui(gui):
    if gui.curr_game:
        global screen
        pygame.init()
        screen = pygame.display.set_mode((960, 540))

        screen.blit(background, (0, 0))
        screen.blit(visualBoard, (45, 150))
        screen.blit(visualBoard, (555, 150))
        try:
            pygame.display.set_caption(gui.curr_game)
            names = gui.curr_game.split(" vs ")
            try:
                label(str((12 - len(names[0])) * " " + "{}'s board" + (12 - len(names[0])) * " ").format(names[0]), 20,
                      (110, 110))
                label(str((12 - len(names[1])) * " " + "{}'s board" + (12 - len(names[1])) * " ").format(names[1]), 20,
                      (650, 110))
                present_board(games[gui.curr_game]['ships'][0], games[gui.curr_game]['guesses'][1], (47, 152))
                present_board(games[gui.curr_game]['ships'][1], games[gui.curr_game]['guesses'][0], (557, 152))
                text = "{}'s Turn".format(games[gui.curr_game]['shooter'])
                label((40 - len(text)) / 2 * " " + text + (40 - len(text)) / 2 * " ", 48, (190, 50))
            except:
                try:
                    present_board(games[gui.curr_game]['ships'][1], games[gui.curr_game]['guesses'][0], (557, 152))
                except:
                    pass
                label("Players placing ships", 48, (220, 45))
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    gui.gamesListbox.selection_clear(0, Tkinter.END)
            pygame.display.update()
        except:
            pygame.quit()
    else:
        pygame.quit()
    gui.update()


server_socket = socket.socket()
server_socket.bind(('0.0.0.0', 12345))
server_socket.listen(5)

gui = ServerGUI()

slotwidth = 36
background = pygame.image.load("media/Turn.png")
signs = (pygame.image.load("media/Hit.png"), pygame.image.load("media/Miss.png"))

visualBoard = pygame.Surface((slotwidth*10, slotwidth*10))
for y in xrange(0, slotwidth*10, slotwidth):
    for x in xrange(0, slotwidth*10, slotwidth):
        pygame.draw.rect(visualBoard, (30, 60, 200), pygame.Rect(x, y, slotwidth, slotwidth))
        pygame.draw.rect(visualBoard, (255, 255, 255), pygame.Rect(x, y, slotwidth, slotwidth), 1)

players = {}
names = []
rooms = []
games = {}

online = True
thread.start_new_thread(identify, tuple())
thread.start_new_thread(chat, tuple())
while online:
    maintain_gui(gui)
    rlist, wlist, xlist = select.select([server_socket] + players.keys(), [], [], 0)
    for sock in rlist:
        if sock == server_socket:
            newSock, addr = server_socket.accept()
            insert_name(newSock.recv(1024), names)
            newSock.send(names[-1])
            gui.playersListbox.insert(Tkinter.END, names[-1])
            players[newSock] = Player(newSock, addr, names[-1])
            print names[-1], "connected from", str(addr)
        else:
            try:
                data = sock.recv(1024)
                if data == "":
                    print players[sock], "disconnected"
                    for i in xrange(gui.playersListbox.size()):
                        if gui.playersListbox.get(i) == players[sock].name:
                            gui.playersListbox.delete(i)
                            break
                    names.remove(players[sock].name)
                    players.pop(sock)
                    sock.close()
                    map(lambda sock: sock.sendall("new;"), players.keys())
                else:
                    data = data.split(";")
                    if data[0] == "get":
                        sock.sendall(lobby_data(rooms, games))
                    elif data[0] == "new":
                        sock.sendall("ack")
                        rooms.append(Room(data[1], players[sock], False, data[2]))
                        players.pop(sock)
                        map(lambda sock: sock.sendall("new;"), players.keys())
                    elif data[0] == "join":
                        if rooms[int(data[1])].password == "":
                            sock.sendall("ack")
                            rooms[int(data[1])].players.append(players[sock])
                            players.pop(sock)
                            rooms[int(data[1])].players[0].socket.sendall(rooms[int(data[1])].players[0].name + "\n" + rooms[int(data[1])].players[1].name)
                            map(lambda sock: sock.sendall("new;"), players.keys())
                        elif data[2] == rooms[int(data[1])].password:
                            sock.sendall("True")
                            rooms[int(data[1])].players.append(players[sock])
                            players.pop(sock)
                            rooms[int(data[1])].players[0].socket.sendall(rooms[int(data[1])].players[0].name + "\n" + rooms[int(data[1])].players[1].name)
                            map(lambda sock: sock.sendall("new;"), players.keys())
                        else:
                            sock.sendall("False")
            except:
                print players[sock], "disconnected"
                for i in xrange(gui.playersListbox.size()):
                    if gui.playersListbox.get(i) == players[sock].name:
                        gui.playersListbox.delete(i)
                        break
                names.remove(players[sock].name)
                players.pop(sock)
                sock.close()
                map(lambda sock: sock.sendall("new;"), players.keys())
    map(Room.update, rooms)

server_socket.close()
pygame.quit()
gui.destroy()
