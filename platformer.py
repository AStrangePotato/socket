import pygame, sys
import time
import socket
import random
import pickle
import threading
from pygame.locals import *

pygame.init()
pygame.display.set_caption('moba deez nuts') # set the window name

WINDOW_SIZE = (800,450) # set up window size

screen = pygame.display.set_mode(WINDOW_SIZE,0,32) # initiate screen

display = pygame.Surface((400, 225))
clock = pygame.time.Clock()


#INITIATE SOCKETS#
HOST = "192.168.1.66"  # The server's hostname or IP address
if socket.gethostname() != "DESKTOP-STEVEN" and socket.gethostname() != "Daniel-ThinkX1":
    HOST = "108.180.180.157"
PORT = 12000  # The port used by the server


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
print("Connected")
time.sleep(0.1)

player = s.recv(1024).decode()
if player == "p1":
    playerNum = 1
if player == "p2":
    playerNum = 0



#VARIABLES
player_image = pygame.image.load('reaper.png').convert()
player_image.set_colorkey((0,0,0))

grass_image = pygame.image.load('grass.png')
TILE_SIZE = grass_image.get_width()

dirt_image = pygame.image.load('dirt.png')
dirt_l = pygame.image.load('dirt_l.png')
dirt_r = pygame.image.load('dirt_r.png')
grass_r = pygame.image.load("grass_r.png")
background = pygame.image.load("bg.png")

moving_right = False
moving_left = False

player_y_momentum = 0
air_timer = 0

vel = 2

debug = True

player_rect = pygame.Rect(50, 10, player_image.get_width() , player_image.get_height() + 2)
weapon_rect = pygame.Rect(0, 0, 18, 30)

player_health = 9

global opponent_state
s.send("get".encode())

opponent_state = pickle.loads(s.recv(1024))[playerNum]
prev_opponent_pos = opponent_state[1]
facing_right = True
lerp_opponent = [opponent_state[1], opponent_state[1]]

player_action = 'idle'
player_frame = 0

opponent_action = "idle"
opponent_frame = 0

global animation_frames
animation_frames = {}

def load_animation(path,frame_durations):
    global animation_frames
    animation_name = path.split('/')[-1]
    animation_frame_data = []
    n = 0
    for frame in frame_durations:
        animation_frame_id = animation_name + '_' + str(n)
        img_loc = path + '/' + animation_frame_id + '.png'
        # player_animations/idle/idle_0.png
        animation_image = pygame.image.load(img_loc).convert()
        animation_image.set_colorkey((0,0,0))
        animation_frames[animation_frame_id] = animation_image.copy()
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data

def change_action(action_var,frame,new_value):
    if action_var != new_value:
        action_var = new_value
        frame = 0
    return action_var,frame
        

animation_database = {}

animation_database['attack'] = load_animation('player_animations/attack',[8,7,7,7,7,7,7,7,7,15]) #length of each frame
animation_database['idle'] = load_animation('player_animations/idle',[7,7,7,7,38])


def loadMap(map_name):
    with open(map_name + ".txt", 'r') as f:
        data = f.read()
        data = data.split("\n")
        game_map = []
        for row in data:
            game_map.append(list(row))
    return game_map

game_map = loadMap("defaultMap")

def strToBool(v):
    if v == "True":
        return True
    if v == "False":
        return False


def collision_test(rect, tiles):
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list

def move(rect, movement, tiles):
    collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}
    rect.x += movement[0]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[0] > 0:
            rect.right = tile.left
            collision_types['right'] = True
        elif movement[0] < 0:
            rect.left = tile.right
            collision_types['left'] = True
    rect.y += movement[1]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[1] > 0:
            rect.bottom = tile.top
            collision_types['bottom'] = True
        elif movement[1] < 0:
            rect.top = tile.bottom
            collision_types['top'] = True
    return rect, collision_types

def lerp(start, end, splitNum):

    lerp_points = []
    if start == end:
        for i in range(0, splitNum):
            lerp_points.append(start)
        return lerp_points

    difference = (end-start) / (splitNum - 1)
    for i in range(splitNum):
        lerp_points.append(start + i*difference)
        
    return lerp_points


def multi():
    global opponent_state
    while True:

        s.send("get ".encode())

        data = pickle.loads(s.recv(1024))
        opponent_state = data[playerNum]


multiThread = threading.Thread(target=multi)
multiThread.daemon = True
multiThread.start()

lerpCounter = 0

trigger1 = False #if idle state
trigger2 = False #if attack state
#combine for new attack command
fresh_attack = False


