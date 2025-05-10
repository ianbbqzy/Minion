"""
Sprite management for the game
"""
import pygame
import os
from src.utils.constants import WHITE, BLACK, TILE_COLORS, TILE_SIZE

class SpriteManager:
    def __init__(self, tile_size=TILE_SIZE):
        self.tile_size = tile_size
        self.sprites = {}
        self.tile_surfaces = {}
        self.initialize_sprites()
        
    def initialize_sprites(self):
        """Initialize all game sprites"""
        # Try to load sprites from files first
        self.load_sprites_from_files()
        
        # Create tile surfaces for each type (0-5: empty, sushi, donut, banana, team1, team2)
        for i in range(6):
            self.tile_surfaces[i] = self.create_tile(i, self.tile_size)
    
    def load_sprites_from_files(self):
        """Load sprite images from files in the assets/tiles folder"""
        # Define the tiles directory path
        tiles_dir = os.path.join("assets", "tiles")
        
        # Ensure the directory exists
        os.makedirs(tiles_dir, exist_ok=True)
        
        # Always use these exact paths for minion sprites
        minions_dir = os.path.join("assets", "minions", "img")
        team1_path = os.path.join(minions_dir, "green_still.png")
        team2_path = os.path.join(minions_dir, "purple_still.png")
        
        # Load team 1 minion sprite
        if os.path.exists(team1_path):
            self.sprites["team1_minion_1"] = self.load_and_scale_image(team1_path)
            self.sprites["team1_minion_2"] = self.create_minion_sprite(TILE_COLORS["team1_minion_2"], self.tile_size)
            print(f"Loaded team1 minion from {team1_path}")
        else:
            # Fallback to generated sprite with warning
            print(f"Warning: {team1_path} not found, using generated sprite")
            self.sprites["team1_minion_1"] = self.create_minion_sprite(TILE_COLORS["team1_minion_1"], self.tile_size)
        
            # Load team 2 minion sprite
            self.sprites["team1_minion_2"] = self.create_minion_sprite(TILE_COLORS["team1_minion_2"], self.tile_size)
            
        if os.path.exists(team2_path):
            self.sprites["team2_minion_1"] = self.load_and_scale_image(team2_path)
            self.sprites["team2_minion_2"] = self.create_minion_sprite(TILE_COLORS["team2_minion_2"], self.tile_size)
            print(f"Loaded team2 minion from {team2_path}")
        else:
            # Fallback to generated sprite with warning
            print(f"Warning: {team2_path} not found, using generated sprite")
            self.sprites["team2_minion_1"] = self.create_minion_sprite(TILE_COLORS["team2_minion_1"], self.tile_size)
            self.sprites["team2_minion_2"] = self.create_minion_sprite(TILE_COLORS["team2_minion_2"], self.tile_size)
        
        # Load item sprites
        item_paths = {
            "empty": os.path.join(tiles_dir, "empty.png"),
            "sushi": os.path.join(tiles_dir, "sushi.png"),
            "donut": os.path.join(tiles_dir, "donut.png"),
            "banana": os.path.join(tiles_dir, "banana.png")
        }
        
        # Load each item sprite
        for item_name, path in item_paths.items():
            if os.path.exists(path):
                self.sprites[item_name] = self.load_and_scale_image(path)
                print(f"Loaded {item_name} from {path}")
            else:
                print(f"Warning: {path} not found, using generated sprite")
                if item_name == "empty":
                    # Create an empty grass tile
                    self.sprites[item_name] = self.create_empty_tile(self.tile_size)
                else:
                    # Create item sprites with emoji
                    emoji_map = {"sushi": "🍣", "donut": "🍩", "banana": "🍌"}
                    self.sprites[item_name] = self.create_item_sprite(emoji_map.get(item_name, "❓"), self.tile_size)
    
    def load_and_scale_image(self, path):
        """Load an image and scale it to tile size"""
        try:
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, (self.tile_size, self.tile_size))
        except pygame.error as e:
            print(f"Error loading image {path}: {e}")
            # Return a pink error surface
            surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            surf.fill((255, 0, 255, 180))
            return surf
    
    def create_empty_tile(self, size):
        """Create an empty tile (grass)"""
        surf = pygame.Surface((size, size))
        surf.fill(TILE_COLORS["empty"])
        
        # Add some texture
        import random
        for _ in range(10):
            shade = random.randint(-20, 20)
            color = TILE_COLORS["empty"]
            texture_color = tuple(min(255, max(0, c + shade)) for c in color)
            x = random.randint(0, size - 6)
            y = random.randint(0, size - 6)
            size_dots = random.randint(3, 6)
            pygame.draw.rect(surf, texture_color, (x, y, size_dots, size_dots))
        
        # Add grid line
        pygame.draw.rect(surf, (0, 0, 0), (0, 0, size, size), 1)
        
        return surf
    
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
        """Create a colored tile with texture or use loaded sprite"""
        # Map tile types to sprite names
        type_to_name = {
            0: "empty",
            1: "sushi",
            2: "donut",
            3: "banana",
            4: "team1_minion_1",
            5: "team1_minion_2",
            6: "team2_minion_1",
            7: "team2_minion_2"
        }
        
        # If it's an item tile (1-3) and we have the sprite, return a transparent surface
        # The item will be drawn separately in board renderer
        if tile_type in [1, 2, 3]:
            # For item tiles, we just need the empty tile
            if "empty" in self.sprites:
                return self.sprites["empty"]
        
        # For empty tile (type 0), use the empty sprite if available
        if tile_type == 0 and "empty" in self.sprites:
            return self.sprites["empty"]
            
        # Fallback to colored tiles if sprite not found
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
            color = TILE_COLORS["team1_minion_1"]
        elif tile_type == 5:  # Team 1 Minion
            color = TILE_COLORS["team1_minion_2"]
        elif tile_type == 6:  # Team 2 Minion
            color = TILE_COLORS["team2_minion_1"]
        elif tile_type == 7:  # Team 2 Minion
            color = TILE_COLORS["team2_minion_2"]
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
