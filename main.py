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
    
for folder in ['player', 'enemies', 'bullets', 'walls', 'background', 'sounds']:
    if not os.path.exists(f'assets/{folder}'):
        os.makedirs(f'assets/{folder}')

def create_placeholder_image(path, size, color):
    if not os.path.exists(path):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, color, (0, 0, size[0], size[1]))
        pygame.image.save(surface, path)

def create_placeholder_sound(path):
    if not os.path.exists(path):
        sound = pygame.mixer.Sound(buffer=bytearray([128]*8000))
        pygame.mixer.Sound.save(sound, path)

create_placeholder_image('assets/player/player_ship.png', (64, 64), BLUE)
create_placeholder_image('assets/enemies/enemy_ship.png', (64, 64), RED)
create_placeholder_image('assets/bullets/player_bullet.png', (16, 16), GREEN)
create_placeholder_image('assets/bullets/enemy_bullet.png', (16, 16), (255, 100, 100))
create_placeholder_image('assets/walls/wall_tile.png', (100, 100), DARK_GRAY)
create_placeholder_image('assets/background/tiled_background.png', (WIDTH, HEIGHT), BLACK)
create_placeholder_sound('assets/sounds/shoot.wav')
create_placeholder_sound('assets/sounds/background_music.mp3')

PLAYER_IMAGE = load_image('assets/player/player_ship.png', max_size=(64, 64))
PLAYER_RADIUS = PLAYER_IMAGE.get_width() // 2

ENEMY_IMAGE = load_image('assets/enemies/enemy_ship.png', max_size=(64, 64))
ENEMY_RADIUS = ENEMY_IMAGE.get_width() // 2

BULLET_IMAGE = load_image('assets/bullets/player_bullet.png', target_size=(16, 16))
ENEMY_BULLET_IMAGE = load_image('assets/bullets/enemy_bullet.png', target_size=(16, 16))
WALL_IMAGE = load_image('assets/walls/wall_tile.png', max_size=(100, 100))
BACKGROUND_IMAGE = load_image('assets/background/tiled_background.png', target_size=(WIDTH, HEIGHT))
SHOOT_SOUND = load_sound('assets/sounds/shoot.wav')
BACKGROUND_MUSIC = 'assets/sounds/background_music.mp3'

class Wall:
    def __init__(self, x, y, width, height):
        self.image = pygame.transform.smoothscale(WALL_IMAGE, (width, height))
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self):
        screen.blit(self.image, self.rect)

class Bullet:
    def __init__(self, x, y, dx, dy, image):
        self.image = image
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = image.get_width() // 2
        self.rect = self.image.get_rect(center=(x, y))

    def get_rotated_image(self):
        angle = math.degrees(math.atan2(-self.dy, self.dx)) - 90
        return pygame.transform.rotozoom(self.image, angle, 1)

    def draw(self):
        rotated_image = self.get_rotated_image()
        screen.blit(rotated_image, self.rect)

    def update(self, walls):
        self.x += self.dx
        self.y += self.dy
        self.rect.center = (int(self.x), int(self.y))

        if (0 <= self.x < WIDTH and 0 <= self.y < HEIGHT and
            not any(self.rect.colliderect(wall.rect) for wall in walls)):
            return True
        return False

class EnemyBullet:
    def __init__(self, x, y, dx, dy):
        self.image = ENEMY_BULLET_IMAGE
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.radius = self.image.get_width() // 2
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = ENEMY_BULLET_DAMAGE

    def get_rotated_image(self):
        angle = math.degrees(math.atan2(-self.dy, self.dx)) - 90
        return pygame.transform.rotozoom(self.image, angle, 1)

    def draw(self):
        rotated_image = self.get_rotated_image()
        screen.blit(rotated_image, self.rect)

    def update(self, walls):
        self.x += self.dx
        self.y += self.dy
        self.rect.center = (int(self.x), int(self.y))

        if (0 <= self.x < WIDTH and 0 <= self.y < HEIGHT and
            not any(self.rect.colliderect(wall.rect) for wall in walls)):
            return True
        return False
    
    class Player:
    def __init__(self):
        self.image = PLAYER_IMAGE
        self.radius = PLAYER_RADIUS
        self.reset_position()
        self.lives = PLAYER_LIVES
        self.vida = PLAYER_HP
        self.vida_max = PLAYER_HP
        self.last_shot = 0
        self.direction = [0, -1]
        self.score = 0
        self.current_bullets = MAX_BULLETS
        self.is_taking_damage = False

    def reset_position(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def get_rotated_image(self):
        angle = math.degrees(math.atan2(-self.direction[1], self.direction[0])) - 90
        return pygame.transform.rotozoom(self.image, angle, 1)

    def draw(self):
        rotated_image = self.get_rotated_image()
        new_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, new_rect.topleft)

    def move(self, dx, dy, walls, enemies):

         if abs(dx) > 1 or abs(dy) > 1:
            mag = math.hypot(dx, dy)
            if mag > 0:
                dx = dx / mag
                dy = dy / mag
        
        if dx != 0 or dy != 0:
            self.direction = [dx, dy]
            dx = dx * PLAYER_SPEED
            dy = dy * PLAYER_SPEED
        else:
            return
