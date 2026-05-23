"""Capture a polished gameplay screenshot with all features visible."""
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
from src.fleet import FleetManager, SpaceProbe

pygame.init()
screen = pygame.display.set_mode((1200, 800), pygame.NOFRAME)
W, H = 1200, 800

# Build scene
renderer = Renderer(screen)
sim = create_three_body_system('default')
planet = create_planet(sim, pos=(100, 100), vel=(0, 30), name="Trisolaris")
civ = Civilization()
lore = LoreEngine()
starfield = Starfield(W, H, 300)
nebula = NebulaRenderer(W, H)
fleet = FleetManager()

# Run interesting physics
for _ in range(80):
    sim.step(0.15)
    stability = sim.get_stability_metric()
    civ.update(stability, 0.02)
    lore.update(0.1, civ.current_era, stability, civ.knowledge)

# Launch a couple of probes for visual interest
fleet.build('scout', planet.pos, sim, civ, target_body=0)
# Push more knowledge to unlock observer
civ.knowledge = 30
fleet.unlock_tech(30)
fleet.build('observer', planet.pos, sim, civ, target_body=1)

# Update probes a bit
for _ in range(10):
    sim.step(0.1)
    fleet.update(sim, 0.1)

# Force a nice quote
lore.current_quote = (
    '"You must know that the universe is a dark forest. '
    'Every civilization is a hunter, stalking through the trees."'
)
lore.quote_timer = 500

# Render everything
starfield.update(0.5, 0.3)
starfield.draw(screen)
nebula.draw(screen, camera_offset=renderer.camera.offset)
renderer.render(sim, civ.current_era, sim.get_stability_metric(),
                civ.population, 'observe', 1.0, False)

# Draw fleet
fleet.draw(screen, renderer.camera)

# HUD info
font = pygame.font.Font(None, 18)
# Temp
planet_idx = len(sim.bodies) - 1
temp = sim.get_planet_temperature(planet_idx)
temp_color = (200, 200, 100) if -20 < temp < 40 else (255, 150, 50) if temp > 40 else (100, 150, 255)
temp_label = font.render(f"Temp: {temp:.0f}°C", True, temp_color)
screen.blit(temp_label, (10, 35))

# Fleet status
probe_counts = fleet.get_probe_count()
fy = 55
for ptype, count in probe_counts.items():
    spec = SpaceProbe.PROBE_TYPES[ptype]
    fl = font.render(f"{spec['name']}: {count}", True, spec['color'])
    screen.blit(fl, (10, fy))
    fy += 16

# Era indicator
era_color = (100, 255, 100) if civ.current_era == 'stable' else (255, 150, 50)
era_label = font.render(f"Era: {civ.current_era.upper()}", True, era_color)
screen.blit(era_label, (10, 10))

# Knowledge
know_label = font.render(f"Knowledge: {civ.knowledge:.0f}%", True, (100, 200, 255))
screen.blit(know_label, (W - know_label.get_width() - 10, 10))

# Population
pop_label = font.render(f"Pop: {civ.population:.0f}/{civ.max_population:.0f}", True, (255, 255, 255))
screen.blit(pop_label, (W - pop_label.get_width() - 10, 30))

# Quote
quote = lore.get_active_quote()
if quote:
    renderer.draw_quote(quote)

filename = 'screenshot_gameplay.png'
pygame.image.save(screen, filename)
print(f"Screenshot: {filename} ({os.path.getsize(filename)} bytes), {W}x{H}")
pygame.quit()