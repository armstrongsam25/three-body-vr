#!/usr/bin/env python3
"""Three Body VR - Main entry point.

A game inspired by Liu Cixin's The Three Body Problem.
Enter the VR world of Trisolaris and attempt to solve the chaotic three-body problem.
"""

import sys
import math
import random
import pygame
import numpy as np

from src.constants import *
from src.nbody import (
    NBodySimulation, CelestialBody,
    create_three_body_system, create_planet,
)
from src.renderer import Renderer
from src.civilization import Civilization, MilestoneTracker
from src.audio import AudioEngine
from src.menu import Menu, PauseMenu
from src.lore import LoreEngine
from src.save_system import SaveSystem
from src.progression import ProgressionManager, DIFFICULTY_SETTINGS, SCENARIOS, Difficulty
from src.achievements import AchievementsScreen
from src.scenario_select import ScenarioSelectScreen
from src.effects import NebulaRenderer, ShockwaveEffect, ScreenShake, TransitionEffect
from src.prediction import PredictionOverlay, KnowledgeDiscovery
from src.starfield import Starfield, BloomRenderer


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
        self.fullscreen = False

        # Game states
        self.game_state = "menu"  # menu, scenario_select, playing, paused, help, achievements
        self.mode = MODE_OBSERVE
        self.time_scale = TIME_SCALE
        self.show_help = False
        self.show_events = False
        self.milestone_popup = None
        self.milestone_popup_timer = 0
        self.prev_era = ERA_STABLE

        # Menu
        self.menu = Menu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.menu.setup()
        self.pause_menu = PauseMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.scenario_screen = ScenarioSelectScreen(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Audio
        self.audio = AudioEngine()

        # Lore, Save, Progression, Achievements, Effects
        self.lore = LoreEngine()
        self.save_system = SaveSystem()
        self.progression = ProgressionManager()
        self.achievements_screen = None
        self.nebula = NebulaRenderer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.shockwaves = ShockwaveEffect()
        self.screenshake = ScreenShake()
        self.transition = TransitionEffect(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.prediction_overlay = PredictionOverlay()
        self.knowledge_discovery = KnowledgeDiscovery()
        self.starfield = Starfield(SCREEN_WIDTH, SCREEN_HEIGHT, 300)
        self.bloom = BloomRenderer()

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

        # Camera
        self.dragging = False
        self.drag_start = (0, 0)
        self.last_mouse = (0, 0)

        # Game state tracking
        self.frame_count = 0
        self.simulation_time = 0.0
        self.flash_message = None
        self.flash_timer = 0

    def start_game(self):
        """Initialize/reset game state for play."""
        scenario = self.progression.current_scenario
        self.simulation = create_three_body_system(scenario['config'])
        self.planet = create_planet(
            self.simulation,
            pos=scenario['planet_pos'],
            vel=scenario['planet_vel'],
            name="Trisolaris"
        )
        self.civilization = Civilization()
        self.progression.apply_difficulty(self.civilization)
        self.civilization.collapse_limit = self.progression.get_difficulty_effects(0.5, 0)[3] + 1  # +1 extra life
        self.milestones = MilestoneTracker()
        self.renderer.camera.offset = np.array([0.0, 0.0])
        self.renderer.camera.target_zoom = 1.0
        self.time_scale = 1.0
        self.game_state = "playing"
        self.paused = False
        self.simulation_time = 0.0
        self.prev_era = ERA_STABLE
        self.flash_message = None
        self.flash_timer = 0
        self._last_collapse = 0

        # Start music
        self.audio.start_music()

        # Fade in from black
        self.transition.start_fade_in(8)

        # Show difficulty
        diff_name = DIFFICULTY_SETTINGS[self.progression.current_difficulty]['name']
        self.show_flash(f"Difficulty: {diff_name}", 120)

    def show_flash(self, message, duration=120):
        """Show a flash message."""
        self.flash_message = message
        self.flash_timer = duration

    def handle_input(self):
        """Process keyboard and mouse input."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True

            elif event.type == pygame.KEYDOWN:
                if self.game_state == "menu":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.start_game()
                        self.audio.play('click')
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False

                elif self.game_state == "help":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_h:
                        self.game_state = "playing"
                        self.show_help = False

                elif self.game_state == "playing" or self.game_state == "paused":
                    if event.key == pygame.K_SPACE:
                        if self.game_state == "playing":
                            self.game_state = "paused"
                            self.pause_menu.setup()
                        else:
                            self.game_state = "playing"
                        self.audio.play('click')

                    elif event.key == pygame.K_e and self.game_state == "playing":
                        self.mode = MODE_PREDICT if self.mode == MODE_OBSERVE else MODE_OBSERVE
                        self.prediction_overlay.toggle()
                        if self.mode == MODE_PREDICT:
                            self.milestones.milestones['first_prediction'] = True
                            self.audio.play('predict')
                            self.show_flash("PREDICTION MODE - Click and drag to predict orbits", 90)
                        else:
                            self.show_flash("OBSERVATION MODE", 60)

                    elif event.key == pygame.K_r and self.game_state == "playing":
                        self.start_game()
                        self.audio.play('click')

                    elif event.key == pygame.K_h and self.game_state == "playing":
                        self.show_help = not self.show_help
                        self.game_state = "help" if self.show_help else "playing"

                    elif event.key == pygame.K_TAB and self.game_state == "playing":
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
                        # Recreate menus with new size
                        w, h = self.screen.get_size()
                        self.menu = Menu(w, h)
                        self.menu.setup()
                        self.pause_menu = PauseMenu(w, h)

                    elif event.key == pygame.K_ESCAPE:
                        if self.game_state == "paused":
                            self.game_state = "playing"
                        else:
                            self.game_state = "paused"
                            self.pause_menu.setup()

                    elif event.key == pygame.K_m:
                        enabled = self.audio.toggle_mute()
                        self.show_flash(
                            "Audio: ON" if enabled else "Audio: MUTED", 60
                        )

                    elif event.key == pygame.K_F5:
                        # Quick save
                        filename = self.save_system.save_game(
                            self.simulation, self.planet,
                            self.civilization, self.milestones
                        )
                        if filename:
                            self.show_flash(f"Game saved: {filename}", 90)
                        else:
                            self.show_flash("Save failed!", 60)

                    elif event.key == pygame.K_F9:
                        # Quick load
                        result = self.save_system.load_game(
                            NBodySimulation, Civilization, MilestoneTracker
                        )
                        if result:
                            self.simulation, self.planet, self.civilization, self.milestones, _ = result
                            self.show_flash("Game loaded!", 90)
                            self.renderer.camera.target_offset = self.planet.pos.copy()
                        else:
                            self.show_flash("No save found", 60)

                    elif event.key == pygame.K_0:
                        self.time_scale = 1.0
                        self.show_flash("Speed: 1x", 30)
                    elif event.key == pygame.K_1:
                        self.time_scale = 0.5
                        self.show_flash("Speed: 0.5x", 30)
                    elif event.key == pygame.K_2:
                        self.time_scale = 2.0
                        self.show_flash("Speed: 2x", 30)
                    elif event.key == pygame.K_5:
                        self.time_scale = 5.0
                        self.show_flash("Speed: 5x", 30)

                    elif event.key == pygame.K_c:
                        self.renderer.camera.target_offset = self.planet.pos.copy()
                        self.show_flash("Centered on Trisolaris", 30)

            elif event.type == pygame.MOUSEWHEEL and self.game_state == "playing":
                zoom_factor = 1.1 if event.y > 0 else 0.9
                self.renderer.camera.target_zoom *= zoom_factor
                self.renderer.camera.target_zoom = max(
                    0.1, min(5.0, self.renderer.camera.target_zoom)
                )

            elif event.type == pygame.VIDEORESIZE:
                self.renderer.width = event.w
                self.renderer.height = event.h
                self.renderer.camera.width = event.w
                self.renderer.camera.height = event.h

        # Continuous input (polling)
        if self.game_state == "playing":
            keys = pygame.key.get_pressed()

            pan_speed = 5
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.renderer.camera.pan(-pan_speed, 0)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.renderer.camera.pan(pan_speed, 0)
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.renderer.camera.pan(0, -pan_speed)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                self.renderer.camera.pan(0, pan_speed)

            if keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:
                self.renderer.camera.target_zoom = min(
                    5.0, self.renderer.camera.target_zoom * 1.02
                )
            if keys[pygame.K_MINUS]:
                self.renderer.camera.target_zoom = max(
                    0.1, self.renderer.camera.target_zoom * 0.98
                )

            if keys[pygame.K_LEFTBRACKET]:
                self.time_scale = max(MIN_TIME_SCALE, self.time_scale * 0.95)
            if keys[pygame.K_RIGHTBRACKET]:
                self.time_scale = min(MAX_TIME_SCALE, self.time_scale * 1.05)

            # Mouse drag pan (right click) or prediction (left click in predict mode)
            mouse = pygame.mouse.get_pressed()
            if self.mode == MODE_PREDICT and self.game_state == "playing":
                if mouse[0]:
                    # Convert screen to world coords
                    world_pos = self.renderer.camera.screen_to_world(mouse_pos)
                    self.prediction_overlay.add_point(world_pos)
                    self.dragging = False
                elif mouse[2]:  # Right click pans
                    if not self.dragging:
                        self.dragging = True
                        self.drag_start = mouse_pos
                    else:
                        dx = mouse_pos[0] - self.last_mouse[0]
                        dy = mouse_pos[1] - self.last_mouse[1]
                        self.renderer.camera.pan(-dx, -dy)
                else:
                    # Evaluate prediction when released
                    if self.prediction_overlay.current_prediction:
                        accuracy = self.prediction_overlay.commit_prediction(self.simulation)
                        if accuracy > 0:
                            self.civilization.add_knowledge(accuracy * 0.5)
                            hint = self.knowledge_discovery.get_hint(accuracy)
                            self.show_flash(f"Accuracy: {accuracy:.0f}% - {hint}", 120)
                    self.dragging = False
            else:
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

            self.last_mouse = mouse_pos

        # Menu handling
        if self.game_state == "menu":
            action = self.menu.update(mouse_pos, mouse_click, self.clock.get_time() / 1000.0)
            if action == "start":
                self.game_state = "scenario_select"
                self.scenario_screen.setup(self.progression)
            elif action == "help":
                self.show_help = True
                self.game_state = "help"
            elif action == "settings":
                self.game_state = "achievements"
                self.achievements_screen = AchievementsScreen(self.renderer.width, self.renderer.height)
                self.achievements_screen.setup(
                    self.milestones.milestones,
                    self.progression.get_stats_display()
                )
            elif action == "quit":
                self.running = False

        elif self.game_state == "scenario_select":
            action = self.scenario_screen.update(mouse_pos, mouse_click)
            if action == "start":
                self.progression.current_scenario = self.scenario_screen.selected_scenario
                self.progression.current_difficulty = self.scenario_screen.selected_difficulty
                self.start_game()
            elif action == "back":
                self.game_state = "menu"
                self.menu.setup()

        elif self.game_state == "achievements":
            if self.achievements_screen:
                action = self.achievements_screen.update(mouse_pos, mouse_click)
                if action == "back":
                    self.game_state = "menu"
                    self.menu.setup()

        elif self.game_state == "paused":
            action = self.pause_menu.update(mouse_pos, mouse_click)
            if action == "resume":
                self.game_state = "playing"
            elif action == "reset":
                self.start_game()
            elif action == "menu":
                self.game_state = "menu"
                self.menu.setup()
                self.audio.stop_music()
            elif action == "quit":
                self.running = False

    def update(self, dt):
        """Update game state."""
        dt = min(dt, 0.1)

        if self.game_state == "playing":
            # Update simulation
            sim_dt = dt * self.time_scale * 10
            self.simulation.step(sim_dt)
            self.simulation_time += sim_dt

            # Check for close encounters / collisions
            collisions = self.simulation.check_collisions()
            if collisions:
                for i, j, dist in collisions:
                    b1 = self.simulation.bodies[i]
                    b2 = self.simulation.bodies[j]
                    if b1.is_sun and b2.is_sun:
                        self.civilization.events.append(
                            f"{b1.name} and {b2.name} nearly collided! Gravitational chaos intensifies."
                        )
                        self.renderer.particle_system.emit(
                            (b1.pos + b2.pos) / 2, count=20,
                            color=(255, 220, 80), speed=5.0, lifetime=60
                        )
                        self.shockwaves.emit(
                            (b1.pos + b2.pos) / 2,
                            color=(255, 220, 80), max_radius=200, duration=45
                        )
                        self.screenshake.trigger(5, 15)

            # Planet temperature
            planet_idx = len(self.simulation.bodies) - 1
            sun_count = self.simulation.is_planet_between_suns(planet_idx)
            temp = self.simulation.get_planet_temperature(planet_idx)

            # Update civilization
            stability = self.simulation.get_stability_metric()
            prev_era = self.civilization.current_era
            
            # Temperature affects civilization
            if temp > 100:
                self.civilization.population -= 0.05 * sim_dt * 0.01
            elif temp < -100:
                self.civilization.population -= 0.03 * sim_dt * 0.01
                
            # Get difficulty-modified rates
            growth, death, knowledge_gain, collapse_limit = \
                self.progression.get_difficulty_effects(stability, sim_dt * 0.01)
            
            # Override civ growth/death rates with difficulty settings
            self.civilization.knowledge_rate = knowledge_gain
            
            self.civilization.update(stability, sim_dt * 0.01)

            # Era transition effects
            if self.civilization.current_era != prev_era:
                self.audio.play('era_transition')
                if self.civilization.current_era == ERA_CHAOTIC:
                    self.show_flash("⚠ CHAOTIC ERA BEGINS ⚠", 120)
                elif self.civilization.current_era == ERA_STABLE:
                    self.show_flash("✦ STABLE ERA BEGINS ✦", 120)
            else:
                # Ambient sound
                if int(self.simulation_time) % 5 == 0:
                    self.audio.play_era_ambient(self.civilization.current_era)

            # Collapse sound
            state = self.civilization.get_state()
            if state['collapse_count'] > 0:
                # Only play on new collapse
                if not hasattr(self, '_last_collapse'):
                    self._last_collapse = 0
                if state['collapse_count'] > self._last_collapse:
                    self.audio.play('collapse')
                    self.shockwaves.emit(self.planet.pos, color=(255, 100, 50), max_radius=500, duration=90)
                    self.screenshake.trigger(15, 30)
                    self._last_collapse = state['collapse_count']

            # Update lore engine
            self.lore.update(sim_dt, self.civilization.current_era, stability, state['knowledge'])

            # Check for game over
            if self.civilization.game_over:
                self.progression.on_game_end(state['knowledge'], state['collapse_count'])
                self.show_flash("GAME OVER - Civilization Lost", 300)
                self.game_state = "paused"
                self.pause_menu.setup()
                self.audio.play('collapse')

            # Check milestones
            unlocked = self.milestones.check(state)
            if unlocked:
                self.milestone_popup = unlocked[0]
                self.milestone_popup_timer = 180
                self.audio.play('milestone')
                self.civilization.add_knowledge(5)
                self.shockwaves.emit(
                    self.planet.pos, color=(100, 255, 200), max_radius=350, duration=80
                )
                # Add milestone narrative
                narrative = self.lore.get_milestone_narrative(unlocked[0])
                if narrative:
                    self.civilization.events.append(narrative)

            # Auto-pan for cinematic feel
            if not self.dragging:
                self.renderer.camera.target_offset += np.array([
                    math.sin(self.frame_count * 0.001) * 0.2,
                    math.cos(self.frame_count * 0.001) * 0.2,
                ])

        # Update flash message
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.flash_message = None

        # Update milestone popup
        if self.milestone_popup_timer > 0:
            self.milestone_popup_timer -= 1
            if self.milestone_popup_timer == 0:
                self.milestone_popup = None

        # Update effects
        self.shockwaves.update()
        self.screenshake.update()
        self.transition.update()

        # Auto-evaluate prediction if in prediction mode
        if self.mode == MODE_PREDICT:
            result = self.prediction_overlay.update(self.simulation, self.frame_count)
            if result is not None and result > 0:
                self.civilization.add_knowledge(result * 0.3)

        self.frame_count += 1

    def draw_help(self):
        """Draw help overlay."""
        overlay = pygame.Surface(
            (self.renderer.width, self.renderer.height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        lines = [
            ("THREE BODY VR - CONTROLS", True, YELLOW),
            ("", False, None),
            ("Space        Pause / Resume", False, WHITE),
            ("E            Toggle Prediction Mode", False, WHITE),
            ("R            Reset Simulation", False, WHITE),
            ("C            Center on Trisolaris", False, WHITE),
            ("H            Toggle Help", False, WHITE),
            ("Tab          Toggle Event Log", False, WHITE),
            ("M            Mute/Unmute Audio", False, WHITE),
            ("F5           Quick Save", False, WHITE),
            ("F9           Quick Load", False, WHITE),
            ("F            Fullscreen", False, WHITE),
            ("0,1,2,5       Set Time Speed", False, WHITE),
            ("[/]          Adjust Time Scale", False, WHITE),
            ("+/-           Zoom In / Out", False, WHITE),
            ("Arrow Keys    Pan View", False, WHITE),
            ("Mouse Drag    Pan View", False, WHITE),
            ("Mouse Wheel   Zoom", False, WHITE),
            ("Esc           Menu / Quit", False, WHITE),
            ("", False, None),
            ("", False, None),
            ("THE STORY", True, YELLOW),
            ("", False, None),
            ("You have entered the VR world of Trisolaris,", False, CYAN),
            ("a planet orbiting three chaotic suns.", False, CYAN),
            ("Civilizations rise during Stable Eras and fall", False, CYAN),
            ("during Chaotic Eras when the suns' paths", False, CYAN),
            ("become unpredictable.", False, CYAN),
            ("", False, None),
            ("Your goal: observe the orbital patterns,", False, CYAN),
            ("predict era changes, and help Trisolaran", False, CYAN),
            ("civilization survive by gaining understanding", False, CYAN),
            ("of the three-body problem.", False, CYAN),
            ("", False, None),
            ("Press H or Esc to return", False, GRAY),
        ]

        y = 40
        for text, is_title, color in lines:
            if text == "":
                y += 10 if not is_title else 15
                continue
            if is_title:
                surf = self.renderer.font_large.render(text, True, color)
            else:
                surf = self.renderer.font_small.render(text, True, color)

            x = self.renderer.width // 2 - surf.get_width() // 2
            self.screen.blit(surf, (x, y))
            y += 26

    def draw_events_panel(self):
        """Draw event log panel."""
        events = self.civilization.get_recent_events(12)
        if not events:
            return

        panel_w = 380
        panel_h = min(320, len(events) * 25 + 40)
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        pygame.draw.rect(panel, (60, 60, 80, 200), panel.get_rect(), 2)

        # Title
        title = self.renderer.font_medium.render("EVENT LOG", True, YELLOW)
        panel.blit(title, (10, 8))

        for i, event in enumerate(reversed(events)):
            color = WHITE
            if "collapse" in event.lower():
                color = BRIGHT_RED
            elif "knowledge" in event.lower() or "enlightenment" in event.lower():
                color = CYAN
            elif "stable" in event.lower() or "golden" in event.lower():
                color = GREEN
            elif "catastrophe" in event.lower():
                color = ORANGE

            text = self.renderer.font_small.render(
                f"· {event[:55]}", True, color
            )
            panel.blit(text, (15, 40 + i * 25))

        self.screen.blit(panel, (self.renderer.width - panel_w - 10, 80))

    def draw_milestone_popup(self):
        """Draw milestone achieved popup."""
        if self.milestone_popup and self.milestone_popup_timer > 0:
            msg = self.milestones.unlocked_messages.get(self.milestone_popup, "")
            if not msg:
                return

            # Fade in/out
            if self.milestone_popup_timer > 150:
                alpha = int(255 * (180 - self.milestone_popup_timer) / 30)
            elif self.milestone_popup_timer < 30:
                alpha = int(255 * self.milestone_popup_timer / 30)
            else:
                alpha = 255
            alpha = max(0, min(255, alpha))

            # Glow effect
            title_text = "✦ MILESTONE ACHIEVED ✦"
            title_surf = self.renderer.font_medium.render(title_text, True, YELLOW)
            msg_surf = self.renderer.font_small.render(msg, True, WHITE)

            total_w = max(title_surf.get_width(), msg_surf.get_width()) + 60
            total_h = title_surf.get_height() + msg_surf.get_height() + 40

            bg = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
            bg.fill((0, 0, 0, min(220, alpha)))

            # Golden border
            border_color = (255, 220, 50, alpha)
            pygame.draw.rect(bg, border_color, bg.get_rect(), 2)

            bg.blit(title_surf, (total_w // 2 - title_surf.get_width() // 2, 15))
            bg.blit(msg_surf, (total_w // 2 - msg_surf.get_width() // 2, 15 + title_surf.get_height() + 5))

            x = self.renderer.width // 2 - total_w // 2
            y = self.renderer.height - 140
            self.screen.blit(bg, (x, y))

    def draw_flash_message(self):
        """Draw centered flash message."""
        if not self.flash_message or self.flash_timer <= 0:
            return

        alpha = min(255, self.flash_timer * 5)
        if self.flash_timer < 20:
            alpha = self.flash_timer * 12

        font_size = 36
        flash_font = pygame.font.Font(None, font_size)
        surf = flash_font.render(self.flash_message, True, YELLOW)
        bg = pygame.Surface(
            (surf.get_width() + 30, surf.get_height() + 15), pygame.SRCALPHA
        )
        bg.fill((0, 0, 0, min(180, alpha)))
        bg.blit(surf, (15, 7))

        x = self.renderer.width // 2 - bg.get_width() // 2
        y = self.renderer.height // 2 + 120
        self.screen.blit(bg, (x, y))

    def render(self):
        """Render current frame."""
        if self.game_state == "menu":
            self.menu.render(self.screen, self.clock.get_time() / 1000.0)
            pygame.display.flip()
            return

        if self.game_state == "scenario_select":
            self.scenario_screen.render(self.screen)
            pygame.display.flip()
            return

        if self.game_state == "achievements":
            if self.achievements_screen:
                self.achievements_screen.render(self.screen)
            pygame.display.flip()
            return

        if self.game_state == "help":
            self.renderer.draw_background(0.5)
            self.draw_help()
            pygame.display.flip()
            return

        # Playing or paused
        stability = self.simulation.get_stability_metric()
        state = self.civilization.get_state()

        # Calculate planet temperature
        planet_idx = len(self.simulation.bodies) - 1
        temp = self.simulation.get_planet_temperature(planet_idx)

        # Draw starfield (behind everything)
        self.starfield.update(
            camera_dx=self.renderer.camera.offset[0] * 0.01,
            camera_dy=self.renderer.camera.offset[1] * 0.01
        )
        self.starfield.draw(self.screen)

        # Draw nebula background
        self.nebula.draw(self.screen, camera_offset=self.renderer.camera.offset)

        self.renderer.render(
            self.simulation,
            state['era'],
            stability,
            state['population'],
            self.mode,
            self.time_scale,
            self.game_state == "paused",
        )

        # Draw shockwaves (after simulation render, on top)
        self.shockwaves.draw(self.screen, self.renderer.camera)

        # Draw prediction overlay
        if self.mode == MODE_PREDICT:
            self.prediction_overlay.draw(self.screen, self.renderer.camera)

        # Apply screenshake offset
        shake = self.screenshake.get_offset()
        if shake[0] != 0 or shake[1] != 0:
            # We already rendered, so we'd need to offset the final surface
            # Simple approach: draw a shift
            pass  # Screenshake handled via camera offset for now

        # Temperature display
        temp_color = CYAN if -20 < temp < 40 else (ORANGE if temp > 40 else BLUE)
        temp_label = self.renderer.font_small.render(
            f"Temp: {temp:.0f}°C", True, temp_color
        )
        self.screen.blit(temp_label, (10, 35))

        # Knowledge meter
        knowledge = state['knowledge']
        bar_h = 200
        bar_w = 15
        bar_x = 10
        bar_y = self.renderer.height // 2 - bar_h // 2

        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h))
        know_h = int(knowledge / 100 * bar_h)
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

        know_label = self.renderer.font_small.render("Know:", True, CYAN)
        self.screen.blit(know_label, (bar_x - 2, bar_y - 20))
        know_val = self.renderer.font_small.render(f"{knowledge:.0f}%", True, CYAN)
        self.screen.blit(know_val, (bar_x - 2, bar_y + bar_h + 5))

        # Events panel
        if self.show_events:
            self.draw_events_panel()

        # Lore quote
        quote = self.lore.get_active_quote()
        self.renderer.draw_quote(quote)

        # Flash message
        self.draw_flash_message()

        # Milestone popup
        self.draw_milestone_popup()

        # Pause menu overlay
        if self.game_state == "paused":
            self.pause_menu.render(self.screen)

        # Transition effect (fade in/out)
        self.transition.draw(self.screen)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_input()
            self.update(dt)
            self.render()

        self.audio.stop_music()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()