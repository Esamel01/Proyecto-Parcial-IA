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

BLACK = (20, 20, 30)
WHITE = (240, 240, 240)
RED = (220, 60, 60)
GREEN = (50, 220, 100)
BLUE = (80, 160, 255)
DARK_GRAY = (60, 60, 70)
YELLOW = (255, 220, 100)

def load_image(filepath, target_size=None, max_size=None):
    try:
        image = pygame.image.load(filepath).convert_alpha()
        if max_size:
            width, height = image.get_size()
            scale = min(max_size[0]/width, max_size[1]/height)
            if scale < 1:
                image = pygame.transform.smoothscale(image, (int(width * scale), int(height * scale)))
        if target_size:
            image = pygame.transform.smoothscale(image, target_size)
        return image
    except pygame.error as e:
        print(f"Error loading image {filepath}: {e}")
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.rect(surface, (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)), (0, 0, 32, 32))
        return surface

def load_sound(filepath):
    try:
        return pygame.mixer.Sound(filepath)
    except pygame.error as e:
        print(f"Error loading sound {filepath}: {e}")
        return None