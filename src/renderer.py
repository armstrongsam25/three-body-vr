"""Renderer for the Three Body VR game with VR-like visual effects."""

import math
import random
import pygame
import numpy as np
from src.constants import *


class Camera:
    """Camera for pan/zoom of the simulation view."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.offset = np.array([0.0, 0.0])
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.target_offset = np.array([0.0, 0.0])
        self.smooth_factor = 0.1

    def world_to_screen(self, world_pos):
        """Convert world coordinates to screen coordinates."""
        center = np.array([self.width / 2, self.height / 2])
        return (world_pos - self.offset) * self.zoom + center

    def screen_to_world(self, screen_pos):
        """Convert screen coordinates to world coordinates."""
        center = np.array([self.width / 2, self.height / 2])
        return (screen_pos - center) / self.zoom + self.offset

    def update(self):
        """Smooth camera movement."""
        self.zoom += (self.target_zoom - self.zoom) * self.smooth_factor
        self.offset += (self.target_offset - self.offset) * self.smooth_factor

    def pan(self, dx, dy):
        """Pan camera by screen-space delta."""
        self.target_offset -= np.array([dx, dy]) / self.zoom

    def zoom_at(self, factor, screen_pos):
        """Zoom camera centered at screen position."""
        world_pos = self.screen_to_world(np.array(screen_pos))
        self.target_zoom = max(0.1, min(5.0, self.target_zoom * factor))
        # Adjust offset to keep world_pos under cursor
        new_screen = self.world_to_screen(world_pos)
        # (not strictly needed for smooth camera as target_offset handles it)


class Renderer:
    """Handles all rendering for the game."""

    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.camera = Camera(self.width, self.height)
        self.vr_scanline_offset = 0
        self.particle_system = ParticleSystem()

        # Glow surfaces for suns (pre-rendered)
        self.glow_surfaces = {}
        self._create_glow_surfaces()

        # Fonts
        self.font_small = pygame.font.Font(None, 18)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_large = pygame.font.Font(None, 42)
        self.font_huge = pygame.font.Font(None, 64)

    def _create_glow_surfaces(self):
        """Pre-render glow effects for suns."""
        for radius in [12, 16, 18, 20, 24]:
            size = radius * 8
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            cx, cy = size // 2, size // 2
            
            # Multi-layer glow
            for r in range(size // 2, 0, -1):
                alpha = max(0, int(80 * (1 - r / (size / 2)) ** 2))
                color = (255, 200, 80, alpha)
                pygame.draw.circle(surf, color, (cx, cy), r)
            
            self.glow_surfaces[radius] = surf

    def draw_background(self, stability):
        """Draw space background with nebula effects."""
        # Gradient background
        for y in range(0, self.height, 2):
            t = y / self.height
            r = int(5 + 10 * t)
            g = int(5 + 5 * t)
            b = int(25 + 15 * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))

        # Stars
        # Use seeded positions for consistent stars
        np.random.seed(42)
        star_count = 200
        for _ in range(star_count):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            brightness = np.random.randint(40, 200)
            size = 1 if np.random.random() < 0.9 else 2
            color = (brightness, brightness, brightness)
            self.screen.set_at((x, y), color)
        np.random.seed()

    def draw_vr_overlay(self):
        """Draw VR headset style overlay effects."""
        # Scanlines
        self.vr_scanline_offset = (self.vr_scanline_offset + 1) % SCANLINE_SPACING
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 0))

        for y in range(self.vr_scanline_offset, self.height, SCANLINE_SPACING):
            pygame.draw.line(
                overlay, (0, 0, 0, OVERLAY_ALPHA),
                (0, y), (self.width, y)
            )

        # Vignette
        vignette_center = (self.width // 2, self.height // 2)
        max_dist = math.sqrt(self.width**2 + self.height**2) / 2
        for r in range(int(max_dist), int(max_dist * 0.3), -2):
            alpha = int(VR_VIGNETTE_STRENGTH * 255 * (1 - r / max_dist))
            pygame.draw.circle(
                overlay, (0, 0, 0, alpha),
                vignette_center, r
            )

        # Subtle chromatic aberration edges
        edge_width = 3
        for i in range(edge_width):
            alpha = 30 - i * 8  # Fading edge effect
            if alpha <= 0:
                break
            # Top
            pygame.draw.rect(overlay, (40, 0, 0, alpha),
                             (0, 0, self.width, 1))
            # Bottom
            pygame.draw.rect(overlay, (0, 0, 40, alpha),
                             (0, self.height - 1, self.width, 1))
            # Left
            pygame.draw.rect(overlay, (0, 40, 0, alpha),
                             (0, 0, 1, self.height))
            # Right
            pygame.draw.rect(overlay, (40, 0, 0, alpha),
                             (self.width - 1, 0, 1, self.height))

        self.screen.blit(overlay, (0, 0))

    def draw_sun(self, pos, radius, color, name=""):
        """Draw a sun with glow effect."""
        screen_pos = self.camera.world_to_screen(pos)
        sx, sy = int(screen_pos[0]), int(screen_pos[1])
        screen_radius = max(1, int(radius * self.camera.zoom))

        if screen_radius < 2:
            # Draw as bright point
            pygame.draw.circle(self.screen, color, (sx, sy), 2)
            return

        # Draw glow
        glow_radius = max(4, screen_radius * 3)
        glow_alpha = 60
        for r in range(glow_radius, screen_radius, -2):
            alpha = max(0, glow_alpha - (glow_radius - r) * 2)
            glow_color = (*color[:3], alpha)
            glow_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, glow_color, (r + 1, r + 1), r)
            self.screen.blit(glow_surf, (sx - r, sy - r))

        # Main body
        pygame.draw.circle(self.screen, color, (sx, sy), screen_radius)
        
        # Bright center
        highlight_radius = max(1, screen_radius // 3)
        lighter = tuple(min(255, c + 80) for c in color[:3])
        pygame.draw.circle(self.screen, lighter, (sx, sy), highlight_radius)

        # Name label
        if name and screen_radius > 5:
            label = self.font_small.render(name, True, WHITE)
            self.screen.blit(label, (sx - label.get_width() // 2, sy + screen_radius + 8))

    def draw_planet(self, pos, radius, color, name="", population=0):
        """Draw a planet."""
        screen_pos = self.camera.world_to_screen(pos)
        sx, sy = int(screen_pos[0]), int(screen_pos[1])
        screen_radius = max(2, int(radius * self.camera.zoom))

        # Planet body
        pygame.draw.circle(self.screen, color, (sx, sy), screen_radius)
        
        # Atmosphere glow
        if screen_radius > 3:
            atmos_color = (*color[:3], 40)
            atmos_surf = pygame.Surface(
                (screen_radius * 3, screen_radius * 3), pygame.SRCALPHA
            )
            pygame.draw.circle(atmos_surf, atmos_color,
                               (screen_radius * 3 // 2, screen_radius * 3 // 2),
                               int(screen_radius * 1.5))
            self.screen.blit(atmos_surf, (sx - screen_radius * 3 // 2,
                                          sy - screen_radius * 3 // 2))

        # Name label
        if name and screen_radius > 3:
            label = self.font_small.render(name, True, CYAN)
            self.screen.blit(label, (sx - label.get_width() // 2, sy + screen_radius + 5))

    def draw_orbit_trail(self, trail, color, alpha_start=255, alpha_end=30):
        """Draw an orbit trail with fading."""
        if len(trail) < 2:
            return

        points = []
        for i, pos in enumerate(trail):
            screen_pos = self.camera.world_to_screen(pos)
            points.append((int(screen_pos[0]), int(screen_pos[1])))

        # Draw in segments for fading effect
        total = len(points)
        for i in range(len(points) - 1):
            t = i / total
            alpha = int(alpha_end + (alpha_start - alpha_end) * t)
            color_with_alpha = (*color[:3], alpha)
            pygame.draw.line(self.screen, color_with_alpha, points[i], points[i + 1], 1)

    def draw_prediction_trail(self, trail, color):
        """Draw predicted orbit (dashed/dotted)."""
        if len(trail) < 2:
            return

        screen_points = []
        for pos in trail:
            sp = self.camera.world_to_screen(pos)
            screen_points.append((int(sp[0]), int(sp[1])))

        # Dashed line
        for i in range(0, len(screen_points) - 1, 4):
            if i + 1 < len(screen_points):
                pygame.draw.line(
                    self.screen, color,
                    screen_points[i], screen_points[i + 1], 1
                )

    def draw_gravitational_grid(self, bodies):
        """Draw gravitational field lines / grid distortion."""
        # Grid resolution
        grid_size = 80
        world_corners = [
            self.camera.screen_to_world((0, 0)),
            self.camera.screen_to_world((self.width, self.height)),
        ]
        wx_min = min(c[0] for c in world_corners)
        wx_max = max(c[0] for c in world_corners)
        wy_min = min(c[1] for c in world_corners)
        wy_max = max(c[1] for c in world_corners)

        step_x = (wx_max - wx_min) / grid_size
        step_y = (wy_max - wy_min) / grid_size

        for i in range(grid_size + 1):
            pts = []
            wy = wy_min + i * step_y
            for j in range(grid_size + 1):
                wx = wx_min + j * step_x
                # Distort based on gravitational influence
                distorted = np.array([wx, wy])
                for body in bodies:
                    if not body.is_sun:
                        continue
                    r_vec = distorted - body.pos
                    dist = np.linalg.norm(r_vec) + SOFTENING
                    if dist < 300:
                        force_dir = r_vec / dist
                        distortion = force_dir * body.mass * G / (dist * 10)
                        distorted += distortion

                screen = self.camera.world_to_screen(distorted)
                if 0 <= screen[0] <= self.width and 0 <= screen[1] <= self.height:
                    pts.append((int(screen[0]), int(screen[1])))

            if len(pts) >= 2:
                # Draw as connected faint lines
                for k in range(len(pts) - 1):
                    alpha = 10
                    pygame.draw.line(
                        self.screen, (80, 80, 160, alpha),
                        pts[k], pts[k + 1], 1
                    )

    def draw_hud(self, era, stability, time, population, mode, time_scale):
        """Draw game HUD."""
        # Era indicator
        if era == ERA_STABLE:
            era_color = GREEN
            era_text = "STABLE ERA"
        elif era == ERA_CHAOTIC:
            era_color = BRIGHT_RED
            era_text = "CHAOTIC ERA"
        else:
            era_color = YELLOW
            era_text = "TRANSITION"

        era_surf = self.font_large.render(era_text, True, era_color)
        era_rect = era_surf.get_rect(midtop=(self.width // 2, 10))
        self.screen.blit(era_surf, era_rect)

        # Stability bar
        bar_width = 200
        bar_height = 12
        bar_x = self.width // 2 - bar_width // 2
        bar_y = 55
        pygame.draw.rect(self.screen, DARK_GRAY,
                         (bar_x, bar_y, bar_width, bar_height))
        stable_width = int(stability * bar_width)
        bar_color = (
            int(255 * (1 - stability)),
            int(255 * stability),
            40
        )
        pygame.draw.rect(self.screen, bar_color,
                         (bar_x, bar_y, stable_width, bar_height))
        pygame.draw.rect(self.screen, WHITE,
                         (bar_x, bar_y, bar_width, bar_height), 1)

        # Stability label
        stab_label = self.font_small.render(
            f"Stability: {stability:.1%}", True, WHITE
        )
        self.screen.blit(stab_label, (bar_x, bar_y + bar_height + 3))

        # Time
        time_label = self.font_small.render(
            f"Time: {time:.1f} cycles | Speed: {time_scale:.1f}x", True, GRAY
        )
        self.screen.blit(time_label, (10, self.height - 25))

        # Population
        pop_label = self.font_small.render(
            f"Population: {population:.1f}M", True, CYAN
        )
        self.screen.blit(pop_label, (10, 10))

        # Mode
        mode_label = self.font_small.render(
            f"Mode: {mode.upper()}", True, YELLOW
        )
        self.screen.blit(mode_label, (self.width - mode_label.get_width() - 10, 10))

        # Help hint
        hint = self.font_small.render("H: Help | Space: Pause | +/-: Speed | Arrow Keys: Pan | E: Predict", True, GRAY)
        self.screen.blit(hint, (self.width // 2 - hint.get_width() // 2, self.height - 50))

    def render(self, simulation, era, stability, population, mode, time_scale, paused):
        """Main render function."""
        self.camera.update()
        
        # Clear
        self.draw_background(stability)

        # Gravitational grid
        self.draw_gravitational_grid(simulation.bodies)

        # Draw orbit trails
        for body in simulation.bodies:
            if body.is_sun:
                trail_color = body.color
            else:
                trail_color = CYAN
            self.draw_orbit_trail(body.trail, trail_color)

        # Draw prediction if in predict mode (placeholder for now)
        if mode == MODE_PREDICT:
            # Simulate forward 200 steps for prediction
            pred_sim = simulation.copy()
            for body in pred_sim.bodies:
                body.trail = []
            for _ in range(200):
                pred_sim.step(0.1)
            for body in pred_sim.bodies:
                pred_trail_color = (*body.color[:3], 150)
                self.draw_prediction_trail(body.trail, pred_trail_color)

        # Draw bodies
        for body in simulation.bodies:
            if body.is_sun:
                self.draw_sun(body.pos, body.radius, body.color, body.name)
            else:
                self.draw_planet(body.pos, body.radius, body.color, body.name, population)

        # Particles
        self.particle_system.update()
        self.particle_system.draw(self.screen, self.camera)

        # VR overlay effects
        self.draw_vr_overlay()

        # HUD
        self.draw_hud(era, stability, simulation.time, population, mode, time_scale)

        # Pause overlay
        if paused:
            pause_surf = self.font_huge.render("PAUSED", True, WHITE)
            pause_rect = pause_surf.get_rect(center=(self.width // 2, self.height // 2 - 50))
            # Semi-transparent background
            bg = pygame.Surface((pause_surf.get_width() + 40, pause_surf.get_height() + 20))
            bg.set_alpha(128)
            bg.fill(BLACK)
            self.screen.blit(bg, (pause_rect.x - 20, pause_rect.y - 10))
            self.screen.blit(pause_surf, pause_rect)


class ParticleSystem:
    """Manages visual particle effects."""

    def __init__(self):
        self.particles = []

    def emit(self, pos, count=5, color=(255, 200, 50), speed=2.0, lifetime=30):
        """Emit particles at a position."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            mag = random.uniform(0.5, speed)
            vel = np.array([math.cos(angle), math.sin(angle)]) * mag
            self.particles.append({
                'pos': np.array(pos),
                'vel': vel,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'color': color,
            })

    def update(self):
        """Update all particles."""
        alive = []
        for p in self.particles:
            p['pos'] += p['vel']
            p['lifetime'] -= 1
            if p['lifetime'] > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, screen, camera):
        """Draw particles."""
        for p in self.particles:
            alpha = int(255 * p['lifetime'] / p['max_lifetime'])
            color = (*p['color'][:3], alpha)
            screen_pos = camera.world_to_screen(p['pos'])
            sx, sy = int(screen_pos[0]), int(screen_pos[1])
            if 0 <= sx < screen.get_width() and 0 <= sy < screen.get_height():
                size = max(1, int(3 * p['lifetime'] / p['max_lifetime']))
                if size == 1:
                    screen.set_at((sx, sy), color[:3])
                else:
                    pygame.draw.circle(screen, color, (sx, sy), size)