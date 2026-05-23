"""Tech tree and civilization upgrade system.

Players spend accumulated knowledge to unlock permanent upgrades
that improve civilization resilience, fleet capabilities, and game mechanics.
"""

import pygame
from src.constants import *


class TechNode:
    """A technology or upgrade node."""

    def __init__(self, tech_id, name, description, cost, prerequisite=None,
                 effects=None, icon_char="◆"):
        self.tech_id = tech_id
        self.name = name
        self.description = description
        self.cost = cost
        self.prerequisite = prerequisite
        self.effects = effects or {}
        self.icon_char = icon_char
        self.researched = False
        self.active = True  # Whether the node can be researched

    def can_research(self, knowledge, researched_ids):
        """Check if this tech can be researched."""
        if self.researched:
            return False, "Already researched"
        if not self.active:
            return False, "Not available"
        if knowledge < self.cost:
            return False, f"Need {self.cost} knowledge (have {knowledge:.0f})"
        if self.prerequisite and self.prerequisite not in researched_ids:
            return False, f"Requires prerequisite technology"
        return True, "Available"

    def apply_effects(self, civilization, fleet, progression):
        """Apply the tech effects to the game state."""
        result_messages = []

        for effect_key, effect_value in self.effects.items():
            if effect_key == 'max_population':
                civilization.max_population += effect_value
                result_messages.append(f"Max population +{effect_value}")

            elif effect_key == 'population_growth':
                # Modifies difficulty growth rate (handled elsewhere)
                result_messages.append(f"Population growth +{effect_value * 100:.0f}%")

            elif effect_key == 'knowledge_rate':
                civilization.knowledge_rate += effect_value
                result_messages.append(f"Knowledge rate +{effect_value * 100:.0f}%")

            elif effect_key == 'collapse_resistance':
                civilization.collapse_limit += effect_value
                result_messages.append(f"+{effect_value} extra collapse(s) allowed")

            elif effect_key == 'probe_cost_reduction':
                fleet.population_cost_factor *= (1.0 - effect_value)
                result_messages.append(f"Probe costs -{effect_value * 100:.0f}%")

            elif effect_key == 'probe_speed':
                for ptype, spec in fleet.SpaceProbe.PROBE_TYPES.items():
                    # Increase speed of all probe types
                    pass  # Handled by override
                result_messages.append(f"Probe speed +{effect_value * 100:.0f}%")

            elif effect_key == 'event_resistance':
                # Reduces negative event effects
                result_messages.append(f"Event damage -{effect_value * 100:.0f}%")

            elif effect_key == 'unlock_probe':
                fleet.available_types.append(effect_value)
                result_messages.append(f"Unlocked {effect_value} probes")

        return result_messages


# Complete tech tree
TECH_TREE = [
    TechNode(
        'adaptive_architecture', 'Adaptive Architecture',
        'Buildings that withstand the chaos of era transitions.',
        cost=15,
        effects={'max_population': 20},
        icon_char="🏗",
    ),
    TechNode(
        'agricultural_science', 'Agricultural Science',
        'Better food production during stable eras.',
        cost=10,
        effects={'population_growth': 0.15},
        icon_char="🌱",
    ),
    TechNode(
        'orbital_mathematics', 'Orbital Mathematics',
        'Advanced Kepler-derived math for predicting sun movements.',
        cost=20,
        prerequisite='agricultural_science',
        effects={'knowledge_rate': 0.02},
        icon_char="📐",
    ),
    TechNode(
        'deep_bunkers', 'Deep Bunkers',
        'Underground shelters protect population during chaos.',
        cost=25,
        prerequisite='adaptive_architecture',
        effects={'collapse_resistance': 1},
        icon_char="🏰",
    ),
    TechNode(
        'advanced_propulsion', 'Advanced Propulsion',
        'Faster, more efficient probe engines.',
        cost=30,
        prerequisite='orbital_mathematics',
        effects={'probe_speed': 0.3},
        icon_char="🚀",
    ),
    TechNode(
        'mass_production', 'Mass Production',
        'Cheaper probe construction through standardization.',
        cost=20,
        prerequisite='advanced_propulsion',
        effects={'probe_cost_reduction': 0.4},
        icon_char="🏭",
    ),
    TechNode(
        'gravitational_shielding', 'Gravitational Shielding',
        'Protect the planet from extreme gravitational events.',
        cost=40,
        prerequisite='deep_bunkers',
        effects={'event_resistance': 0.35},
        icon_char="🛡",
    ),
    TechNode(
        'sophon_network', 'Sophon Network',
        'Deploy quantum-entangled sophons to monitor the suns.',
        cost=50,
        prerequisite='advanced_propulsion',
        effects={'knowledge_rate': 0.04},
        icon_char="🔮",
    ),
    TechNode(
        'stellar_engineering', 'Stellar Engineering',
        'Limited ability to influence the orbits of the suns.',
        cost=80,
        prerequisite='sophon_network',
        effects={'event_resistance': 0.5, 'population_growth': 0.2},
        icon_char="⭐",
    ),
    TechNode(
        'three_body_solution', 'Three-Body Solution',
        'The ultimate understanding. The chaos is no more.',
        cost=100,
        prerequisite='stellar_engineering',
        effects={'collapse_resistance': 99, 'knowledge_rate': 0.1, 'max_population': 100},
        icon_char="🌌",
    ),
]


