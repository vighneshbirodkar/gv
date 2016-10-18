import sys
import numpy as np
import socket
import random
import math


def euclideanDistance(x1, y1, x2, y2):
    distance = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
    return math.sqrt(distance)


def get_move(stone_array, stones_present):
    validMoveFound = False
    nextI = 0
    nextJ = 0

    while not validMoveFound:
        randomI = random.randint(0, 999)
        randomJ = random.randint(0, 999)

        validMoveFound = True
        for move in stone_array:
            if euclideanDistance(randomI, randomJ, move[0], move[1]) < 66:
                validMoveFound = False

        if validMoveFound:
            nextI = randomI
            nextJ = randomJ

    return nextI, nextJ


US = 1
THEM = 2

HOST = 'localhost'
PORT = 9000


N = int(sys.argv[1])
stones = np.zeros((3*N, 3), dtype=np.int)
stones[...] = -1
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

game_running = True
first_data = True
grid = [[0] * 1000 for item in range(0, 1000)]


while game_running:
    recv_data = sock.recv(1024)
    recv_data = recv_data.split()

    if first_data:
        if len(recv_data) == 2:
            US = 1
            THEM = 2
        else:
            US = 2
            THEM = 1
        first_data = False
        print('We are player %d' % US)

    # Check if the game has ended
    if int(recv_data[0]) == 1:
        game_running = False
        break

    # Construct the grid by placing all the moves so far
    num_moves = int(recv_data[1])

    stones[...] = -1
    for item in xrange(0, num_moves):
        i = int(recv_data[2 + item * 3])
        j = int(recv_data[2 + item * 3 + 1])
        player = int(recv_data[2 + item * 3 + 2])

        if player > 0:
            grid[i][j] = player
            stones[item] = [i, j, player]

    x, y = get_move(stones, num_moves)

    print('Making move (%d, %d)' % (x, y))
    sock.sendall("%d %d" % (x, y))
