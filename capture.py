import os
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import pygame
import sys
sys.path.insert(0, '.')
from src.nbody import create_three_body_system, create_planet
from src.renderer import Renderer
from src.civilization import Civilization
from src.lore import LoreEngine

pygame.init()
screen = pygame.display.set_mode((1200, 800), pygame.NOFRAME)
renderer = Renderer(screen)
sim = create_three_body_system()
planet = create_planet(sim, pos=(100, 100), vel=(0, 30), name="Trisolaris")
civ = Civilization()
lore = LoreEngine()

# Run some physics to get interesting orbits
for _ in range(80):
    sim.step(0.1)
    stability = sim.get_stability_metric()
    civ.update(stability, 0.01)
    lore.update(0.1, civ.current_era, stability, civ.knowledge)

# Force a quote
lore.current_quote = "The universe is a dark forest. Every civilization is a silent hunter."
lore.quote_timer = 300

# Render
renderer.render(sim, civ.current_era, sim.get_stability_metric(),
                civ.population, 'observe', 1.0, False)
quote = lore.get_active_quote()
renderer.draw_quote(quote)

pygame.image.save(screen, 'screenshot_gameplay.png')
print(f"Screenshot saved: {os.path.getsize('screenshot_gameplay.png')} bytes")
pygame.quit()
