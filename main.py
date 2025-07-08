import pygame
import random
import math
import sys
import os
import heapq
from pygame.locals import *

pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Roguelike - Directional Shooting")
clock = pygame.time.Clock()
FPS = 60

PLAYER_SPEED = 4
BULLET_SPEED = 8
ENEMY_BULLET_SPEED = 5
PLAYER_LIVES = 3
PLAYER_HP = 100
MAX_BULLETS = 100
SHOOT_DELAY = 150
ENEMY_SHOOT_DELAY = 1000
DAMAGE_PER_SECOND = 10
ENEMY_BULLET_DAMAGE = 10
GRID_CELL_SIZE = 30

JOYSTICK_DEADZONE = 0.5
JOYSTICK_SHOOT_BUTTON = 0  # Button A
JOYSTICK_MENU_BUTTON = 7   # Button Start
JOYSTICK_RESTART_BUTTON = 6 # Button Select
JOYSTICK_NEXT_LEVEL_BUTTON = 3 # Button Y
