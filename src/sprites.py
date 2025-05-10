import pygame
import random
import os
from typing import Dict, List, Tuple, Union

class Minion(pygame.sprite.Sprite):
    def __init__(self, grid_x: int, grid_y: int, tile_size: int) -> None:
        super().__init__()
        self.grid_x: int = grid_x
        self.grid_y: int = grid_y
        self.tile_size: int = tile_size
        
        # Direction: (dx, dy) where each value is -1, 0, or 1
        self.direction: Tuple[int, int] = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        
        # Movement timer
        self.move_timer: int = 0
        self.move_interval: int = 2000  # 2 seconds in milliseconds
        
        # Animation frames
        self.load_sprites()
        self.current_frame: int = 0
        self.animation_speed: float = 0.2  # Frames per update
        self.animation_timer: float = 0
        
        # After load_sprites is called
        self.direction_name: str = self.get_direction_name()
        self.image: pygame.Surface = self.sprites[self.direction_name][0]
        
    def load_sprites(self) -> None:
        # Load spritesheet for each direction
        # We'll check if the sprites exist, otherwise use placeholder graphics
        self.sprites: Dict[str, List[pygame.Surface]] = {
            "up": [],
            "down": [],
            "left": [],
            "right": []
        }
        
        sprite_dir: str = os.path.join("assets", "images", "minions")
        if os.path.exists(os.path.join(sprite_dir, "minion_down_1.png")):
            # Load real sprites if they exist
            for i in range(1, 5):  # 4 frames per direction
                self.sprites["down"].append(pygame.image.load(os.path.join(sprite_dir, f"minion_down_{i}.png")))
                self.sprites["up"].append(pygame.image.load(os.path.join(sprite_dir, f"minion_up_{i}.png")))
                self.sprites["right"].append(pygame.image.load(os.path.join(sprite_dir, f"minion_right_{i}.png")))
                self.sprites["left"].append(pygame.image.load(os.path.join(sprite_dir, f"minion_left_{i}.png")))
        else:
            # Create placeholder colored rectangles
            colors: List[Tuple[int, int, int]] = [(random.randint(200, 255), random.randint(200, 255), 0) for _ in range(4)]
            
            for i in range(4):
                # Create surface for each direction and frame
                for direction in ["up", "down", "left", "right"]:
                    surf: pygame.Surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                    
                    # Draw minion body
                    pygame.draw.circle(surf, colors[i], 
                                     (self.tile_size // 2, self.tile_size // 2), 
                                     self.tile_size // 3)
                    
                    # Draw direction indicator
                    if direction == "up":
                        pygame.draw.polygon(surf, (255, 0, 0), 
                                         [(self.tile_size // 2, self.tile_size // 4), 
                                          (self.tile_size // 3, self.tile_size // 2),
                                          (self.tile_size * 2 // 3, self.tile_size // 2)])
                    elif direction == "down":
                        pygame.draw.polygon(surf, (255, 0, 0), 
                                         [(self.tile_size // 2, self.tile_size * 3 // 4), 
                                          (self.tile_size // 3, self.tile_size // 2),
                                          (self.tile_size * 2 // 3, self.tile_size // 2)])
                    elif direction == "left":
                        pygame.draw.polygon(surf, (255, 0, 0), 
                                         [(self.tile_size // 4, self.tile_size // 2), 
                                          (self.tile_size // 2, self.tile_size // 3),
                                          (self.tile_size // 2, self.tile_size * 2 // 3)])
                    elif direction == "right":
                        pygame.draw.polygon(surf, (255, 0, 0), 
                                         [(self.tile_size * 3 // 4, self.tile_size // 2), 
                                          (self.tile_size // 2, self.tile_size // 3),
                                          (self.tile_size // 2, self.tile_size * 2 // 3)])
                    
                    # Add slight animation offset based on frame number
                    offset: int = (i * 2) % 8 - 4
                    if direction in ["left", "right"]:
                        # Draw eyes with slight y-offset for animation
                        eye_y: int = self.tile_size // 2 - 5 + offset
                        eye_x_offset: int = 8
                        pygame.draw.circle(surf, (255, 255, 255), 
                                         (self.tile_size // 2 - eye_x_offset, eye_y), 5)
                        pygame.draw.circle(surf, (255, 255, 255), 
                                         (self.tile_size // 2 + eye_x_offset, eye_y), 5)
                        pygame.draw.circle(surf, (0, 0, 0), 
                                         (self.tile_size // 2 - eye_x_offset, eye_y), 2)
                        pygame.draw.circle(surf, (0, 0, 0), 
                                         (self.tile_size // 2 + eye_x_offset, eye_y), 2)
                    else:
                        # Draw eyes with slight x-offset for animation
                        eye_y: int = self.tile_size // 2 - 5
                        eye_x_offset: int = 8 + offset
                        pygame.draw.circle(surf, (255, 255, 255), 
                                         (self.tile_size // 2 - eye_x_offset, eye_y), 5)
                        pygame.draw.circle(surf, (255, 255, 255), 
                                         (self.tile_size // 2 + eye_x_offset, eye_y), 5)
                        pygame.draw.circle(surf, (0, 0, 0), 
                                         (self.tile_size // 2 - eye_x_offset, eye_y), 2)
                        pygame.draw.circle(surf, (0, 0, 0), 
                                         (self.tile_size // 2 + eye_x_offset, eye_y), 2)
                        
                    self.sprites[direction].append(surf)
                    
    def get_direction_name(self) -> str:
        dx, dy = self.direction
        if dx < 0:
            return "left"
        elif dx > 0:
            return "right"
        elif dy < 0:
            return "up"
        else:
            return "down"
        
    def update(self, map_width: int, map_height: int) -> None:
        # Animation update (continuous)
        current_time: int = pygame.time.get_ticks()
        self.animation_timer += 0.1
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.sprites[self.get_direction_name()])
        
        # Movement update (every 2 seconds)
        if current_time - self.move_timer >= self.move_interval:
            # Choose a random direction
            self.direction = random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
            self.direction_name = self.get_direction_name()
            
            # Move exactly 1 grid in the chosen direction
            dx, dy = self.direction
            new_grid_x: int = self.grid_x + dx
            new_grid_y: int = self.grid_y + dy
            
            # Check boundaries and only move if within bounds
            if 0 <= new_grid_x < map_width:
                self.grid_x = new_grid_x
            
            if 0 <= new_grid_y < map_height:
                self.grid_y = new_grid_y
                
            # Reset timer
            self.move_timer = current_time
            
    def draw(self, screen: pygame.Surface) -> None:
        # Get current sprite frame
        self.image = self.sprites[self.direction_name][self.current_frame]
        
        # Draw the minion at its grid position
        screen_x: int = self.grid_x * self.tile_size
        screen_y: int = self.grid_y * self.tile_size
        
        # Draw the sprite
        screen.blit(self.image, (screen_x, screen_y)) 