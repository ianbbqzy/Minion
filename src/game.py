import pygame
import sys
import random
import cv2
import numpy as np
from typing import List, Tuple, Optional, Union
from src.sprites import Minion
from src.tilemap import TileMap

class Game:
    def __init__(self) -> None:
        # Initialize pygame
        pygame.init()
        
        # Constants
        self.SCREEN_WIDTH: int = 1100  # Increased to accommodate webcam feed
        self.SCREEN_HEIGHT: int = 600
        self.TILE_SIZE: int = 64
        self.MAP_WIDTH: int = 12
        self.MAP_HEIGHT: int = 9
        
        # Webcam settings
        self.WEBCAM_WIDTH: int = 300
        self.WEBCAM_HEIGHT: int = 225
        self.webcam: Optional[cv2.VideoCapture] = None
        self.webcam_available: bool = False
        try:
            self.webcam = cv2.VideoCapture(0)
            if self.webcam.isOpened():
                self.webcam_available = True
            else:
                print("Warning: Webcam could not be opened. Retrying...")
                # Try a different approach
                self.webcam = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  # Specifically for macOS
                if self.webcam.isOpened():
                    self.webcam_available = True
                else:
                    print("Error: Could not access webcam. Running without camera.")
        except Exception as e:
            print(f"Error initializing webcam: {e}")
        
        # Colors
        self.WHITE: Tuple[int, int, int] = (255, 255, 255)
        self.BLACK: Tuple[int, int, int] = (0, 0, 0)
        
        # Create the screen
        self.screen: pygame.Surface = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Minion Movement Game")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        
        # Create tilemap
        self.tilemap: TileMap = TileMap(self.MAP_WIDTH, self.MAP_HEIGHT, self.TILE_SIZE)
        
        # Create minions
        self.minions: List[Minion] = []
        for i in range(5):
            self.minions.append(Minion(
                random.randint(0, self.MAP_WIDTH-1),
                random.randint(0, self.MAP_HEIGHT-1),
                self.TILE_SIZE
            ))
        
        self.running: bool = False
            
    def run(self) -> None:
        # Main game loop
        self.running = True
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(60)
            
        # Release webcam and quit pygame
        if self.webcam_available and self.webcam is not None:
            self.webcam.release()
        pygame.quit()
        sys.exit()
        
    def handle_events(self) -> None:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
    def update(self) -> None:
        # Update minions
        for minion in self.minions:
            minion.update(self.MAP_WIDTH, self.MAP_HEIGHT)
            
    def draw(self) -> None:
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Draw tilemap
        self.tilemap.draw(self.screen)
        
        # Draw minions
        for minion in self.minions:
            minion.draw(self.screen)
        
        # Get webcam frame and convert it to a pygame surface
        if self.webcam_available:
            ret: bool
            frame: np.ndarray
            ret, frame = self.webcam.read()
            if ret:
                # Resize frame to fit our display area
                frame = cv2.resize(frame, (self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT))
                # Convert from BGR (OpenCV) to RGB (Pygame)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Rotate the frame if needed (webcam is often flipped)
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                # Create pygame surface from numpy array
                webcam_surface: pygame.Surface = pygame.surfarray.make_surface(frame)
                # Draw webcam feed on the right side of the screen
                self.screen.blit(webcam_surface, (self.SCREEN_WIDTH - self.WEBCAM_WIDTH - 10, 10))
                
                # Draw a border around the webcam feed
                pygame.draw.rect(self.screen, self.WHITE, 
                                (self.SCREEN_WIDTH - self.WEBCAM_WIDTH - 10, 10, 
                                 self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT), 2)
            else:
                # Draw a placeholder when webcam frame isn't available
                pygame.draw.rect(self.screen, (50, 50, 50), 
                                (self.SCREEN_WIDTH - self.WEBCAM_WIDTH - 10, 10, 
                                 self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT), 0)
                font: pygame.font.Font = pygame.font.SysFont(None, 24)
                text: pygame.Surface = font.render("Camera Unavailable", True, self.WHITE)
                text_rect: pygame.Rect = text.get_rect(center=(self.SCREEN_WIDTH - self.WEBCAM_WIDTH//2 - 10, 
                                                  self.WEBCAM_HEIGHT//2 + 10))
                self.screen.blit(text, text_rect)
        else:
            # Draw a placeholder when webcam isn't available
            pygame.draw.rect(self.screen, (50, 50, 50), 
                            (self.SCREEN_WIDTH - self.WEBCAM_WIDTH - 10, 10, 
                             self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT), 0)
            font: pygame.font.Font = pygame.font.SysFont(None, 24)
            text: pygame.Surface = font.render("Camera Unavailable", True, self.WHITE)
            text_rect: pygame.Rect = text.get_rect(center=(self.SCREEN_WIDTH - self.WEBCAM_WIDTH//2 - 10, 
                                              self.WEBCAM_HEIGHT//2 + 10))
            self.screen.blit(text, text_rect)
        
        # Update the display
        pygame.display.flip() 
