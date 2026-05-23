"""Trisolaran fleet and space probe system.

The player can build and deploy ships that interact with the three-body system.
Ships explore, collect data, and can be sacrificed to gain knowledge.
"""

import random
import math
import pygame
import numpy as np
from src.constants import *


class SpaceProbe:
    """A probe launched by the Trisolaran civilization."""

    PROBE_TYPES = {
        'scout': {
            'name': 'Scout Probe',
            'cost': 5,
            'speed': 8.0,
            'range': 300,
            'knowledge_gain': 5,
            'color': (100, 200, 255),
            'size': 3,
            'lifetime': 600,  # frames
        },
        'observer': {
            'name': 'Deep Observer',
            'cost': 10,
            'speed': 4.0,
            'range': 500,
            'knowledge_gain': 12,
            'color': (200, 200, 100),
            'size': 4,
            'lifetime': 900,
        },
        'lander': {
            'name': 'Sun Diver',
            'cost': 15,
            'speed': 12.0,
            'range': 200,
            'knowledge_gain': 20,
            'color': (255, 100, 50),
            'size': 5,
            'lifetime': 450,
        },
        'interstellar': {
            'name': 'Interstellar Ark',
            'cost': 30,
            'speed': 3.0,
            'range': 1000,
            'knowledge_gain': 35,
            'color': (150, 100, 255),
            'size': 6,
            'lifetime': 1200,
        },
    }

    def __init__(self, probe_type, start_pos, target_body=None, target_pos=None):
        spec = self.PROBE_TYPES[probe_type]
        self.probe_type = probe_type
        self.name = spec['name']
        self.pos = np.array(start_pos, dtype=np.float64)
        self.vel = np.zeros(2, dtype=np.float64)
        self.speed = spec['speed']
        self.range_left = spec['range']
        self.knowledge_gain = spec['knowledge_gain']
        self.color = spec['color']
        self.size = spec['size']
        self.lifetime = spec['lifetime']
        self.age = 0
        self.target_body = target_body
        self.target_pos = target_pos
        self.alive = True
        self.mission_complete = False
        self.trail = []
        self.data_collected = 0.0

    def update(self, simulation, dt):
        """Update probe position and behavior."""
        if not self.alive:
            return

        self.age += dt

        # Die of old age
        if self.age > self.lifetime:
            self.alive = False
            return

        # Update trail
        self.trail.append(self.pos.copy())
        if len(self.trail) > 100:
            self.trail.pop(0)

        # Determine target
        target_pos = self.target_pos
        if self.target_body is not None and self.target_body < len(simulation.bodies):
            target_pos = simulation.bodies[self.target_body].pos

        if target_pos is not None:
            # Navigate toward target
            direction = target_pos - self.pos
            dist = np.linalg.norm(direction)
            if dist > 0:
                self.vel = (direction / dist) * self.speed
                self.pos += self.vel * dt
                self.range_left -= np.linalg.norm(self.vel) * dt

                # Collect data when close to target
                if dist < 30:
                    self.data_collected += 0.5 * dt
                    if self.data_collected >= 100:
                        self.mission_complete = True

                # Check if reached target closely
                if dist < 5:
                    self.mission_complete = True
        else:
            # Drift in a straight line
            if np.linalg.norm(self.vel) == 0:
                self.vel = np.array([self.speed, 0])
            self.pos += self.vel * dt
            self.range_left -= self.speed * dt

        # Out of range
        if self.range_left <= 0:
            self.alive = False

    def get_reward(self):
        """Calculate knowledge reward on mission completion."""
        base = self.knowledge_gain
        # Bonus for data collected
        data_bonus = min(self.knowledge_gain, self.data_collected * 0.5)
        return base + data_bonus


class FleetManager:
    """Manages the Trisolaran space fleet."""

    def __init__(self):
        self.probes = []
        self.available_types = ['scout']  # Start with scouts only
        self.population_cost_factor = 0.5

    def can_build(self, probe_type, civilization):
        """Check if civilization can build this probe type."""
        if probe_type not in self.available_types:
            return False, "Technology not yet available"

        spec = SpaceProbe.PROBE_TYPES[probe_type]
        cost = spec['cost'] * self.population_cost_factor
        if civilization.population < cost:
            return False, f"Need {cost:.0f} population (have {civilization.population:.0f})"

        return True, f"Cost: {cost:.0f} population"

    def build(self, probe_type, start_pos, simulation, civilization, target_body=None):
        """Build and launch a probe."""
        can, msg = self.can_build(probe_type, civilization)
        if not can:
            return None, msg

        spec = SpaceProbe.PROBE_TYPES[probe_type]
        cost = spec['cost'] * self.population_cost_factor
        civilization.population = max(5, civilization.population - cost)

        # Set target to nearest sun if not specified
        if target_body is None:
            target_body = 0  # Default to first sun

        probe = SpaceProbe(probe_type, start_pos, target_body)
        self.probes.append(probe)
        return probe, f"Launched {spec['name']}!"

    def update(self, simulation, dt):
        """Update all probes."""
        results = []
        for probe in self.probes[:]:
            probe.update(simulation, dt)

            if probe.mission_complete and probe.alive:
                reward = probe.get_reward()
                results.append(('complete', probe, reward))
                probe.alive = False

        # Remove dead probes
        self.probes = [p for p in self.probes if p.alive]
        return results

    def unlock_tech(self, knowledge_level):
        """Unlock new probe types based on civilization knowledge."""
        if knowledge_level >= 25 and 'observer' not in self.available_types:
            self.available_types.append('observer')
        if knowledge_level >= 50 and 'lander' not in self.available_types:
            self.available_types.append('lander')
        if knowledge_level >= 80 and 'interstellar' not in self.available_types:
            self.available_types.append('interstellar')

    def get_probe_count(self):
        """Get count of active probes by type."""
        counts = {}
        for probe in self.probes:
            counts[probe.probe_type] = counts.get(probe.probe_type, 0) + 1
        return counts

    def draw(self, surface, camera):
        """Draw all active probes."""
        for probe in self.probes:
            if not probe.alive:
                continue

            screen_pos = camera.world_to_screen(probe.pos)
            sx, sy = int(screen_pos[0]), int(screen_pos[1])

            # Check if on screen
            if sx < -50 or sx > surface.get_width() + 50:
                continue
            if sy < -50 or sy > surface.get_height() + 50:
                continue

            # Draw trail
            if len(probe.trail) >= 2:
                for i in range(len(probe.trail) - 1):
                    p1 = camera.world_to_screen(probe.trail[i])
                    p2 = camera.world_to_screen(probe.trail[i + 1])
                    alpha = int(150 * (i / len(probe.trail)))
                    c = (*probe.color[:3], alpha)
                    try:
                        pygame.draw.line(surface, c,
                                         (int(p1[0]), int(p1[1])),
                                         (int(p2[0]), int(p2[1])), 1)
                    except Exception:
                        pass

            # Draw probe
            size = max(2, int(probe.size * camera.zoom))
            pygame.draw.circle(surface, probe.color, (sx, sy), size)
            # Bright center
            bright = tuple(min(255, c + 100) for c in probe.color[:3])
            pygame.draw.circle(surface, bright, (sx, sy), max(1, size // 2))

            # Direction indicator
            if np.linalg.norm(probe.vel) > 0:
                dir_vec = probe.vel / np.linalg.norm(probe.vel) * size * 2
                end_x = int(sx + dir_vec[0] * camera.zoom)
                end_y = int(sy + dir_vec[1] * camera.zoom)
                pygame.draw.line(surface, probe.color, (sx, sy), (end_x, end_y), 1)