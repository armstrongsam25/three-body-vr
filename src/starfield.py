"""Procedural starfield with parallax scrolling for Three Body VR."""

import random
import pygame
import numpy as np


class Starfield:
    """Multi-layer starfield with parallax scrolling."""

    def __init__(self, width, height, num_stars=300, num_layers=3):
        self.width = width
        self.height = height
        self.num_layers = num_layers
        self.layers = []

        for layer in range(num_layers):
            stars = []
            count = num_stars // (layer + 1)
            for _ in range(count):
                stars.append({
                    'x': random.randint(0, width),
                    'y': random.randint(0, height),
                    'brightness': random.randint(20, 255),
                    'size': 1 if random.random() < 0.85 else 2,
                })
            # Bright stars with color
            for _ in range(count // 10):
                color_choice = random.choice([
                    (180, 200, 255),  # Blue-white
                    (255, 240, 200),  # Yellow-white
                    (255, 180, 180),  # Reddish
                    (200, 180, 255),  # Purple
                ])
                stars.append({
                    'x': random.randint(0, width),
                    'y': random.randint(0, height),
                    'color': color_choice,
                    'brightness': random.randint(150, 255),
                    'size': 2,
                })

            self.layers.append({
                'stars': stars,
                'speed': 0.05 + layer * 0.08,  # Parallax speed
                'offset_x': 0.0,
                'offset_y': 0.0,
            })

    def update(self, camera_dx=0, camera_dy=0):
        """Update star positions for scrolling."""
        for layer in self.layers:
            layer['offset_x'] = (layer['offset_x'] + camera_dx * layer['speed']) % self.width
            layer['offset_y'] = (layer['offset_y'] + camera_dy * layer['speed']) % self.height

    def draw(self, surface):
        """Draw starfield."""
        for layer in self.layers:
            for star in layer['stars']:
                x = (star['x'] + layer['offset_x']) % self.width
                y = (star['y'] + layer['offset_y']) % self.height

                if 'color' in star:
                    color = star['color']
                else:
                    b = star['brightness']
                    color = (b, b, b)

                if star['size'] == 1:
                    surface.set_at((int(x), int(y)), color)
                else:
                    # Draw small circle for larger stars
                    pygame.draw.circle(surface, color, (int(x), int(y)), star['size'])


class BloomRenderer:
    """Simple bloom/glow effect for bright objects."""

    def __init__(self):
        pass

    @staticmethod
    def draw_bloom(surface, pos, base_color, radius, intensity=0.6):
        """Draw a bloom glow effect at position."""
        layers = [
            (radius * 3, int(30 * intensity)),
            (radius * 2, int(60 * intensity)),
            (radius * 1.5, int(100 * intensity)),
            (radius, int(150 * intensity)),
        ]

        for r, alpha in layers:
            if alpha <= 0:
                continue
            color = (*base_color[:3], alpha)
            try:
                pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), int(r))
            except TypeError:
                pass  # Might fail for non-RGBA surfaces in some pygame versions