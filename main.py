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

        original_x = self.rect.x
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dx > 0:
                    self.rect.right = wall.rect.left
                elif dx < 0:
                    self.rect.left = wall.rect.right
                break
        
        original_y = self.rect.y
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if dy > 0:
                    self.rect.bottom = wall.rect.top
                elif dy < 0:
                    self.rect.top = wall.rect.bottom
                break

                    self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(HEIGHT, self.rect.bottom)

    def can_shoot(self):
        return pygame.time.get_ticks() - self.last_shot >= SHOOT_DELAY and self.current_bullets > 0

    def shoot(self):
        if self.can_shoot():
            self.last_shot = pygame.time.get_ticks()
            self.current_bullets -= 1
            norm = math.hypot(*self.direction)
            if norm > 0:
                dx = self.direction[0] / norm * BULLET_SPEED
                dy = self.direction[1] / norm * BULLET_SPEED
            else:
                dx, dy = 0, -BULLET_SPEED
            
            if SHOOT_SOUND:
                SHOOT_SOUND.play()
                
            return Bullet(self.rect.centerx, self.rect.centery, dx, dy, BULLET_IMAGE)
        return None

    def update(self, dt):
        if self.is_taking_damage:
            self.vida -= DAMAGE_PER_SECOND * (dt / 1000)
            if self.vida <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.vida = self.vida_max
                    self.reset_position()
                else:
                    self.vida = 0

    def take_damage(self, amount):
        self.vida -= amount
        if self.vida <= 0:
            self.lives -= 1
            if self.lives > 0:
                self.vida = self.vida_max
                self.reset_position()
            else:
                self.vida = 0

    def set_taking_damage(self, status):
        self.is_taking_damage = status

