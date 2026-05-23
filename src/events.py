"""Random event system for Three Body VR.

Catastrophic and beneficial events that spice up the game:
solar flares, gravitational spikes, syzygies, meteor showers, etc.
"""

import random
import math
import pygame
import numpy as np
from src.constants import *


class GameEvent:
    """A one-shot or recurring game event."""

    def __init__(self, event_type, source_pos=None, duration=60, intensity=1.0):
        self.event_type = event_type
        self.source_pos = source_pos
        self.duration = duration
        self.intensity = intensity
        self.elapsed = 0
        self.active = True
        self.effects_applied = False

    def update(self):
        """Advance event timer."""
        self.elapsed += 1
        if self.elapsed >= self.duration:
            self.active = False

    def progress(self):
        """0.0 to 1.0 progress."""
        return min(1.0, self.elapsed / self.duration)


class EventManager:
    """Manages random game events."""

    EVENT_TYPES = {
        'solar_flare': {
            'name': 'Solar Flare',
            'description': 'A massive solar flare erupts! The planet is bathed in radiation.',
            'population_effect': -15,
            'knowledge_effect': 2,
            'color': (255, 200, 50),
            'min_duration': 60,
            'max_duration': 120,
            'cooldown': 300,
        },
        'gravitational_spike': {
            'name': 'Gravitational Spike',
            'description': 'A sudden gravitational anomaly distorts the suns\' orbits.',
            'population_effect': -8,
            'knowledge_effect': 5,
            'color': (150, 100, 255),
            'min_duration': 40,
            'max_duration': 80,
            'cooldown': 250,
        },
        'syzygy': {
            'name': 'Syzygy',
            'description': 'The three suns align! The gravitational forces are at their peak.',
            'population_effect': 0,
            'knowledge_effect': 10,
            'color': (100, 255, 255),
            'min_duration': 30,
            'max_duration': 50,
            'cooldown': 400,
        },
        'meteor_shower': {
            'name': 'Meteor Shower',
            'description': 'A beautiful but deadly meteor shower rains down.',
            'population_effect': -5,
            'knowledge_effect': 3,
            'color': (200, 200, 255),
            'min_duration': 45,
            'max_duration': 90,
            'cooldown': 200,
        },
        'quantum_fluctuation': {
            'name': 'Quantum Fluctuation',
            'description': 'Reality warps momentarily. The suns flicker in and out of existence.',
            'population_effect': -20,
            'knowledge_effect': 15,
            'color': (255, 100, 255),
            'min_duration': 20,
            'max_duration': 40,
            'cooldown': 600,
        },
        'stable_resonance': {
            'name': 'Stable Resonance',
            'description': 'The suns briefly settle into a rare resonance pattern.',
            'population_effect': 10,
            'knowledge_effect': 8,
            'color': (100, 255, 100),
            'min_duration': 30,
            'max_duration': 60,
            'cooldown': 500,
        },
    }

    def __init__(self):
        self.active_events = []
        self.cooldowns = {}
        self.event_history = []
        self.base_chance = 0.001  # Per-frame chance of random event
        self.chaos_multiplier = 2.5  # More events during chaos

    def update(self, stability, dt, frame_count):
        """Update events and possibly spawn new ones."""
        triggered = []

        # Update active events
        for event in self.active_events[:]:
            event.update()
            if not event.effects_applied:
                triggered.append(event)
                event.effects_applied = True

        # Remove expired events
        self.active_events = [e for e in self.active_events if e.active]

        # Decrease cooldowns
        for key in list(self.cooldowns.keys()):
            self.cooldowns[key] -= dt
            if self.cooldowns[key] <= 0:
                del self.cooldowns[key]

        # Random event spawn
        chaos_bonus = (1.0 - stability) * self.chaos_multiplier + 1.0
        chance = self.base_chance * chaos_bonus * dt

        if random.random() < chance:
            # Pick a random event type that's not on cooldown
            available = [
                t for t in self.EVENT_TYPES
                if t not in self.cooldowns
            ]
            if available and len(self.active_events) < 3:
                event_type = random.choice(available)
                spec = self.EVENT_TYPES[event_type]
                duration = random.randint(spec['min_duration'], spec['max_duration'])

                # Intensity varies with stability
                intensity = 0.5 + (1.0 - stability) * 1.0

                # Source position (center of suns or random)
                source_pos = np.array([
                    random.uniform(-50, 50),
                    random.uniform(-50, 50),
                ])

                event = GameEvent(event_type, source_pos, duration, intensity)
                self.active_events.append(event)
                self.cooldowns[event_type] = spec['cooldown']
                self.event_history.append((event_type, frame_count))

        return triggered

    def apply_event_effects(self, event, civilization, renderer):
        """Apply an event's effects to civilization."""
        spec = self.EVENT_TYPES[event.event_type]
        pop_effect = spec['population_effect'] * event.intensity
        know_effect = spec['knowledge_effect'] * event.intensity

        civilization.population = max(0, civilization.population + pop_effect)
        civilization.events.append(f"EVENT: {spec['description']}")

        if know_effect > 0:
            civilization.add_knowledge(abs(know_effect))

        # Visual effects
        if renderer and event.source_pos is not None:
            pass  # Handled by render

        return pop_effect, know_effect

    def get_active_event_names(self):
        """Get list of active event names."""
        return [self.EVENT_TYPES[e.event_type]['name'] for e in self.active_events]

    def get_active_event_colors(self):
        """Get colors of active events for visual feedback."""
        return [self.EVENT_TYPES[e.event_type]['color'] for e in self.active_events]

    def draw(self, surface, camera, width, height):
        """Draw visual indicators for active events."""
        for event in self.active_events:
            spec = self.EVENT_TYPES[event.event_type]
            color = spec['color']
            progress = event.progress()

            # Pulsing overlay effect
            if event.event_type == 'solar_flare':
                # Screen-wide orange pulse
                alpha = int(40 * (1 - progress) * event.intensity)
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((*color[:3], alpha))
                surface.blit(overlay, (0, 0))

            elif event.event_type == 'gravitational_spike':
                # Expanding purple rings from center
                screen_center = np.array([width / 2, height / 2])
                max_radius = min(width, height) * 0.6
                radius = max_radius * progress
                alpha = int(100 * (1 - progress))
                pygame.draw.circle(
                    surface, (*color[:3], alpha),
                    (int(screen_center[0]), int(screen_center[1])),
                    int(radius), 2
                )

            elif event.event_type == 'quantum_fluctuation':
                # Random flickering pixels
                alpha = int(60 * (1 - progress) * event.intensity)
                for _ in range(20):
                    x = random.randint(0, width - 1)
                    y = random.randint(0, height - 1)
                    surface.set_at((x, y), (*color[:3], alpha))

            elif event.event_type == 'syzygy':
                # Bright white flash at center
                alpha = int(150 * (1 - progress) * event.intensity)
                pygame.draw.circle(
                    surface, (*color[:3], alpha),
                    (width // 2, height // 2),
                    int(50 * (1 - progress) + 5), 0
                )

            elif event.event_type == 'stable_resonance':
                # Gentle green pulses
                pulse = abs(math.sin(progress * math.pi * 3))
                alpha = int(30 * pulse)
                overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                overlay.fill((*color[:3], alpha))
                surface.blit(overlay, (0, 0))