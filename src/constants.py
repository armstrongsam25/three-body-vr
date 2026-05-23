"""Game constants and configuration."""

# Display
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
TITLE = "Three Body VR - Trisolaris"

# Colors
BLACK = (0, 0, 0)
DARK_BLUE = (5, 5, 25)
SPACE_BLUE = (10, 10, 40)
WHITE = (255, 255, 255)
YELLOW = (255, 220, 50)
ORANGE = (255, 150, 30)
RED = (255, 60, 40)
BLUE = (40, 120, 255)
CYAN = (0, 220, 255)
GREEN = (50, 255, 100)
PURPLE = (180, 50, 255)
GRAY = (120, 120, 130)
DARK_GRAY = (40, 40, 50)
BRIGHT_RED = (255, 0, 0)

# Physics
G = 6.67430e-1  # Scaled gravitational constant for game feel
SOFTENING = 5.0  # Softening factor to prevent infinite forces
TIME_SCALE = 1.0  # Base time scale
MAX_TIME_SCALE = 20.0
MIN_TIME_SCALE = 0.1

# Orbits
ORBIT_TRAIL_LENGTH = 2000
ORBIT_POINTS_DENSITY = 4  # Points per frame to sample

# VR Overlay
OVERLAY_ALPHA = 25  # Scanline overlay alpha
SCANLINE_SPACING = 3
VR_VIGNETTE_STRENGTH = 0.4

# Civilization
CIV_MAX_POPULATION = 100.0
CIV_GROWTH_RATE = 0.1
CIV_DEATH_RATE_CHAOTIC = 0.3
CIV_DEATH_RATE_STABLE = 0.01
POPULATION_THRESHOLD = 10.0  # Below this, civilization collapse risk

# Suns
SUN_RADIUS = 18
SUN_MASS = 100.0
PLANET_RADIUS = 8
PLANET_MASS = 1.0

# Game modes
MODE_OBSERVE = "observe"
MODE_PREDICT = "predict"
MODE_MENU = "menu"

# Eras
ERA_STABLE = "stable"
ERA_CHAOTIC = "chaotic"
ERA_TRANSITION = "transition"