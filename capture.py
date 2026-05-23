"""Capture a polished gameplay screenshot."""
import os
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
import sys
sys.path.insert(0, '.')
from src.nbody import create_three_body_system, create_planet
from src.renderer import Renderer
from src.civilization import Civilization
from src.lore import LoreEngine
from src.starfield import Starfield
from src.effects import NebulaRenderer

pygame.init()
screen = pygame.display.set_mode((1200, 800), pygame.NOFRAME)
renderer = Renderer(screen)
sim = create_three_body_system('default')
planet = create_planet(sim, pos=(100, 100), vel=(0, 30), name="Trisolaris")
civ = Civilization()
lore = LoreEngine()
starfield = Starfield(1200, 800, 300)
nebula = NebulaRenderer(1200, 800)

# Run physics to get interesting orbital pattern with some variety
for _ in range(50):
    sim.step(0.2)
sim.step(0.1)

# Run more with different time steps for chaos
for _ in range(40):
    sim.step(0.15)
    stability = sim.get_stability_metric()
    civ.update(stability, 0.02)
    lore.update(0.1, civ.current_era, stability, civ.knowledge)

# Force a dramatic quote
lore.current_quote = (
    "The universe is a dark forest. Every civilization "
    "is a silent hunter stalking through the trees."
)
lore.quote_timer = 500

# Render with full effects
starfield.update()
starfield.draw(screen)
nebula.draw(screen, camera_offset=renderer.camera.offset)
renderer.render(sim, civ.current_era, sim.get_stability_metric(),
                civ.population, 'observe', 1.0, False)
quote = lore.get_active_quote()
if quote:
    renderer.draw_quote(quote)

filename = 'screenshot_gameplay.png'
pygame.image.save(screen, filename)
print(f"Screenshot saved: {filename} ({os.path.getsize(filename)} bytes)")
pygame.quit()