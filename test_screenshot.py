import os
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
import sys
sys.path.insert(0, '.')
from src.nbody import create_three_body_system, create_planet
from src.renderer import Renderer

pygame.init()
screen = pygame.display.set_mode((1200, 800), pygame.NOFRAME)
renderer = Renderer(screen)
sim = create_three_body_system()
planet = create_planet(sim, pos=(100, 100), vel=(0, 30), name="Trisolaris")

# Run a few physics steps
for _ in range(50):
    sim.step(0.1)

# Render
renderer.render(sim, 'stable', 0.75, 65.0, 'observe', 1.0, False)
pygame.image.save(screen, 'screenshot.png')
print("Screenshot saved!")
pygame.quit()