class Enemy:
    def __init__(self, x, y, level):
        self.x = x
        self.y = y
        self.level = level
        self.vida = 25 + level * 5
        self.speed = 1.3 + level * 0.1
        self.image = ENEMY_IMAGE
        self.radius = ENEMY_RADIUS
        self.rect = self.image.get_rect(center=(x, y))
        self.last_shot = pygame.time.get_ticks()
        self.last_path_update = 0
        self.current_path = []
        self.behavior_tree = self.create_behavior_tree()

    def create_behavior_tree(self):
        return BehaviorTree.Selector([
            BehaviorTree.Sequence([
                BehaviorTree.CanShootPlayer(),
                BehaviorTree.ShootAction()
            ]),
            BehaviorTree.Sequence([
                BehaviorTree.PathfindToPlayer(),
                BehaviorTree.FollowPath()
            ])
        ])

    def get_rotated_image(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        angle = math.degrees(math.atan2(-dy, dx)) - 90
        return pygame.transform.rotozoom(self.image, angle, 1)

    def draw(self, player):
        rotated_image = self.get_rotated_image(player)
        new_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, new_rect.topleft)

                life_ratio = self.vida / (25 + self.level * 5)
        bar_width = 30
        pygame.draw.rect(screen, (30, 30, 30), (new_rect.centerx - bar_width//2, new_rect.top - 10, bar_width, 5))
        pygame.draw.rect(screen, (0, 180, 0), (new_rect.centerx - bar_width//2, new_rect.top - 10, int(bar_width * life_ratio), 5))

    def update(self, player, walls, enemies_list, dt, game):
        generated_bullet = None
        self.behavior_tree.run(self, game)
        
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(HEIGHT, self.rect.bottom)
        
        return self.rect.colliderect(player.rect), generated_bullet
    
    class AStarNode:
    def __init__(self, position, parent=None):
        self.position = position
        self.parent = parent
        self.g = 0
        self.h = 0
        self.f = 0
    
    def __eq__(self, other):
        return self.position == other.position
    
    def __lt__(self, other):
        return self.f < other.f

class AStarPathfinding:
    @staticmethod
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    @staticmethod
    def find_path(start, end, walls):
        grid_width = WIDTH // GRID_CELL_SIZE
        grid_height = HEIGHT // GRID_CELL_SIZE
        
        open_set = []
        closed_set = set()
        
        start_node = AStarNode(start)
        end_node = AStarNode(end)
        
        heapq.heappush(open_set, (start_node.f, start_node))
        
        while open_set:
            current_node = heapq.heappop(open_set)[1]
            closed_set.add(current_node.position)
            
            if current_node == end_node:
                path = []
                while current_node:
                    path.append(current_node.position)
                    current_node = current_node.parent
                return path[::-1]
            
            for dx, dy in [(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]:
                neighbor_pos = (current_node.position[0]+dx, current_node.position[1]+dy)
                
                if 0 <= neighbor_pos[0] < grid_width and 0 <= neighbor_pos[1] < grid_height:
                    cell_rect = pygame.Rect(
                        neighbor_pos[0]*GRID_CELL_SIZE, 
                        neighbor_pos[1]*GRID_CELL_SIZE, 
                        GRID_CELL_SIZE, 
                        GRID_CELL_SIZE
                    )
                    
                    walkable = True
                    for wall in walls:
                        if cell_rect.colliderect(wall.rect):
                            walkable = False
                            break
                    
                    if walkable:
                        neighbor = AStarNode(neighbor_pos, current_node)
                        if neighbor.position in closed_set:
                            continue
                            
                        neighbor.g = current_node.g + 1
                        neighbor.h = AStarPathfinding.heuristic(neighbor.position, end_node.position)
                        neighbor.f = neighbor.g + neighbor.h
                        
                        if not any(node[1] == neighbor and node[0] <= neighbor.f for node in open_set):
                            heapq.heappush(open_set, (neighbor.f, neighbor))
        
        return None

class BehaviorTree:
    class Node:
        def run(self, enemy, game):
            return False
    
    class Selector(Node):
        def __init__(self, children):
            self.children = children
        
        def run(self, enemy, game):
            for child in self.children:
                if child.run(enemy, game):
                    return True
            return False
    
    class Sequence(Node):
        def __init__(self, children):
            self.children = children
        
        def run(self, enemy, game):
            for child in self.children:
                if not child.run(enemy, game):
                    return False
            return True
    
    class CanShootPlayer(Node):
        def run(self, enemy, game):
            dx = game.player.rect.centerx - enemy.rect.centerx
            dy = game.player.rect.centery - enemy.rect.centery
            dist = math.hypot(dx, dy)
            return dist < 300 and pygame.time.get_ticks() - enemy.last_shot >= ENEMY_SHOOT_DELAY
    
    class ShootAction(Node):
        def run(self, enemy, game):
            dx = game.player.rect.centerx - enemy.rect.centerx
            dy = game.player.rect.centery - enemy.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist > 0:
                bullet_dx = dx/dist * ENEMY_BULLET_SPEED
                bullet_dy = dy/dist * ENEMY_BULLET_SPEED
            else:
                bullet_dx, bullet_dy = 0, -ENEMY_BULLET_SPEED
            
            game.enemy_bullets.append(EnemyBullet(enemy.rect.centerx, enemy.rect.centery, bullet_dx, bullet_dy))
            enemy.last_shot = pygame.time.get_ticks()
            return True
    
    class PathfindToPlayer(Node):
        def run(self, enemy, game):
            if pygame.time.get_ticks() - enemy.last_path_update < 1000:
                return True
                
            enemy.last_path_update = pygame.time.get_ticks()
            start = (int(enemy.rect.centerx/GRID_CELL_SIZE), int(enemy.rect.centery/GRID_CELL_SIZE))
            end = (int(game.player.rect.centerx/GRID_CELL_SIZE), int(game.player.rect.centery/GRID_CELL_SIZE))
            
            path = AStarPathfinding.find_path(start, end, game.walls)
            if path and len(path) > 1:
                enemy.current_path = path[1:]
            return True
    
    class FollowPath(Node):
        def run(self, enemy, game):
            if not enemy.current_path:
                return False
                
            next_node = enemy.current_path[0]
            target_x = next_node[0]*GRID_CELL_SIZE + GRID_CELL_SIZE//2
            target_y = next_node[1]*GRID_CELL_SIZE + GRID_CELL_SIZE//2
            
            dx = target_x - enemy.rect.centerx
            dy = target_y - enemy.rect.centery
            dist = math.hypot(dx, dy)
            
            if dist < 5:
                enemy.current_path.pop(0)
                if not enemy.current_path:
                    return False
                next_node = enemy.current_path[0]
                dx = next_node[0]*GRID_CELL_SIZE + GRID_CELL_SIZE//2 - enemy.rect.centerx
                dy = next_node[1]*GRID_CELL_SIZE + GRID_CELL_SIZE//2 - enemy.rect.centery
                dist = math.hypot(dx, dy)
            
            if dist > 0:
                dx = dx/dist * enemy.speed
                dy = dy/dist * enemy.speed
                
                original_x = enemy.rect.x
                enemy.rect.x += dx
                for wall in game.walls:
                    if enemy.rect.colliderect(wall.rect):
                        enemy.rect.x = original_x
                        break
                
                original_y = enemy.rect.y
                enemy.rect.y += dy
                for wall in game.walls:
                    if enemy.rect.colliderect(wall.rect):
                        enemy.rect.y = original_y
                        break
            
            return True
        
        class Game:
    def __init__(self):
        self.reset_game()
        
        try:
            pygame.mixer.music.load(BACKGROUND_MUSIC)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except:
            print("No se pudo cargar la música de fondo")
    
    def reset_game(self):
        self.player = Player()
        self.walls = []
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.level = 1
        self.game_over = False
        self.level_complete = False
        self.in_menu = True
        self.generate_level()

    def generate_level(self):
        self.walls.clear()
        self.enemies.clear()
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.player.reset_position()
        self.player.current_bullets = MAX_BULLETS
        self.level_complete = False
        self.game_over = False

         border = 20
        self.walls.append(Wall(0, 0, WIDTH, border))
        self.walls.append(Wall(0, HEIGHT - border, WIDTH, border))
        self.walls.append(Wall(0, 0, border, HEIGHT))
        self.walls.append(Wall(WIDTH - border, 0, border, HEIGHT))

                for _ in range(10 + self.level * 2):
            valid = False
            attempts = 0
            while not valid and attempts < 100:
                x = random.randint(border, WIDTH - border - 50)
                y = random.randint(border, HEIGHT - border - 50)
                w = random.randint(20, 70)
                h = random.randint(20, 70)
                new_wall = Wall(x, y, w, h)
                
                dist_to_player = math.hypot(new_wall.rect.centerx - WIDTH//2, new_wall.rect.centery - HEIGHT//2)
                if dist_to_player > 150 and not any(new_wall.rect.colliderect(w.rect) for w in self.walls):
                    self.walls.append(new_wall)
                    valid = True
                attempts += 1

                        num_enemies = 3 + self.level * 2
        for _ in range(num_enemies):
            valid = False
            attempts = 0
            while not valid and attempts < 100:
                x = random.randint(border + ENEMY_RADIUS, WIDTH - border - ENEMY_RADIUS)
                y = random.randint(border + ENEMY_RADIUS, HEIGHT - border - ENEMY_RADIUS)
                enemy_rect = pygame.Rect(x - ENEMY_RADIUS, y - ENEMY_RADIUS, ENEMY_RADIUS*2, ENEMY_RADIUS*2)
                dist_to_player = math.hypot(x - WIDTH//2, y - HEIGHT//2)
                
                if (dist_to_player > 150 and
                    not any(enemy_rect.colliderect(w.rect) for w in self.walls)):
                    self.enemies.append(Enemy(x, y, self.level))
                    valid = True
                attempts += 1

    def update(self, dt):
        if self.game_over or self.level_complete or self.in_menu:
            return

        keys = pygame.key.get_pressed()

                dx = dy = 0
        if keys[K_LEFT] or keys[K_a]: dx = -1
        if keys[K_RIGHT] or keys[K_d]: dx = 1
        if keys[K_UP] or keys[K_w]: dy = -1
        if keys[K_DOWN] or keys[K_s]: dy = 1

                if keys[K_SPACE] and self.player.current_bullets > 0:
            bullet = self.player.shoot()
            if bullet:
                self.bullets.append(bullet)

                      if dx != 0 or dy != 0:
            self.player.move(dx, dy, self.walls, self.enemies)
        
                bullets_to_remove = []
        for i, bullet in enumerate(self.bullets):
            if not bullet.update(self.walls):
                bullets_to_remove.append(i)
                continue

            for j, enemy in enumerate(self.enemies):
                if bullet.rect.colliderect(enemy.rect):
                    bullets_to_remove.append(i)
                    enemy.vida -= 10
                    if enemy.vida <= 0:
                        self.enemies.pop(j)
                        self.player.score += 50 * self.level
                    break

        for i in sorted(bullets_to_remove, reverse=True):
            if i < len(self.bullets):
                self.bullets.pop(i)
