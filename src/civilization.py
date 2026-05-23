"""Civilization management system for the Three Body VR game."""

import random
from src.constants import *


class Civilization:
    """Represents the Trisolaran civilization trying to survive the chaos."""

    def __init__(self):
        self.population = CIV_MAX_POPULATION / 2
        self.max_population = CIV_MAX_POPULATION
        self.cycles_survived = 0
        self.total_cycles = 0
        self.current_era = ERA_STABLE
        self.era_duration = 0
        self.era_timer = 0
        self.era_history = []  # Record of eras
        self.knowledge = 0.0  # Understanding of the three-body problem (0-100)
        self.knowledge_rate = 0.05  # Knowledge gained per cycle in stable era
        self.buildings = 0
        self.collapse_count = 0
        
        # Narrative events
        self.events = []
        self.event_cooldown = 0

    def update(self, stability, dt):
        """Update civilization state based on stability."""
        self.total_cycles += dt
        
        # Determine era
        if stability > 0.6:
            new_era = ERA_STABLE
        elif stability > 0.3:
            new_era = ERA_TRANSITION
        else:
            new_era = ERA_CHAOTIC

        if new_era != self.current_era:
            self.era_history.append((self.current_era, self.era_duration))
            self.current_era = new_era
            self.era_duration = 0
            self.era_timer = random.uniform(20, 80)  # Random era length

        self.era_duration += dt

        # Population dynamics
        sun_count = 3  # Always 3 suns in three-body problem
        if self.current_era == ERA_STABLE:
            growth = CIV_GROWTH_RATE * sun_count * dt
            death = CIV_DEATH_RATE_STABLE * self.population * dt
            knowledge_gain = self.knowledge_rate * dt * (1 + self.knowledge / 50)
        elif self.current_era == ERA_TRANSITION:
            growth = CIV_GROWTH_RATE * 0.5 * dt
            death = CIV_DEATH_RATE_CHAOTIC * 0.3 * self.population * dt
            knowledge_gain = self.knowledge_rate * 0.5 * dt
        else:  # Chaotic
            growth = 0
            death = CIV_DEATH_RATE_CHAOTIC * self.population * dt
            knowledge_gain = 0

            # Random catastrophic events in chaotic eras
            if random.random() < 0.005 * dt:
                severity = random.uniform(0.1, 0.3)
                self.population *= (1 - severity)
                self.events.append(f"Catastrophe! Lost {severity:.0%} of population")

        self.population = max(0, min(self.max_population,
                                     self.population + growth - death))
        self.knowledge = min(100, self.knowledge + knowledge_gain)

        # Collapse check
        if self.population < POPULATION_THRESHOLD:
            if self.collapse_count < 3:
                self.population = CIV_MAX_POPULATION * 0.3  # Rebound
                self.collapse_count += 1
                self.events.append(f"Civilization collapsed! Rebooting... (collapse #{self.collapse_count})")
            else:
                self.population = 0
                self.events.append("Final collapse. Civilization lost.")

        # Event cooldown
        if self.event_cooldown > 0:
            self.event_cooldown -= dt

    def get_state(self):
        """Return civilization state summary."""
        return {
            'population': self.population,
            'era': self.current_era,
            'era_duration': self.era_duration,
            'knowledge': self.knowledge,
            'cycles_survived': self.cycles_survived,
            'total_cycles': self.total_cycles,
            'collapse_count': self.collapse_count,
            'buildings': self.buildings,
        }

    def add_knowledge(self, amount):
        """Award knowledge points (e.g., from player discoveries)."""
        self.knowledge = min(100, self.knowledge + amount)
        if amount > 0:
            self.events.append(f"Gained {amount:.1f} knowledge about the three-body problem!")

    def get_recent_events(self, count=5):
        """Get recent narrative events."""
        return self.events[-count:]


class MilestoneTracker:
    """Tracks player achievements and milestones."""

    def __init__(self):
        self.milestones = {
            'first_cycle': False,
            'stable_era_100': False,
            'population_max': False,
            'survive_10_collapses': False,
            'knowledge_50': False,
            'knowledge_100': False,
            'first_prediction': False,
            'predict_era_change': False,
        }
        self.unlocked_messages = {
            'first_cycle': "You've witnessed your first orbital cycle. The dance of the three suns is mesmerizing.",
            'stable_era_100': "A Stable Era lasting 100 cycles! The Trisolarans remember this as a golden age.",
            'population_max': "Civilization at peak population! The cities sprawl across the planet.",
            'survive_10_collapses': "Ten collapses survived. The Trisolarans have become resilient.",
            'knowledge_50': "You begin to understand the pattern beneath the chaos...",
            'knowledge_100': "ENLIGHTENMENT: You have solved the three-body problem!",
            'first_prediction': "You've made your first prediction. The path ahead shimmers with possibility.",
            'predict_era_change': "You correctly predicted an era change! Your understanding grows.",
        }

    def check(self, civ_state):
        """Check and unlock milestones."""
        unlocked = []
        if not self.milestones['first_cycle'] and civ_state['total_cycles'] >= 1:
            self.milestones['first_cycle'] = True
            unlocked.append('first_cycle')
        if not self.milestones['stable_era_100'] and civ_state['era_duration'] >= 100:
            self.milestones['stable_era_100'] = True
            unlocked.append('stable_era_100')
        if not self.milestones['population_max'] and civ_state['population'] >= CIV_MAX_POPULATION:
            self.milestones['population_max'] = True
            unlocked.append('population_max')
        if not self.milestones['survive_10_collapses'] and civ_state['collapse_count'] >= 10:
            self.milestones['survive_10_collapses'] = True
            unlocked.append('survive_10_collapses')
        if not self.milestones['knowledge_50'] and civ_state['knowledge'] >= 50:
            self.milestones['knowledge_50'] = True
            unlocked.append('knowledge_50')
        if not self.milestones['knowledge_100'] and civ_state['knowledge'] >= 100:
            self.milestones['knowledge_100'] = True
            unlocked.append('knowledge_100')
        return unlocked