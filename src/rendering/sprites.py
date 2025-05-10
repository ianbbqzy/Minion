"""
Sprite management for the game
"""
import pygame
from src.utils.constants import WHITE, BLACK, TILE_COLORS, TILE_SIZE

class SpriteManager:
    def __init__(self, tile_size=TILE_SIZE):
        self.tile_size = tile_size
        self.sprites = {}
        self.tile_surfaces = {}
        self.initialize_sprites()
        
    def initialize_sprites(self):
        """Initialize all game sprites"""
        # Create minion sprites
        self.sprites["team1"] = self.create_minion_sprite(TILE_COLORS["team1"], self.tile_size)
        self.sprites["team2"] = self.create_minion_sprite(TILE_COLORS["team2"], self.tile_size)
        
        # Create item sprites
        self.sprites["sushi"] = self.create_item_sprite("🍣", self.tile_size)
        self.sprites["donut"] = self.create_item_sprite("🍩", self.tile_size)
        self.sprites["banana"] = self.create_item_sprite("🍌", self.tile_size)
        
        # Create tile surfaces for each type (0-5: empty, sushi, donut, banana, team1, team2)
        for i in range(6):
            self.tile_surfaces[i] = self.create_tile(i, self.tile_size)
    
    def create_minion_sprite(self, color, size):
        """Create a simple minion sprite with the given color"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw minion body (circle)
        pygame.draw.circle(surf, color, (size//2, size//2), size//3)
        
        # Draw eyes
        eye_offset = 8
        pygame.draw.circle(surf, WHITE, (size//2 - eye_offset, size//2 - 5), 5)
        pygame.draw.circle(surf, WHITE, (size//2 + eye_offset, size//2 - 5), 5)
        pygame.draw.circle(surf, BLACK, (size//2 - eye_offset, size//2 - 5), 2)
        pygame.draw.circle(surf, BLACK, (size//2 + eye_offset, size//2 - 5), 2)
        
        # Draw smile
        pygame.draw.arc(surf, BLACK, (size//3, size//2, size//3, size//4), 0, 3.14, 2)
        
        return surf
    
    def create_item_sprite(self, emoji, size):
        """Create a sprite for an item using emojis on a colored background"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Render the emoji text
        font = pygame.font.SysFont('Arial', size//2)
        text = font.render(emoji, True, WHITE)
        text_rect = text.get_rect(center=(size//2, size//2))
        
        # Add a circle background
        if emoji == "🍣":
            bg_color = (30, 144, 255, 150)  # Blue for sushi
        elif emoji == "🍩":
            bg_color = (139, 69, 19, 150)   # Brown for donut
        elif emoji == "🍌":
            bg_color = (238, 214, 175, 150) # Yellow for banana
        else:
            bg_color = (200, 200, 200, 150) # Default gray
            
        pygame.draw.circle(surf, bg_color, (size//2, size//2), size//3)
        
        # Add the emoji
        surf.blit(text, text_rect)
        
        return surf
    
    def create_tile(self, tile_type, size):
        """Create a colored tile with texture"""
        surf = pygame.Surface((size, size))
        
        if tile_type == 0:  # Empty (grass)
            color = TILE_COLORS["empty"]
        elif tile_type == 1:  # Sushi
            color = TILE_COLORS["sushi"]
        elif tile_type == 2:  # Donut
            color = TILE_COLORS["donut"]
        elif tile_type == 3:  # Banana
            color = TILE_COLORS["banana"]
        elif tile_type == 4:  # Team 1 Minion
            color = TILE_COLORS["team1"]
        elif tile_type == 5:  # Team 2 Minion
            color = TILE_COLORS["team2"]
        else:
            color = (200, 200, 200)  # Default gray
            
        surf.fill(color)
        
        # Add some texture to tiles
        import random
        for _ in range(10):
            # Add slightly different colored pixels for texture
            shade = random.randint(-20, 20)
            texture_color = tuple(min(255, max(0, c + shade)) for c in color)
            x = random.randint(0, size - 6)
            y = random.randint(0, size - 6)
            size_dots = random.randint(3, 6)
            pygame.draw.rect(surf, texture_color, (x, y, size_dots, size_dots))
        
        # Add grid lines
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, size, size), 1)
        
        return surf 
