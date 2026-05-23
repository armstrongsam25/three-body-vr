"""Achievements display screen for Three Body VR."""

import pygame
from src.constants import *


class AchievementsScreen:
    """Displays unlocked achievements and game stats."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.title_font = pygame.font.Font(None, 48)
        self.heading_font = pygame.font.Font(None, 32)
        self.body_font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.back_button = None

    def setup(self, milestones, stats):
        """Set up the achievements display."""
        self.milestones = milestones
        self.stats = stats
        cx = self.width // 2
        self.back_button = pygame.Rect(cx - 100, self.height - 60, 200, 40)

    def update(self, mouse_pos, mouse_click):
        """Check for back button click."""
        if self.back_button and self.back_button.collidepoint(mouse_pos) and mouse_click:
            return "back"
        return None

    def render(self, surface):
        """Render achievements screen."""
        # Background
        surface.fill(DARK_BLUE)
        for y in range(self.height):
            t = y / self.height
            color = (int(5 + 10 * t), int(5 + 5 * t), int(25 + 20 * t))
            pygame.draw.line(surface, color, (0, y), (self.width, y))

        # Title
        title = self.title_font.render("ACHIEVEMENTS & STATS", True, YELLOW)
        title_rect = title.get_rect(center=(self.width // 2, 40))
        surface.blit(title, title_rect)

        # Stats section
        stats_y = 100
        stats = [
            f"Games Played: {self.stats.get('games_played', 0)}",
            f"Best Knowledge: {self.stats.get('best_knowledge', 0):.0f}%",
            f"Total Collapses: {self.stats.get('total_collapses', 0)}",
            f"Scenarios Unlocked: {self.stats.get('scenarios_unlocked', 0)}/{self.stats.get('total_scenarios', 4)}",
        ]

        stats_title = self.heading_font.render("STATISTICS", True, CYAN)
        surface.blit(stats_title, (self.width // 2 - stats_title.get_width() // 2, stats_y))
        stats_y += 35

        for stat in stats:
            text = self.body_font.render(stat, True, WHITE)
            surface.blit(text, (self.width // 2 - 150, stats_y))
            stats_y += 28

        # Milestones section
        milestone_y = stats_y + 30
        milestone_title = self.heading_font.render("MILESTONES", True, CYAN)
        surface.blit(milestone_title,
                     (self.width // 2 - milestone_title.get_width() // 2, milestone_y))
        milestone_y += 40

        all_milestones = [
            ('first_cycle', 'First Cycle', 'Witness your first complete orbital cycle'),
            ('stable_era_100', 'Golden Century', 'Survive a Stable Era of 100+ cycles'),
            ('population_max', 'Peak Civilization', 'Reach maximum population capacity'),
            ('survive_10_collapses', 'Resilient', 'Survive 10 civilization collapses'),
            ('first_prediction', 'Prophet', 'Make your first orbital prediction'),
            ('predict_era_change', 'Oracle', 'Correctly predict an era change'),
            ('first_probe', 'First Launch', 'Launch your first space probe'),
            ('fleet_commander', 'Fleet Commander', 'Command 5 active probes simultaneously'),
            ('knowledge_50', 'Scholar', 'Achieve 50% understanding'),
            ('knowledge_100', 'Enlightenment', 'Achieve 100% understanding'),
        ]

        for key, name, desc in all_milestones:
            unlocked = self.milestones.get(key, False)
            color = GREEN if unlocked else DARK_GRAY
            icon = "✦" if unlocked else "◇"

            name_text = self.body_font.render(f"{icon} {name}", True, color)
            surface.blit(name_text, (self.width // 2 - 150, milestone_y))

            desc_text = self.small_font.render(desc, True, GRAY if unlocked else DARK_GRAY)
            surface.blit(desc_text, (self.width // 2 - 150, milestone_y + 22))

            milestone_y += 50

        # Back button
        btn_color = (60, 60, 100)
        hovered = self.back_button and self.back_button.collidepoint(pygame.mouse.get_pos())
        if hovered:
            btn_color = (80, 80, 140)

        pygame.draw.rect(surface, btn_color, self.back_button, border_radius=5)
        pygame.draw.rect(surface, YELLOW if hovered else (60, 60, 80),
                         self.back_button, 2, border_radius=5)
        back_text = self.body_font.render("BACK", True, WHITE)
        back_rect = back_text.get_rect(center=self.back_button.center)
        surface.blit(back_text, back_rect)