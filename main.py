#!/usr/bin/env python3
"""Three Body VR - Main entry point.

A game inspired by Liu Cixin's The Three Body Problem.
Enter the VR world of Trisolaris and attempt to solve the chaotic three-body problem.
"""

import sys
import math
import pygame
import numpy as np

from src.constants import *
from src.nbody import (
    NBodySimulation, CelestialBody,
    create_three_body_system, create_planet,
)
from src.renderer import Renderer
from src.civilization import Civilization, MilestoneTracker


class Game:
    """Main game class."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.RESIZABLE
        )
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.fullscreen = False

        # Game state
        self.mode = MODE_OBSERVE
        self.time_scale = TIME_SCALE
        self.show_help = False
        self.show_events = False
        self.event_display_timer = 0
        self.milestone_popup = None
        self.milestone_popup_timer = 0

        # Simulation
        self.simulation = create_three_body_system()
        self.planet = create_planet(
            self.simulation,
            pos=(100, 100),
            vel=(0, 30),
            name="Trisolaris"
        )

        # Civilization
        self.civilization = Civilization()
        self.milestones = MilestoneTracker()

        # Renderer
        self.renderer = Renderer(self.screen)

        # Camera dragging
        self.dragging = False
        self.drag_start = (0, 0)
        self.last_mouse = (0, 0)

        # Game state tracking
        self.frame_count = 0
        self.auto_pan_speed = 0.3  # Slow auto-pan

    def handle_input(self):
        """Process keyboard and mouse input."""
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Pan with arrow keys / WASD
        pan_speed = 5
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.renderer.camera.pan(-pan_speed, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.renderer.camera.pan(pan_speed, 0)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.renderer.camera.pan(0, -pan_speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.renderer.camera.pan(0, pan_speed)

        # Zooming
        if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:
            self.renderer.camera.target_zoom = min(5.0, self.renderer.camera.target_zoom * 1.02)
        if keys[pygame.K_MINUS]:
            self.renderer.camera.target_zoom = max(0.1, self.renderer.camera.target_zoom * 0.98)

        # Time scale
        if keys[pygame.K_LEFTBRACKET]:
            self.time_scale = max(MIN_TIME_SCALE, self.time_scale * 0.95)
        if keys[pygame.K_RIGHTBRACKET]:
            self.time_scale = min(MAX_TIME_SCALE, self.time_scale * 1.05)

        # Mouse drag pan
        if mouse[0]:
            if not self.dragging:
                self.dragging = True
                self.drag_start = mouse_pos
            else:
                dx = mouse_pos[0] - self.last_mouse[0]
                dy = mouse_pos[1] - self.last_mouse[1]
                self.renderer.camera.pan(-dx, -dy)
        else:
            self.dragging = False

        # Mouse wheel zoom
        self.last_mouse = mouse_pos

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused

                elif event.key == pygame.K_e:
                    # Toggle predict mode
                    self.mode = MODE_PREDICT if self.mode == MODE_OBSERVE else MODE_OBSERVE
                    if self.mode == MODE_PREDICT:
                        self.milestones.milestones['first_prediction'] = True

                elif event.key == pygame.K_r:
                    # Reset simulation
                    self.simulation = create_three_body_system()
                    self.planet = create_planet(
                        self.simulation,
                        pos=(100, 100),
                        vel=(0, 30),
                        name="Trisolaris"
                    )
                    self.civilization = Civilization()
                    self.renderer.camera.offset = np.array([0.0, 0.0])
                    self.renderer.camera.target_zoom = 1.0

                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help

                elif event.key == pygame.K_TAB:
                    self.show_events = not self.show_events

                elif event.key == pygame.K_f:
                    self.fullscreen = not self.fullscreen
                    if self.fullscreen:
                        self.screen = pygame.display.set_mode(
                            (0, 0), pygame.FULLSCREEN
                        )
                    else:
                        self.screen = pygame.display.set_mode(
                            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE
                        )
                    self.renderer = Renderer(self.screen)

                elif event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_0:
                    self.time_scale = 1.0

                elif event.key == pygame.K_1:
                    self.time_scale = 0.5

                elif event.key == pygame.K_2:
                    self.time_scale = 2.0

                elif event.key == pygame.K_5:
                    self.time_scale = 5.0

                elif event.key == pygame.K_c:
                    # Center on planet
                    self.renderer.camera.target_offset = self.planet.pos.copy()

            elif event.type == pygame.MOUSEWHEEL:
                zoom_factor = 1.1 if event.y > 0 else 0.9
                self.renderer.camera.target_zoom *= zoom_factor
                self.renderer.camera.target_zoom = max(0.1, min(5.0, self.renderer.camera.target_zoom))

            elif event.type == pygame.VIDEORESIZE:
                self.renderer.width = event.w
                self.renderer.height = event.h
                self.renderer.camera.width = event.w
                self.renderer.camera.height = event.h

    def draw_help(self):
        """Draw help overlay."""
        overlay = pygame.Surface(
            (self.renderer.width, self.renderer.height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        lines = [
            "THREE BODY VR - CONTROLS",
            "",
            "Space     - Pause / Resume",
            "E         - Toggle Prediction Mode",
            "R         - Reset Simulation",
            "C         - Center on Trisolaris",
            "H         - Toggle Help",
            "Tab       - Toggle Event Log",
            "F         - Fullscreen",
            "0,1,2,5   - Set Time Speed",
            "[/]       - Adjust Time Scale",
            "+/-        - Zoom In / Out",
            "Arrow Keys - Pan View",
            "Mouse Drag - Pan View",
            "Mouse Wheel - Zoom",
            "Esc       - Quit",
            "",
            "GOAL: Help Trisolaran civilization survive",
            "by understanding the three-body problem.",
            "Observe the orbital patterns, predict era changes,",
            "and guide civilization through Stable Eras.",
            "",
            "Press H to close",
        ]

        y = 50
        for line in lines:
            if line.startswith("THREE"):
                surf = self.renderer.font_large.render(line, True, YELLOW)
            elif line == "":
                y += 10
                continue
            else:
                surf = self.renderer.font_small.render(line, True, WHITE)

            x = self.renderer.width // 2 - surf.get_width() // 2
            self.screen.blit(surf, (x, y))
            y += 28

    def draw_events(self):
        """Draw event log."""
        events = self.civilization.get_recent_events(10)
        if not events:
            return

        # Panel background
        panel_w = 350
        panel_h = min(300, len(events) * 25 + 30)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        pygame.draw.rect(panel, (60, 60, 80, 200), panel.get_rect(), 2)

        # Title
        title = self.renderer.font_medium.render("EVENT LOG", True, YELLOW)
        panel.blit(title, (10, 5))

        # Events
        for i, event in enumerate(reversed(events)):
            color = WHITE
            if "collapse" in event.lower():
                color = BRIGHT_RED
            elif "knowledge" in event.lower() or "enlightenment" in event.lower():
                color = CYAN
            elif "stable" in event.lower():
                color = GREEN

            text = self.renderer.font_small.render(
                f"· {event[:50]}", True, color
            )
            panel.blit(text, (15, 35 + i * 25))

        self.screen.blit(panel, (self.renderer.width - panel_w - 10, 80))

    def draw_milestone_popup(self):
        """Draw milestone achieved popup."""
        if self.milestone_popup and self.milestone_popup_timer > 0:
            msg = self.milestones.unlocked_messages.get(self.milestone_popup, "")
            if not msg:
                return

            alpha = min(255, self.milestone_popup_timer * 5)
            if self.milestone_popup_timer < 30:
                alpha = self.milestone_popup_timer * 8

            surf = self.renderer.font_medium.render(msg, True, YELLOW)
            bg = pygame.Surface(
                (surf.get_width() + 40, surf.get_height() + 20), pygame.SRCALPHA
            )
            bg.fill((0, 0, 0, min(200, alpha)))
            bg.blit(surf, (20, 10))

            x = self.renderer.width // 2 - bg.get_width() // 2
            y = self.renderer.height - 100
            self.screen.blit(bg, (x, y))

    def update(self, dt):
        """Update game state."""
        dt = min(dt, 0.1)  # Cap dt to prevent physics explosion

        if not self.paused:
            # Update simulation
            sim_dt = dt * self.time_scale * 10  # Scale for visible motion
            self.simulation.step(sim_dt)

            # Update civilization
            stability = self.simulation.get_stability_metric()
            self.civilization.update(stability, sim_dt * 0.01)

            # Check milestones
            state = self.civilization.get_state()
            unlocked = self.milestones.check(state)
            if unlocked:
                self.milestone_popup = unlocked[0]
                self.milestone_popup_timer = 120

        # Update milestone popup timer
        if self.milestone_popup_timer > 0:
            self.milestone_popup_timer -= 1
            if self.milestone_popup_timer == 0:
                self.milestone_popup = None

        # Auto-pan for cinematic feel
        if not self.dragging and not self.paused:
            self.renderer.camera.target_offset += np.array([
                math.sin(self.frame_count * 0.001) * 0.2,
                math.cos(self.frame_count * 0.001) * 0.2,
            ])

        self.frame_count += 1

    def render(self):
        """Render current frame."""
        stability = self.simulation.get_stability_metric()
        state = self.civilization.get_state()

        self.renderer.render(
            self.simulation,
            state['era'],
            stability,
            state['population'],
            self.mode,
            self.time_scale,
            self.paused,
        )

        # Draw knowledge meter (left side)
        knowledge = state['knowledge']
        bar_h = 200
        bar_w = 15
        bar_x = 10
        bar_y = self.renderer.height // 2 - bar_h // 2

        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        know_h = int(knowledge / 100 * bar_h)
        # Gradient from blue to bright cyan
        know_color = (
            int(40 + 200 * knowledge / 100),
            int(120 + 135 * knowledge / 100),
            255
        )
        pygame.draw.rect(
            self.screen, know_color,
            (bar_x, bar_y + bar_h - know_h, bar_w, know_h)
        )
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1)

        # Knowledge label
        know_label = self.renderer.font_small.render(
            f"Know:", True, CYAN
        )
        self.screen.blit(know_label, (bar_x - 2, bar_y - 20))
        know_val = self.renderer.font_small.render(
            f"{knowledge:.0f}%", True, CYAN
        )
        self.screen.blit(know_val, (bar_x - 2, bar_y + bar_h + 5))

        # Help overlay
        if self.show_help:
            self.draw_help()

        # Events panel
        if self.show_events:
            self.draw_events()

        # Milestone popup
        self.draw_milestone_popup()

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_input()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()