while True: # game loop
    display.blit(background, (0, 0))

    tile_rects = []
    y = 0
    for row in game_map:
        x = 0
        for tile in row:
            if tile == '1':
                display.blit(dirt_image, (x * TILE_SIZE, y * TILE_SIZE))
            if tile == '2':
                display.blit(grass_image, (x * TILE_SIZE, y * TILE_SIZE))
            if tile == '3':
                display.blit(dirt_l, (x * TILE_SIZE, y * TILE_SIZE))
            if tile == '4':
                display.blit(dirt_r, (x * TILE_SIZE, y * TILE_SIZE))
            if tile == '5':
                display.blit(grass_r, (x * TILE_SIZE, y * TILE_SIZE))
            if tile != '0':
                tile_rects.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            x += 1
        y += 1

    player_movement = [0.0, 0.0]
    if moving_right:
        player_movement[0] += vel
    if moving_left:
        player_movement[0] -= vel


    #flip
    if player_movement[0] > 0:
        facing_right = True
    elif player_movement[0] < 0:
        facing_right = False

    player_movement[1] += player_y_momentum    
    player_y_momentum += 0.2 + air_timer*0.01 #gravity
    if player_y_momentum > 7:
        player_y_momentum = 7
        
    player_rect, collisions = move(player_rect, player_movement, tile_rects)

    if collisions['bottom']:
        player_y_momentum = 0
        air_timer = 0
    if collisions["top"]:
        player_y_momentum = 0
    else:
        air_timer += 1



    #linear interpolation for lag compensation
    oppFace = strToBool(opponent_state[2]) #[hp, (coordinates), facingRight, attackState]
    opponentX, opponentY = float(opponent_state[1][0]), float(opponent_state[1][1])
    lerp_opponent[0] = lerp_opponent[1]
    lerp_opponent[1] = [opponentX, opponentY]

    if lerp_opponent[1] != lerp_opponent[0]: #when there is a server update and the positiosn change
        lerpX_points = lerp(lerp_opponent[0][0], lerp_opponent[1][0], 5)
        lerpY_points = lerp(lerp_opponent[0][1], lerp_opponent[1][1], 5)
        lerpCounter = 0


    player_frame += 1
    opponent_frame += 1

    opponent_action = opponent_state[3]

    if opponent_action == "idle":
        trigger1 = True
    if trigger1 and opponent_action == "attack":
        trigger2 = True
    if player_frame >= len(animation_database["attack"]):
        player_frame = 0
        player_action = "idle"
    if player_frame >= len(animation_database[player_action]):
        player_frame = 0


    if opponent_frame >= len(animation_database["attack"]):
        opponent_frame = 0
        opponent_action = "idle"

    if opponent_frame >= len(animation_database[opponent_action]):
        opponent_frame = 0

    if trigger1 and trigger2:
        opponent_frame = 0
        trigger1, trigger2 = False, False


    #damage
    if fresh_attack and player_frame >= 30:
        fresh_attack = False
        print("hit here")

    player_img_id = animation_database[player_action][player_frame] 
    player_image = animation_frames[player_img_id]


    opponent_img_id = animation_database[opponent_action][opponent_frame]
    opponent_image = animation_frames[opponent_img_id]



    if facing_right == False:
        shift = 0
        if player_action == "attack":
            display.blit(pygame.transform.flip(player_image, not facing_right, False), (player_rect.x - 9, player_rect.y))
        else:
            display.blit(pygame.transform.flip(player_image, not facing_right, False), (player_rect.x - 5, player_rect.y))
        weapon_rect.x = player_rect.x - 10
        weapon_rect.y = player_rect.y + 4


    elif facing_right == True:
        display.blit(pygame.transform.flip(player_image, not facing_right, False), (player_rect.x - 8, player_rect.y))
        weapon_rect.x = player_rect.x + 20
        weapon_rect.y = player_rect.y + 4



    if oppFace == False:
        try:
            if opponent_action == "attack":
                display.blit(pygame.transform.flip(opponent_image, not oppFace, False), (lerpX_points[lerpCounter] - 9, lerpY_points[lerpCounter]))
            else:
                display.blit(pygame.transform.flip(opponent_image, not oppFace, False), (lerpX_points[lerpCounter] - 5, lerpY_points[lerpCounter]))
            
        except Exception as e:
            print(e)


    elif oppFace == True:
        try:
            display.blit(pygame.transform.flip(opponent_image, not oppFace, False), (lerpX_points[lerpCounter] - 8, lerpY_points[lerpCounter]))

        except Exception as e:
            print(e)

        
    #HITBOX display
    try:
        display.blit(pygame.image.load("health/health_" + str(9-player_health) + ".png"), (player_rect.x - 1, player_rect.y - 10))
    except:
        display.blit(pygame.image.load("health/health_0.png"), (player_rect.x - 1, player_rect.y - 10))
    
    if debug:
        pygame.draw.rect(display, (0, 255, 0), player_rect, 1)
        pygame.draw.rect(display, (255, 0, 0), weapon_rect, 1)
        
    if lerpCounter < 4:
        lerpCounter += 1


    #socket stuff
    s.send(f"move {player_rect.x} {player_rect.y} {facing_right} ".encode())
    s.send(f"updateState {player_action} ".encode())

    for event in pygame.event.get(): # event loop
        if event.type == QUIT: # check for window quit
            pygame.quit() # stop pygame
            sys.exit() # stop script
        if event.type == KEYDOWN:
            if event.key == K_d:
                moving_right = True
            if event.key == K_a:
                moving_left = True
            if event.key == K_SPACE:
                if air_timer <= 6:
                    player_y_momentum = -4.8
            if event.key == K_p:
                if player_action != "attack":
                    player_action = "attack"
                    fresh_attack = True
                    player_frame = 0
            if event.key == K_b:
                player_health -= 1
        if event.type == KEYUP:
            if event.key == K_d:
                moving_right = False
            if event.key == K_a:
                moving_left = False

    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    pygame.display.update() # update display
    clock.tick(60) # maintain 60 fps