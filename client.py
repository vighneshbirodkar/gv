import sys
import numpy as np
import socket
import random
import math
import random
import multiprocessing
from joblib import Parallel, delayed

BOARD_X = 1000
BOARD_Y = 1000
MIN_DIST_SQ = 66 ** 2
candidate_limit = multiprocessing.cpu_count()

pull_us = [[0] * 1000 for item in range(0, 1000)]
pull_them = [[0] * 1000 for item in range(0, 1000)]

def euclideanDistance(x1, y1, x2, y2):
    distance = (x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)
    return distance
    # return math.sqrt(distance)


def get_move():

    # Identify best move

    spacing_x = BOARD_X / 10
    spacing_y = BOARD_Y / 10
    
    current_x = spacing_x / 2
    current_y = spacing_y / 2

    candidates = []

    # Build candidate list
    while current_x <= BOARD_X:
        current_y = spacing_y / 2
        while current_y <= BOARD_Y:
            if is_move_valid(current_x, current_y, stones):
                candidates.append((current_x, current_y))
            current_y += spacing_y
        current_x += spacing_x

    # Evaluate candidates
    # If player 1: Minimize distance between our moves (defensive)
    # If player 2: Minimize distance between their moves (reactive)
    #              If last turn, evaluate all and pick best


    # Deep evaluation
    if US == 2 and moves_played == N:
        return get_last_move(candidates, stones)
    else:
        return get_cadidate(candidates, stones)
        

def get_cadidate(candidates, stones):

    if (US == 1) and (moves_played == 1):
        return (BOARD_X / 2, BOARD_Y / 2)

    
    # Heuristic: Minimize with us, maximimize with us; minimize with them, maximize with them.
    min_dist_us = 1e32
    max_dist_us = -1
    min_dist_them = 1e32
    max_dist_them = -1

    final_candidates = [ None ] * 4
    
    for candidate in candidates:
        
        # Compute distance to each move
        current_dist_us = 0
        current_dist_them = 0
        
        for move in stones:
            
            distance = euclideanDistance(candidate[0], candidate[1], move[0], move[1])
            
            if move[2] == US:
                current_dist_us += distance

            if move[2] == THEM:
                current_dist_them += distance

        # Update best candidates
        if current_dist_us < min_dist_us:
            final_candidates[0] = candidate
            min_dist_us = current_dist_us

        if current_dist_us > max_dist_us:
            final_candidates[1] = candidate
            max_dist_us = current_dist_us

        if current_dist_them < min_dist_them:
            final_candidates[2] = candidate
            min_dist_them = current_dist_them

        if current_dist_them > max_dist_them:
            final_candidates[3] = candidate
            max_dist_them = current_dist_them

    # Add two random candidates
    final_candidates.append(get_random_move())
    final_candidates.append(get_random_move())

    # Identify best option among final candidates
    # Parallelize
    best_difference = -(BOARD_X * BOARD_Y)
    idx = 1

    scores = parallel_get_best_candidate_wrapper(final_candidates)

    for i in range(len(final_candidates)):
        (u, t) = scores[i]

        if (u - t) > best_difference:
            best_difference = (u - t)
            best_candidate = final_candidates[i]
    
    print(best_candidate, 'has scores', best_difference)
    return best_candidate


def parallel_get_best_candidate_wrapper(candidates):

    num_cores = multiprocessing.cpu_count()

    print('Starting', num_cores, 'parallel threads')
    scores = Parallel(n_jobs = num_cores)(delayed(parallel_get_best_candidate)(c) for c in candidates)

    return scores


def parallel_get_best_candidate(candidate):
    return update_score(candidate[0], candidate[1], US, True)


def get_last_move(candidates, stones):
    bestScore = 0
    
    print('Final move, Have to evaluate', len(candidates))

    if len(candidates) > candidate_limit:
        print('Reducing to ', candidate_limit)
        candidates = random.sample(candidates, candidate_limit)

    closest = None
    closest_loss = 0

    # Evaluate
    scores = parallel_get_best_candidate_wrapper(candidates)

    for i in range(len(candidates)):
        (u, t) = scores[i]

        if u > t:
            return candidates[i]
            break
        else:
            if (closest_loss == 0) or (t - u < closest_loss):
                closest_loss = t - u
                closest = candidate

    # If control reached here, no win condition was found
    # Search further with the closest solution
    candidates = []
    for i in range(len(candidate_limit)):
        randomI = random.randint(closest[0] - spacing_x, closest[0] + spacing_x)
        randomJ = random.randint(closest[1] - spacing_y, closest[1] + spacing_y)

        if is_move_valid(randomI, randomJ, stones):
            candidates.append((randomI, randomJ))

    # Evaluate
    scores = parallel_get_best_candidate_wrapper(candidates)
    
    for i in range(len(candidates)):
        (u, t) = scores[i]

        if u > t:
            return candidates[i]
            break


    # No hopes
    return get_random_move()


def update_score(i, j, player, temp=False):

    score_us = 0
    score_them = 0

    for x in range(0, BOARD_X):
        for y in range(0, BOARD_Y):

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
        x, y = get_random_move()

    moves_played += 1

    update_score(x, y, US)

    print('Making move (%d, %d)' % (x, y))
    sock.sendall("%d %d" % (x, y))
