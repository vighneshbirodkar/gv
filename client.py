import sys
import numpy as np
import socket
import random
import math
import random
import multiprocessing
from joblib import Parallel, delayed

def euclideanDistance(x1, y1, x2, y2):
    distance = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
    return distance


def get_move():

    if (US == 2) and (moves_played == N):
        spacing_x = BOARD_X / (SPACING_FACTOR * 5)
        spacing_y = BOARD_Y / (SPACING_FACTOR * 5)
    else:
        spacing_x = BOARD_X / SPACING_FACTOR
        spacing_y = BOARD_Y / SPACING_FACTOR
    
    current_x = spacing_x / 2
    current_y = spacing_y / 2

    candidates = []

    # Build candidate list
    while current_x <= BOARD_X:
        current_y = spacing_y / 2
        while current_y <= BOARD_Y:
            if is_move_valid(current_x, current_y, stones):
                candidates.append((current_x, current_y))
                # print current_x, current_y
            current_y += spacing_y
        current_x += spacing_x

    # Evaluate candidates
    return get_candidate(candidates, stones)


def get_candidate(candidates, stones):

    if (US == 1) and (moves_played == 1):
        return (BOARD_X / 2, BOARD_Y / 2)

    # Identify best option among final candidates
    # Parallelize
    best_difference = -(BOARD_X * BOARD_Y)

    print('Evaluating', len(candidates), 'candidates')

    scores = parallel_get_best_candidate_wrapper(candidates)

    for i in range(len(candidates)):
        (u, t) = scores[i]
        difference = u - t

        if difference > best_difference:
            best_difference = difference
            best_candidate = candidates[i]

    print(best_candidate, 'Difference', best_difference)

    # If this is the last move, make a deeper search around the best candidate to win
    if (US == 2) and (moves_played == N) and (best_difference < 0):
        target_candidates = len(candidates) / 2
        candidates = []
        box_size_x = BOARD_X / 10
        box_size_y = BOARD_Y / 10
        for i in range(len(target_candidates)):
            randomI = random.randint(closest[0] - box_size_x, closest[0] + box_size_x)
            randomJ = random.randint(closest[1] - box_size_y, closest[1] + box_size_y)

            if is_move_valid(randomI, randomJ, stones):
                candidates.append((randomI, randomJ))

        # Re-evaluate among these candidates
        scores = parallel_get_best_candidate_wrapper(candidates)
        for i in range(len(candidates)):
            (u, t) = scores[i]
            difference = u - t
            if difference > 0:
                print('Winning local random found', candidates[i], 'Difference', best_difference)
                return candidates[i]

        # Return something
        return get_random_move(candidates)

    # Normal flow, return best candidate
    return best_candidate


def parallel_get_best_candidate_wrapper(candidates):

    num_cores = multiprocessing.cpu_count()
    scores = Parallel(n_jobs = num_cores)(delayed(parallel_get_best_candidate)(c) for c in candidates)

    return scores


def parallel_get_best_candidate(candidate):
    return update_score(candidate[0], candidate[1], US, True)


def update_score(i, j, player, temp=False):

    score_us = 0
    score_them = 0

    step = 10

    for x in range(0, BOARD_X, 10):
        for y in range(0, BOARD_Y, 10):

            if x == i and y == j:
                continue

            Di = euclideanDistance(x, y, i, j)
            pull = float(float(1) / float(Di * Di))

            pull_us_temp = pull_us[x][y]
            pull_them_temp = pull_them[x][y]

            if player == US:
                pull_us_temp += pull
                pull_them_temp -= pull
            else:
                pull_us_temp -= pull
                pull_them_temp += pull

            if temp == False:
                pull_us[x][y] = pull_us_temp
                pull_them[x][y] = pull_them_temp

            if pull_us_temp > pull_them_temp:
                score_us += 1
            else:
                score_them += 1

    return (score_us, score_them)


def is_move_unique(i, j, stones):

    for move in stones:
        if move[0] == i and move[1] == j:
            return False

    return True


def is_move_valid(i, j, stones):

    if (i < 0) or (j < 0) or (i >= BOARD_X) or (j >= BOARD_Y):
        return False

    if is_move_unique(i, j, stones) == False:
        return False

    for move in stones:
        if euclideanDistance(i, j, move[0], move[1]) < MIN_DIST_SQ:
            return False
    return True


def get_random_move():
    validMoveFound = False
    nextI = 0
    nextJ = 0

    while not validMoveFound:
        randomI = random.randint(0, 999)
        randomJ = random.randint(0, 999)

        validMoveFound = is_move_valid(randomI, randomJ, stones)

        if validMoveFound:
            nextI = randomI
            nextJ = randomJ

    return nextI, nextJ


US = 1
THEM = 2

HOST = 'localhost'
PORT = 9000


N = int(sys.argv[1])
stones = np.zeros((3 * N, 3), dtype=np.int)
stones[...] = -1
moves_played = 1
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

game_running = True
first_data = True
grid = [[0] * 1000 for item in range(0, 1000)]

BOARD_X = 1000
BOARD_Y = 1000
MIN_DIST = 66
MIN_DIST_SQ = MIN_DIST ** 2
SPACING_FACTOR = 15

pull_us = [[0] * 1000 for item in range(0, 1000)]
pull_them = [[0] * 1000 for item in range(0, 1000)]

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

        # Update pull
        if item == num_moves - 1:
            print('They moved', i, j)
            update_score(i, j, THEM)

    try:
        x, y = get_move()
    except:
        print('Normal evaluation failed, falling back to random')
        x, y = get_random_move()

    moves_played += 1

    update_score(x, y, US)

    print('Making move (%d, %d)' % (x, y))
    print('------------------------------------------------------')
    sock.sendall("%d %d" % (x, y))
