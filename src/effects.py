"""Advanced visual effects for Three Body VR.

Nebula clouds, star fields, shockwaves, and other atmospheric effects.
"""

import math
import random
import colorsys
import pygame
import numpy as np
from src.constants import *


class NebulaRenderer:
    """Procedural nebula cloud rendering."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.nebula_surface = None
        self.nebula_offset_x = 0
        self.nebula_offset_y = 0
        self._generate_nebula()

    def _generate_nebula(self):
        """Generate a procedural nebula background texture."""
        surf = pygame.Surface((self.width * 2, self.height * 2), pygame.SRCALPHA)
        
        # Create several nebula clouds
        clouds = [
            {'x': self.width * 0.3, 'y': self.height * 0.4, 'size': 300, 'color': (0.4, 0.1, 0.5)},
            {'x': self.width * 1.2, 'y': self.height * 0.3, 'size': 350, 'color': (0.6, 0.1, 0.3)},
            {'x': self.width * 0.7, 'y': self.height * 1.1, 'size': 400, 'color': (0.1, 0.2, 0.6)},
            {'x': self.width * 1.5, 'y': self.height * 1.4, 'size': 280, 'color': (0.3, 0.0, 0.5)},
        ]

        for cloud in clouds:
            cx, cy = cloud['x'], cloud['y']
            size = cloud['size']
            h, s, v = cloud['color']

            # Draw multiple layers for each cloud
            for layer in range(4):
                layer_size = size * (1 + layer * 0.3)
                offset_x = random.uniform(-50, 50)
                offset_y = random.uniform(-50, 50)
                alpha = int(15 * (1 - layer * 0.25))

                # Create a soft circle using concentric rings
                for r in range(int(layer_size), 0, -2):
                    a = max(0, int(alpha * (1 - r / layer_size) ** 1.5))
                    if a == 0:
                        break
                    
                    # Slight color variation per ring
                    hue = (h + random.uniform(-0.05, 0.05)) % 1.0
                    rgb = colorsys.hsv_to_rgb(hue, s, v)
                    color = (
                        int(max(0, min(255, rgb[0] * 255))),
                        int(max(0, min(255, rgb[1] * 255))),
                        int(max(0, min(255, rgb[2] * 255))),
                        a,
                    )

                    pygame.draw.circle(
                        surf, color,
                        (int(cx + offset_x), int(cy + offset_y)), r
                    )

        self.nebula_surface = surf
        self.nebula_offset_x = random.randint(0, self.width)
        self.nebula_offset_y = random.randint(0, self.height)

    def draw(self, surface, camera_offset=None):
        """Draw nebula background, slowly panning for parallax."""
        if self.nebula_surface is None:
            self._generate_nebula()

        # Slow drift
        drift_speed = 0.05
        self.nebula_offset_x = (self.nebula_offset_x + drift_speed) % self.width
        self.nebula_offset_y = (self.nebula_offset_y + drift_speed * 0.7) % self.height

        # Draw with parallax from camera
        px = int(-self.nebula_offset_x * 0.2) if camera_offset is None else int(-camera_offset[0] * 0.02)
        py = int(-self.nebula_offset_y * 0.2) if camera_offset is None else int(-camera_offset[1] * 0.02)

        surface.blit(self.nebula_surface, (px, py))


class ShockwaveEffect:
    """Expanding ring shockwave for dramatic events."""

    def __init__(self):
        self.shockwaves = []

    def emit(self, pos, color=(255, 255, 200), max_radius=300, duration=60):
        """Create a new shockwave."""
        self.shockwaves.append({
            'pos': np.array(pos),
            'radius': 5,
            'max_radius': max_radius,
            'duration': duration,
            'elapsed': 0,
            'color': color,
        })

    def update(self):
        """Update all shockwaves."""
        alive = []
        for sw in self.shockwaves:
            sw['elapsed'] += 1
            sw['radius'] = sw['max_radius'] * (sw['elapsed'] / sw['duration'])
            if sw['elapsed'] < sw['duration']:
                alive.append(sw)
        self.shockwaves = alive

    def draw(self, surface, camera):
        """Draw shockwaves."""
        for sw in self.shockwaves:
            progress = sw['elapsed'] / sw['duration']
            alpha = int(255 * (1 - progress))
            screen_pos = camera.world_to_screen(sw['pos'])
            sx, sy = int(screen_pos[0]), int(screen_pos[1])
            screen_radius = int(sw['radius'] * camera.zoom)

            if screen_radius > 0 and screen_radius < surface.get_width():
                color = (*sw['color'][:3], alpha)
                pygame.draw.circle(
                    surface, color,
                    (sx, sy), screen_radius, max(1, int(3 * (1 - progress)))
                )


class ScreenShake:
    """Screen shake effect for dramatic moments."""

    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.elapsed = 0
        self.offset = np.array([0.0, 0.0])

    def trigger(self, intensity=10, duration=20):
        """Start a screen shake."""
        self.intensity = intensity
        self.duration = duration
        self.elapsed = 0

    def update(self):
        """Update shake offset."""
        if self.elapsed < self.duration:
            decay = 1 - self.elapsed / self.duration
            self.offset = np.array([
                random.uniform(-1, 1) * self.intensity * decay,
                random.uniform(-1, 1) * self.intensity * decay,
            ])
            self.elapsed += 1
        else:
            self.offset = np.array([0.0, 0.0])

    def get_offset(self):
        return self.offset


class TransitionEffect:
    """Fade in/out transitions between game states."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fade_alpha = 0
        self.fade_speed = 5
        self.fading_in = False
        self.fading_out = False
        self.complete = False

    def start_fade_in(self, speed=5):
        """Start fade in from black."""
        self.fade_alpha = 255
        self.fade_speed = speed
        self.fading_in = True
        self.fading_out = False
        self.complete = False

    def start_fade_out(self, speed=5):
        """Start fade out to black."""
        self.fade_alpha = 0
        self.fade_speed = speed
        self.fading_out = True
        self.fading_in = False
        self.complete = False

    def update(self):
        """Update fade state."""
        if self.fading_in:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha == 0:
                self.fading_in = False
                self.complete = True
        elif self.fading_out:
            self.fade_alpha = min(255, self.fade_alpha + self.fade_speed)
            if self.fade_alpha >= 255:
                self.fading_out = False
                self.complete = True

    def draw(self, surface):
        """Draw fade overlay."""
        if self.fade_alpha > 0 or self.fading_out:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.fade_alpha)))
            surface.blit(overlay, (0, 0))