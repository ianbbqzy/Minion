"""
Game constants used throughout the application
"""

# Screen dimensions
SCREEN_WIDTH = 1700
SCREEN_HEIGHT = 1000

# Game grid settings
TILE_SIZE = 80
GRID_WIDTH = 10
GRID_HEIGHT = 8

# Webcam settings
WEBCAM_WIDTH = 400
WEBCAM_HEIGHT = 225

# Game mechanics
MAX_TURNS = 50

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_BLUE = (173, 216, 230)
YELLOW = (255, 255, 0)
SPEECH_BG = (50, 50, 50, 180)  # Semi-transparent dark gray
BUTTON_COLOR = (70, 130, 180)  # Steel blue
BUTTON_HOVER_COLOR = (100, 160, 210)  # Lighter blue for hover

# Background gradient colors
GRADIENT_COLORS = [
    (204, 255, 204),  # Pastel Green
    (230, 255, 204),  # Very light pastel green
    (255, 255, 204),  # Pastel Yellow
    (255, 250, 230)   # Pale cream / off-white
]

# Tile colors
TILE_COLORS = {
    "empty": (34, 139, 34),    # Forest green (grass)
    "sushi": (30, 144, 255),   # Blue
    "donut": (139, 69, 19),    # Brown
    "banana": (238, 214, 175), # Sandy/Yellow
    "team1": (255, 100, 100),  # Red-ish
    "team2": (100, 100, 255)   # Blue-ish
}

# Item codes
EMPTY = 0
SUSHI = 1
DONUT = 2
BANANA = 3
TEAM1_MINION = 4
TEAM2_MINION = 5

# UI Settings
PREVIEW_GAP = 8  # Vertical spacing between UI blocks
DIALOGUE_DISPLAY_TIME = 3000  # 3 seconds 