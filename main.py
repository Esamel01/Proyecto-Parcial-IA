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