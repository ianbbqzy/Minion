import pygame
import os
from PIL import Image, ImageSequence

class GifSprite:
    """A class to handle loading and displaying animated GIFs in Pygame"""
    
    def __init__(self, gif_path, size=None):
        """
        Initialize the GIF sprite
        
        Args:
            gif_path: Path to the GIF file
            size: Optional tuple (width, height) to resize the frames
        """
        self.gif_path = gif_path
        self.size = size
        self.frames = []
        self.frame_index = 0
        self.last_update_time = 0
        
        # Load the GIF file
        if os.path.exists(gif_path):
            pil_image = Image.open(gif_path)
            
            # Get frame duration from the GIF
            try:
                self.frame_delay = pil_image.info['duration']
            except KeyError:
                # Default to 100ms if duration not specified
                self.frame_delay = 100
                
            # Convert frame delay from milliseconds to seconds
            self.frame_delay /= 1000.0
            
            # Extract all frames from the GIF
            for frame in ImageSequence.Iterator(pil_image):
                frame_copy = frame.convert('RGBA')
                
                # Resize if size is specified
                if size:
                    frame_copy = frame_copy.resize(size)
                    
                # Convert PIL image to pygame surface
                frame_data = frame_copy.tobytes()
                pygame_surface = pygame.image.fromstring(
                    frame_data, frame_copy.size, frame_copy.mode
                )
                self.frames.append(pygame_surface)
        else:
            print(f"Warning: GIF file {gif_path} not found")
            # Create a small placeholder surface
            placeholder_size = size if size else (60, 60)
            placeholder = pygame.Surface(placeholder_size, pygame.SRCALPHA)
            placeholder.fill((255, 0, 255, 200))  # Purple semi-transparent
            self.frames = [placeholder]
            self.frame_delay = 0.1
    
    def update(self, current_time):
        """
        Update the animation frame based on elapsed time
        
        Args:
            current_time: Current game time in seconds
        """
        # Check if it's time to advance to the next frame
        if current_time - self.last_update_time > self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.last_update_time = current_time
    
    def get_current_frame(self):
        """Return the current frame as a pygame surface"""
        return self.frames[self.frame_index] 