"""Narrative lore system with quotes and events from The Three Body Problem."""

import random


# Collection of lore fragments, quotes, and narrative events
QUOTES = [
    "The universe is a dark forest. Every civilization is a silent hunter.",
    "To effectively contain a civilization, that civilization must not know that it is being contained.",
    "In the face of the three suns, all life is fragile.",
    "A Stable Era is when the planet orbits just one sun. But how long will it last?",
    "The Trisolarans learned to dehydrate and wait. Perhaps we should too.",
    "Three bodies in motion can never be predicted with certainty.",
    "The sophons have arrived. They watch everything.",
    "Do not answer. Do not answer. Do not answer.",
    "You are bugs, they said. And bugs never truly win. But bugs are never truly defeated either.",
    "Every era ends. Every civilization falls. But some rise again.",
    "The Chaotic Eras are not random — they only appear so to us.",
    "We are like ants watching a hurricane. We see the chaos but not the pattern.",
    "Civilization is a brief flicker between two long darknesses.",
    "The droplet — perfect in form, terrifying in purpose.",
    "To a Trisolaran, a Stable Era is a miracle. To us, it's just Tuesday.",
    "The wallfacers knew: to keep a secret from an enemy who can read minds, you must first hide it from yourself.",
    "Space is not empty. It is watching.",
    "If you destroy a civilization, you destroy a universe.",
    "The speed of light: perhaps it was once faster. Perhaps someone slowed it down.",
    "We are small. The universe is vast. And the three-body problem has no solution.",
]

ERA_EVENTS = {
    "stable": [
        "The suns align in a rare configuration. Trisolaris basks in warmth.",
        "A golden age begins. The Trisolarans build great cities.",
        "The stars are calm. Civilization flourishes.",
        "For now, the orbits are predictable. The Trisolarans know peace.",
        "This Stable Era may last generations. Or it may end tomorrow.",
        "The libraries fill with knowledge. The Trisolarans study the heavens.",
    ],
    "transition": [
        "The suns wobble. A subtle shift in their dance.",
        "The elders sense change coming. The signs are there.",
        "A second sun draws near. The temperature begins to rise.",
        "The astronomers watch nervously. Their models show instability.",
        "The beautiful pattern is breaking down. Chaos approaches.",
        "Between stability and chaos, there is a moment of terrible beauty.",
    ],
    "chaotic": [
        "The three suns rage across the sky. No pattern can be found.",
        "All three suns burn at once! The surface becomes uninhabitable.",
        "The Trisolarans dehydrate, waiting for the next Stable Era.",
        "Civilization shudders. The suns are unpredictable today.",
        "In the chaotic dance, there is a terrifying beauty.",
        "The planet swings wildly between the three gravitational wells.",
        "No two cycles are the same. The chaos is complete.",
    ],
}

MILESTONE_NARRATIVES = {
    "first_cycle": "You witness your first complete orbital cycle. The pattern is not yet clear, but you sense there is something beneath the chaos.",
    "stable_era_100": "100 cycles of stability! The Trisolaran historians will call this the Golden Century. The libraries overflow with knowledge and art.",
    "population_max": "The planet teems with life. Cities span the continents. For this brief moment, Trisolaran civilization is at its zenith.",
    "survive_10_collapses": "Ten civilizations have risen and fallen on this world. Each left something behind. The Trisolarans have learned resilience beyond measure.",
    "knowledge_50": "You begin to see patterns in the chaos. The three suns are not random — their movements follow laws. Perhaps the three-body problem IS solvable...",
    "knowledge_100": "ENLIGHTENMENT. You have glimpsed the underlying order of the three-body system. The Trisolarans now have a chance to predict, to prepare, to survive.",
    "first_prediction": "Your first prediction. The shimmering line of possibility stretches into the future. If you can see it, perhaps you can navigate it.",
    "predict_era_change": "You predicted an era change before it happened! This is the power that could save a civilization — or doom another.",
}


class LoreEngine:
    """Manages narrative events, quotes, and storytelling."""

    def __init__(self):
        self.shown_quotes = set()
        self.quote_cooldown = 0
        self.current_quote = None
        self.quote_timer = 0

        # Track narrative state
        self.total_cycles = 0
        self.last_narrative_event = ""
        self.narrative_history = []

    def get_random_quote(self):
        """Get a random quote not recently shown."""
        available = [q for q in QUOTES if q not in self.shown_quotes]
        if not available:
            self.shown_quotes.clear()
            available = QUOTES

        quote = random.choice(available)
        self.shown_quotes.add(quote)
        return quote

    def get_era_event(self, era):
        """Get a random narrative event for the current era."""
        events = ERA_EVENTS.get(era, ERA_EVENTS["transition"])
        return random.choice(events)

    def get_milestone_narrative(self, milestone_key):
        """Get narrative text for a milestone."""
        return MILESTONE_NARRATIVES.get(milestone_key, "")

    def update(self, dt, era, stability, knowledge):
        """Update lore engine, potentially showing quotes."""
        self.total_cycles += dt

        if self.quote_cooldown > 0:
            self.quote_cooldown -= dt

        # Show quotes periodically
        if self.quote_cooldown <= 0 and random.random() < 0.002 * dt:
            self.current_quote = self.get_random_quote()
            self.quote_timer = 300  # Display for ~5 seconds
            self.quote_cooldown = 500  # Wait before next quote

        if self.quote_timer > 0:
            self.quote_timer -= 1

    def add_narrative_event(self, event):
        """Record a narrative event."""
        self.narrative_history.append(event)
        self.last_narrative_event = event

    def get_active_quote(self):
        """Get current quote text or None."""
        if self.quote_timer > 0 and self.current_quote:
            return self.current_quote
        return None