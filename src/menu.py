"""Menu system for Three Body VR."""

import math
import pygame
from src.constants import *


class MenuItem:
    """A single menu item."""

    def __init__(self, text, action, color=WHITE, hover_color=YELLOW):
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        self.rect = None

    def render(self, surface, font, x, y):
        """Render this menu item."""
        color = self.hover_color if self.hovered else self.color
        text_surf = font.render(self.text, True, color)
        self.rect = text_surf.get_rect(center=(x, y))

        # Draw selection indicator
        if self.hovered:
            indicator = "▸ "
            indicator_surf = font.render(indicator + self.text, True, color)
            self.rect = indicator_surf.get_rect(center=(x, y))
        else:
            indicator_surf = text_surf
            self.rect = text_surf.get_rect(center=(x, y))

        surface.blit(indicator_surf, self.rect)


class Button:
    """A clickable button."""

    def __init__(self, text, x, y, width, height, action, font_size=24):
        self.text = text
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.action = action
        self.hovered = False
        self.clicked = False
        self.font = pygame.font.Font(None, font_size)
        self.alpha = 255

    def update(self, mouse_pos, mouse_click):
        """Update hover/click state."""
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and mouse_click:
            self.clicked = True
            return True
        return False

    def render(self, surface):
        """Render button."""
        # Background
        color = (60, 60, 100) if self.hovered else (30, 30, 50)
        border_color = YELLOW if self.hovered else (60, 60, 80)

        # Glow on hover
        if self.hovered:
            glow = pygame.Surface(
                (self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA
            )
            for r in range(15, 0, -2):
                alpha = max(0, 30 - r * 2)
                pygame.draw.rect(
                    glow, (255, 220, 50, alpha),
                    glow.get_rect().inflate(-r * 2, -r * 2),
                    border_radius=5
                )
            surface.blit(glow, (self.rect.x - 10, self.rect.y - 10))

        # Button body
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=5)

        # Text
        text_surf = self.font.render(self.text, True, WHITE if not self.hovered else YELLOW)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class Menu:
    """Main menu screen."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buttons = []
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 22)
        self.title_glow_offset = 0
        self.star_field = self._generate_stars()
        self.particles = []

    def _generate_stars(self, count=150):
        """Generate random star positions."""
        import random
        stars = []
        for _ in range(count):
            stars.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'brightness': random.randint(60, 255),
                'twinkle_speed': random.uniform(0.01, 0.05),
                'twinkle_offset': random.uniform(0, math.pi * 2),
            })
        return stars

    def setup(self):
        """Create menu buttons."""
        self.buttons = []
        btn_w = 250
        btn_h = 50
        cx = self.width // 2
        start_y = self.height // 2

        buttons = [
            ("START SIMULATION", "start", start_y),
            ("HOW TO PLAY", "help", start_y + 65),
            ("SETTINGS", "settings", start_y + 130),
            ("QUIT", "quit", start_y + 195),
        ]

        for text, action, y in buttons:
            self.buttons.append(Button(text, cx, y, btn_w, btn_h, action))

    def update(self, mouse_pos, mouse_click, dt):
        """Update menu state."""
        for btn in self.buttons:
            if btn.update(mouse_pos, mouse_click):
                return btn.action

        # Update title glow
        self.title_glow_offset += dt * 2

        # Update twinkling stars
        for star in self.star_field:
            star['twinkle_offset'] += star['twinkle_speed']

        # Background particles
        import random
        if random.random() < 0.1:
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': self.height + 10,
                'speed': random.uniform(0.3, 1.5),
                'size': random.randint(1, 3),
                'alpha': random.randint(100, 255),
            })

        alive = []
        for p in self.particles:
            p['y'] -= p['speed']
            p['alpha'] -= 1
            if p['alpha'] > 0 and p['y'] > -10:
                alive.append(p)
        self.particles = alive

        return None

    def render(self, surface, dt):
        """Render menu screen."""
        # Background
        surface.fill(DARK_BLUE)

        # Gradient
        for y in range(self.height):
            t = y / self.height
            color = (
                int(5 + 10 * t),
                int(5 + 5 * t),
                int(25 + 20 * t),
            )
            pygame.draw.line(surface, color, (0, y), (self.width, y))

        # Twinkling stars
        for star in self.star_field:
            brightness = star['brightness'] + int(
                20 * math.sin(star['twinkle_offset'])
            )
            brightness = max(40, min(255, brightness))
            color = (brightness, brightness, brightness)
            pygame.draw.circle(
                surface, color,
                (star['x'], star['y']), 1
            )

        # Floating particles
        for p in self.particles:
            alpha = min(255, p['alpha'])
            color = (100, 150, 255, alpha)
            pygame.draw.circle(
                surface, color[:3],
                (int(p['x']), int(p['y'])), p['size']
            )

        # Title
        title_y = self.height // 3
        glow_intensity = 30 + int(10 * math.sin(self.title_glow_offset))

        # Title glow effect
        for offset in range(3, 0, -1):
            alpha = glow_intensity // (offset + 1)
            glow_color = (255, 220, 50, alpha)
            glow_surf = self.title_font.render("THREE BODY VR", True, glow_color[:3])
            glow_rect = glow_surf.get_rect(
                center=(self.width // 2, title_y)
            )
            surface.blit(glow_surf, glow_rect.inflate(offset * 4, offset * 4))

        title_surf = self.title_font.render("THREE BODY VR", True, YELLOW)
        title_rect = title_surf.get_rect(center=(self.width // 2, title_y))
        surface.blit(title_surf, title_rect)

        # Subtitle
        sub_text = "Trisolaris awaits..."
        sub_surf = self.subtitle_font.render(sub_text, True, CYAN)
        sub_rect = sub_surf.get_rect(center=(self.width // 2, title_y + 50))
        surface.blit(sub_surf, sub_rect)

        # Decorative three-body diagram
        diagram_y = title_y - 80
        for i in range(3):
            angle = i * 2 * math.pi / 3 + self.title_glow_offset * 0.3
            r = 60
            sx = self.width // 2 + math.cos(angle) * r
            sy = diagram_y + math.sin(angle) * r
            colors = [(255, 200, 60), (255, 140, 40), (255, 100, 50)]
            pygame.draw.circle(surface, colors[i], (int(sx), int(sy)), 8)

            # Orbital lines
            for j in range(3):
                if j != i:
                    angle_j = j * 2 * math.pi / 3 + self.title_glow_offset * 0.3
                    ex = self.width // 2 + math.cos(angle_j) * r
                    ey = diagram_y + math.sin(angle_j) * r
                    pygame.draw.line(
                        surface, (255, 200, 100, 30),
                        (int(sx), int(sy)), (int(ex), int(ey)), 1
                    )

        # Subtitle 2
        sub2 = self.small_font.render(
            "Enter the virtual world. Solve the impossible.", True, GRAY
        )
        sub2_rect = sub2.get_rect(center=(self.width // 2, title_y + 80))
        surface.blit(sub2, sub2_rect)

        # Buttons
        for btn in self.buttons:
            btn.render(surface)

        # Version
        ver = self.small_font.render("v0.1 · Cixin Liu's Three-Body Problem", True, DARK_GRAY)
        surface.blit(ver, (10, self.height - 25))


class PauseMenu:
    """In-game pause menu."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.buttons = []

    def setup(self):
        self.buttons = []
        cx = self.width // 2
        cy = self.height // 2
        buttons = [
            ("RESUME", "resume", cy - 60),
            ("RESET", "reset", cy),
            ("MAIN MENU", "menu", cy + 60),
            ("QUIT", "quit", cy + 120),
        ]
        for text, action, y in buttons:
            self.buttons.append(Button(text, cx, y, 200, 45, action, 28))

    def update(self, mouse_pos, mouse_click):
        for btn in self.buttons:
            if btn.update(mouse_pos, mouse_click):
                return btn.action
        return None

    def render(self, surface):
        # Dim overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Title
        font = pygame.font.Font(None, 48)
        title = font.render("PAUSED", True, WHITE)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 120))
        surface.blit(title, title_rect)

        for btn in self.buttons:
            btn.render(surface)