import pygame
import random
import os

class TileMap:
    def __init__(self, width, height, tile_size):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.tiles = {}
        self.load_tiles()
        
        # Generate a more interesting tilemap layout
        self.generate_map()
        
    def load_tiles(self):
        """Load tile images or create placeholders if not available"""
        self.tile_images = {}
        tile_dir = os.path.join("assets", "images", "tiles")
        
        # Check if tile images exist
        if os.path.exists(os.path.join(tile_dir, "grass.png")):
            # Load real tile images
            self.tile_images["grass"] = pygame.image.load(os.path.join(tile_dir, "grass.png"))
            self.tile_images["dirt"] = pygame.image.load(os.path.join(tile_dir, "dirt.png"))
            self.tile_images["water"] = pygame.image.load(os.path.join(tile_dir, "water.png"))
            self.tile_images["path"] = pygame.image.load(os.path.join(tile_dir, "path.png"))
            self.tile_images["sand"] = pygame.image.load(os.path.join(tile_dir, "sand.png"))
        else:
            # Create placeholder tiles
            colors = {
                "grass": (34, 139, 34),    # Forest green
                "dirt": (139, 69, 19),     # Brown
                "water": (30, 144, 255),   # Blue
                "path": (210, 180, 140),   # Tan
                "sand": (238, 214, 175)    # Sandy
            }
            
            for tile_name, color in colors.items():
                surf = pygame.Surface((self.tile_size, self.tile_size))
                surf.fill(color)
                
                # Add some texture to tiles
                for _ in range(10):
                    # Add slightly different colored pixels for texture
                    shade = random.randint(-20, 20)
                    texture_color = tuple(min(255, max(0, c + shade)) for c in color)
                    x = random.randint(0, self.tile_size - 6)
                    y = random.randint(0, self.tile_size - 6)
                    size = random.randint(3, 6)
                    pygame.draw.rect(surf, texture_color, (x, y, size, size))
                
                # Add grid lines
                pygame.draw.rect(surf, (0, 0, 0), (0, 0, self.tile_size, self.tile_size), 1)
                
                self.tile_images[tile_name] = surf
    
    def generate_map(self):
        """Generate a random, natural-looking map with different biomes"""
        # Initialize with grass
        self.tilemap = [["grass" for _ in range(self.width)] for _ in range(self.height)]
        
        # Add some water (a small lake)
        lake_center_x = random.randint(2, self.width - 3)
        lake_center_y = random.randint(2, self.height - 3)
        lake_size = random.randint(1, 2)
        
        for y in range(max(0, lake_center_y - lake_size), min(self.height, lake_center_y + lake_size + 1)):
            for x in range(max(0, lake_center_x - lake_size), min(self.width, lake_center_x + lake_size + 1)):
                distance = abs(x - lake_center_x) + abs(y - lake_center_y)
                if distance <= lake_size:
                    self.tilemap[y][x] = "water"
                elif distance <= lake_size + 1:
                    self.tilemap[y][x] = "sand"  # Sand around water
        
        # Add a path
        path_start_x = random.randint(0, self.width - 1)
        path_start_y = 0
        self.tilemap[path_start_y][path_start_x] = "path"
        
        current_x, current_y = path_start_x, path_start_y
        
        # Create a winding path
        for _ in range(self.width + self.height):
            # Pick a random direction
            directions = []
            if current_x > 0:
                directions.append((-1, 0))
            if current_x < self.width - 1:
                directions.append((1, 0))
            if current_y < self.height - 1:
                directions.append((0, 1))
            
            if not directions:
                break
                
            dx, dy = random.choice(directions)
            current_x += dx
            current_y += dy
            
            # Make path tile
            if 0 <= current_x < self.width and 0 <= current_y < self.height:
                self.tilemap[current_y][current_x] = "path"
                
                # Add some dirt around paths sometimes
                if random.random() < 0.3:
                    for nx, ny in [(current_x+1, current_y), (current_x-1, current_y), 
                                  (current_x, current_y+1), (current_x, current_y-1)]:
                        if (0 <= nx < self.width and 0 <= ny < self.height and 
                            self.tilemap[ny][nx] == "grass"):
                            self.tilemap[ny][nx] = "dirt"
        
        # Add random dirt patches
        for _ in range(random.randint(2, 5)):
            dirt_x = random.randint(0, self.width - 1)
            dirt_y = random.randint(0, self.height - 1)
            
            if self.tilemap[dirt_y][dirt_x] == "grass":
                self.tilemap[dirt_y][dirt_x] = "dirt"
                
                # Expand dirt patch a bit
                for i in range(random.randint(1, 3)):
                    nx = min(max(0, dirt_x + random.randint(-1, 1)), self.width - 1)
                    ny = min(max(0, dirt_y + random.randint(-1, 1)), self.height - 1)
                    if self.tilemap[ny][nx] == "grass":
                        self.tilemap[ny][nx] = "dirt"
    
    def draw(self, screen):
        """Draw the tilemap on the screen"""
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.tilemap[y][x]
                screen.blit(self.tile_images[tile_type], (x * self.tile_size, y * self.tile_size)) 