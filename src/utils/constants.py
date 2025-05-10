"""
Game constants used throughout the application
"""

# Screen dimensions
SCREEN_WIDTH = 1750
SCREEN_HEIGHT = 1000

# Game grid settings
TILE_SIZE = 80
GRID_WIDTH = 10
GRID_HEIGHT = 8

# Webcam settings
WEBCAM_WIDTH = 320
WEBCAM_HEIGHT = 180

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
    "team1_minion_1": (255, 100, 100),  # Red-ish
    "team1_minion_2": (100, 100, 255),  # Blue-ish
    "team2_minion_1": (255, 255, 0),  # Yellow-ish
    "team2_minion_2": (0, 255, 0)   # Green-ish
}

# Item codes
EMPTY = 0
SUSHI = 1
DONUT = 2
BANANA = 3
TEAM1_MINION_1 = 4
TEAM1_MINION_2 = 5
TEAM2_MINION_1 = 6
TEAM2_MINION_2 = 7

# UI Settings
PREVIEW_GAP = 8  # Vertical spacing between UI blocks
DIALOGUE_DISPLAY_TIME = 3000  # 3 seconds 

MINIONS_PER_TEAM = 2

TEAM1_MINION_1_INSTRUCTIONS = [
    "You are strong. Your objective is to predict where the enemy goes next and clash with them to eat them up.",
]

TEAM1_MINION_2_INSTRUCTIONS = [
    "Don't ever stay, if instructions are not clear, you should go for something random",
    "if the player acts suprised, you should go for banana",
    "if the player acts happy, you should go for sushi",
    "if the player acts sad, you should go for donut",
]

TEAM2_MINION_1_INSTRUCTIONS = [
    "You are strong. Your objective is to predict where the enemy goes next and clash with them to eat them up.",
]

TEAM2_MINION_2_INSTRUCTIONS = [
    "if the player gestures thumbs up, you should go for banana",
    "if the player gestures thumbs down, you should go for sushi",
    "if the player make a finger heart, you should go for donut",
]

TEAM1_MINION_1_POWER = 2
TEAM1_MINION_2_POWER = 98
TEAM2_MINION_1_POWER = 40
TEAM2_MINION_2_POWER = 60