class TechTreeDisplay:
    """Renders the tech tree screen for research."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.title_font = pygame.font.Font(None, 40)
        self.body_font = pygame.font.Font(None, 22)
        self.small_font = pygame.font.Font(None, 16)
        self.scroll_offset = 0
        self.max_scroll = 0
        self.node_rects = []
        self.back_button = None
        self.hovered_node = None
        self.status_message = ""

    def setup(self, tech_nodes, knowledge, researched_ids):
        """Set up the display with current tech state."""
        self.node_rects = []
        y = 120 + self.scroll_offset
        x_start = self.width // 2 - 200

        for node in tech_nodes:
            can, reason = node.can_research(knowledge, researched_ids)

            rect = pygame.Rect(x_start, y, 400, 65)
            self.node_rects.append({
                'rect': rect,
                'node': node,
                'can_research': can,
                'reason': reason,
            })

            y += 75

        self.max_scroll = max(0, y - self.height + 200)
        self.back_button = pygame.Rect(
            self.width // 2 - 80, self.height - 50, 160, 35
        )

    def update(self, mouse_pos, mouse_click, mouse_wheel):
        """Handle input."""
        self.hovered_node = None

        # Scroll
        if mouse_wheel:
            self.scroll_offset = max(
                -self.max_scroll,
                min(0, self.scroll_offset + mouse_wheel * 30)
            )

        # Check back button
        if self.back_button and self.back_button.collidepoint(mouse_pos) and mouse_click:
            return "back"

        # Check node buttons
        for node_info in self.node_rects:
            node_info['rect'].y = node_info.get('_original_y', node_info['rect'].y)
            if node_info['rect'].collidepoint(mouse_pos):
                self.hovered_node = node_info
                if mouse_click and node_info['can_research']:
                    return ('research', node_info['node'])

        return None

    def render(self, surface):
        """Render the tech tree screen."""
        # Background
        surface.fill(DARK_BLUE)
        for y in range(self.height):
            t = y / self.height
            color = (int(5 + 10 * t), int(5 + 5 * t), int(25 + 20 * t))
            pygame.draw.line(surface, color, (0, y), (self.width, y))

        # Title
        title = self.title_font.render("RESEARCH LABORATORY", True, YELLOW)
        title_rect = title.get_rect(center=(self.width // 2, 35))
        surface.blit(title, title_rect)

        sub = self.small_font.render(
            "Spend knowledge to unlock civilization technologies", True, GRAY
        )
        sub_rect = sub.get_rect(center=(self.width // 2, 70))
        surface.blit(sub, sub_rect)

        # Status message
        if self.status_message:
            status = self.body_font.render(self.status_message, True, GREEN)
            surface.blit(status, (self.width // 2 - status.get_width() // 2, 90))

        # Tech nodes
        mouse_pos = pygame.mouse.get_pos()

        for node_info in self.node_rects:
            rect = node_info['rect'].copy()
            node = node_info['node']
            can = node_info['can_research']
            hovered = rect.collidepoint(mouse_pos)

            # Adjust y for scrolling
            rect.y = node_info.get('_original_y', rect.y) + self.scroll_offset
            node_info['_original_y'] = node_info.get('_original_y', rect.y - self.scroll_offset)

            # Skip off-screen
            if rect.bottom < 100 or rect.top > self.height:
                continue

            # Colors
            if node.researched:
                bg_color = (20, 60, 20) if not hovered else (30, 80, 30)
                border = GREEN
                name_color = GREEN
            elif can:
                bg_color = (30, 40, 70) if not hovered else (50, 60, 100)
                border = CYAN
                name_color = CYAN
            else:
                bg_color = (25, 25, 45) if not hovered else (35, 35, 60)
                border = (50, 50, 70)
                name_color = GRAY

            pygame.draw.rect(surface, bg_color, rect, border_radius=4)
            pygame.draw.rect(surface, border, rect, 2, border_radius=4)

            # Icon and name
            icon = self.body_font.render(node.icon_char, True, name_color)
            surface.blit(icon, (rect.x + 12, rect.y + 8))

            name = self.body_font.render(node.name, True, name_color)
            surface.blit(name, (rect.x + 35, rect.y + 8))

            # Description
            desc = self.small_font.render(node.description, True, WHITE if can or node.researched else DARK_GRAY)
            surface.blit(desc, (rect.x + 35, rect.y + 30))

            # Cost or status
            if node.researched:
                status = self.small_font.render("✓ Researched", True, GREEN)
            elif can:
                status = self.small_font.render(f"Cost: {node.cost} knowledge", True, YELLOW)
            else:
                status = self.small_font.render(node_info['reason'], True, RED)

            surface.blit(status, (rect.right - status.get_width() - 15, rect.y + 8))

            # Prerequisite indicator
            if node.prerequisite and not node.researched:
                prereq = self.small_font.render(f"Req: {node.prerequisite}", True, ORANGE)
                surface.blit(prereq, (rect.right - prereq.get_width() - 15, rect.y + 30))

            # Show effects on hover
            if hovered and node.effects and not node.researched:
                tooltip_y = rect.bottom + 5
                for effect_key, effect_value in node.effects.items():
                    eff_name = effect_key.replace('_', ' ').title()
                    if isinstance(effect_value, float) and effect_value < 1:
                        eff_text = f"+{effect_value * 100:.0f}% {eff_name}"
                    else:
                        eff_text = f"+{effect_value} {eff_name}"
                    eff = self.small_font.render(eff_text, True, LIGHT_GRAY)
                    surface.blit(eff, (rect.x + 20, tooltip_y))
                    tooltip_y += 16

        # Back button
        btn_color = (60, 60, 100)
        if self.back_button and self.back_button.collidepoint(mouse_pos):
            btn_color = (80, 80, 140)

        pygame.draw.rect(surface, btn_color, self.back_button, border_radius=5)
        pygame.draw.rect(surface, YELLOW if self.back_button.collidepoint(mouse_pos) else (60, 60, 80),
                         self.back_button, 2, border_radius=5)
        back_text = self.body_font.render("BACK", True, WHITE)
        back_rect = back_text.get_rect(center=self.back_button.center)
        surface.blit(back_text, back_rect)


class TechManager:
    """Manages the tech tree and research state."""

    def __init__(self):
        self.tech_nodes = {t.tech_id: t for t in TECH_TREE}
        self.researched = set()
        self.total_spent = 0

    def get_available_techs(self, knowledge):
        """Get list of techs sorted by tier."""
        available = []
        for node in TECH_TREE:
            can, _ = node.can_research(knowledge, self.researched)
            if can or node.tech_id in self.researched:
                available.append(node)
        return available

    def research(self, tech_id, knowledge, civilization, fleet, progression):
        """Attempt to research a technology."""
        if tech_id not in self.tech_nodes:
            return False, "Unknown technology"

        node = self.tech_nodes[tech_id]
        can, reason = node.can_research(knowledge, self.researched)
        if not can:
            return False, reason

        # Deduct knowledge
        civilization.knowledge -= node.cost
        node.researched = True
        self.researched.add(tech_id)
        self.total_spent += node.cost

        # Apply effects
        messages = node.apply_effects(civilization, fleet, progression)

        return True, f"Researched {node.name}! " + ", ".join(messages)

    def get_researched_count(self):
        return len(self.researched)

    def get_total_count(self):
        return len(self.tech_nodes)

    def save_state(self):
        return {
            'researched': list(self.researched),
            'total_spent': self.total_spent,
        }

    def load_state(self, data):
        self.researched = set(data.get('researched', []))
        self.total_spent = data.get('total_spent', 0)
        for tech_id in self.researched:
            if tech_id in self.tech_nodes:
                self.tech_nodes[tech_id].researched = True