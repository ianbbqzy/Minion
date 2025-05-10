import pygame
import sys
import random
import cv2
import numpy as np
import base64
import openai
from src.sprites import Minion
from src.tilemap import TileMap

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Constants
        self.SCREEN_WIDTH = 1100  # Increased to accommodate webcam feed
        self.SCREEN_HEIGHT = 600
        self.TILE_SIZE = 64
        self.MAP_WIDTH = 12
        self.MAP_HEIGHT = 9
        
        # Webcam settings
        self.WEBCAM_WIDTH = 300
        self.WEBCAM_HEIGHT = 225
        self.webcam = None
        self.webcam_available = False
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
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        
        # Create the screen
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Minion Movement Game")
        self.clock = pygame.time.Clock()
        
        # Create tilemap
        self.tilemap = TileMap(self.MAP_WIDTH, self.MAP_HEIGHT, self.TILE_SIZE)
        
        # Create minions
        self.minions = []
        for i in range(5):
            self.minions.append(Minion(
                random.randint(0, self.MAP_WIDTH-1),
                random.randint(0, self.MAP_HEIGHT-1),
                self.TILE_SIZE
            ))

        # ───── NEW: Send button ─────
        btn_w, btn_h = self.WEBCAM_WIDTH, 40
        btn_x = self.SCREEN_WIDTH - btn_w - 10
        btn_y = 10 + self.WEBCAM_HEIGHT + 8           # 8-px gap below the camera view
        self.btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        self.btn_font = pygame.font.SysFont(None, 24)
        self.last_frame_for_api = None                # frame cached for click  
        self.captured_preview_surface = None      # thumbnail shown after each click
        self.PREVIEW_GAP = 8                      # vertical spacing between UI blocks

        self.gesture_text = ""                      # latest GPT answer
        self.GESTURE_FONT = pygame.font.SysFont(None, 28)

    def run(self):
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
        
    def handle_events(self):
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
    def update(self):
        # Update minions
        for minion in self.minions:
            minion.update(self.MAP_WIDTH, self.MAP_HEIGHT)
            
    def draw(self):
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Draw tilemap
        self.tilemap.draw(self.screen)
        
        # Draw minions
        for minion in self.minions:
            minion.draw(self.screen)
        
        # Get webcam frame and convert it to a pygame surface
        if self.webcam_available:
            ok, frame = self.webcam.read()
            if ok:
                frame = cv2.resize(frame, (self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame_surface = pygame.surfarray.make_surface(np.flipud(frame))
                self.screen.blit(frame_surface, (self.btn_rect.x, 10))
                pygame.draw.rect(self.screen, self.WHITE,
                                 (self.btn_rect.x, 10, self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT), 2)
                self.last_frame_for_api = frame                 # save for button click
            else:
                self._draw_cam_placeholder("Camera Unavailable")
        else:
            self._draw_cam_placeholder("Camera Unavailable")

        # ───── Analyze button ─────
        color = (0, 120, 255) if self.last_frame_for_api is not None else self.GRAY
        pygame.draw.rect(self.screen, color, self.btn_rect, border_radius=6)
        label = "Query AI" if self.last_frame_for_api is not None else "No Camera"
        text_surf = self.btn_font.render(label, True, self.WHITE)
        self.screen.blit(text_surf, text_surf.get_rect(center=self.btn_rect.center))

        # ───── Captured-image preview ─────
        if self.captured_preview_surface is not None:
            prev_y = self.btn_rect.y + self.btn_rect.height + self.PREVIEW_GAP
            self.screen.blit(self.captured_preview_surface,
                            (self.btn_rect.x, prev_y))
            pygame.draw.rect(self.screen, self.WHITE,
                            (self.btn_rect.x, prev_y,
                            self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT), 2)
            # optional label
            label = self.btn_font.render("Last capture", True, self.WHITE)
            self.screen.blit(label, (self.btn_rect.x,
                                    prev_y + self.WEBCAM_HEIGHT + 4))
        
        # Update the display
        pygame.display.flip()

    # ──────────────────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # NEW: button click
            elif (event.type == pygame.MOUSEBUTTONDOWN and
                  event.button == 1 and
                  self.btn_rect.collidepoint(event.pos) and
                  self.last_frame_for_api is not None):
                # send the cached frame to OpenAI
                pygame.event.set_blocked(pygame.MOUSEBUTTONDOWN)  # avoid double-click spam
                self.query_openai(self.last_frame_for_api.copy())
                pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)

    # ──────────────────────────────────────────────
    def _draw_cam_placeholder(self, msg):
        pygame.draw.rect(self.screen, self.GRAY,
                         (self.btn_rect.x, 10, self.WEBCAM_WIDTH, self.WEBCAM_HEIGHT))
        t = self.btn_font.render(msg, True, self.WHITE)
        self.screen.blit(t, t.get_rect(center=(self.btn_rect.x + self.WEBCAM_WIDTH//2,
                                               10 + self.WEBCAM_HEIGHT//2)))

    # ──────────────────────────────────────────────
    def query_openai(self, frame_rgb):
        """Send the captured frame to GPT-4o Vision and print its answer."""

        GESTURE_PROMPT = (
            "You are a hand-gesture classifier.\n"
            "Look at the image and answer ONLY with one "
            "of these labels (case sensitive):\n"
            "  • ThumbsUp\n  • ThumbsDown\n  • Victory\n  • Stop\n"
            "  • PointLeft\n  • PointRight\n  • Fist\n  • OpenPalm\n"
            "  • Unknown\n"
            "If you are not sure, output Unknown."
        )

        # --- Build the pygame surface for the thumbnail ------------
        self.captured_preview_surface = pygame.surfarray.make_surface(
            np.flipud(frame_rgb)              # flip Y so it isn’t upside-down
        )
        try:
            _, png = cv2.imencode(".png",
                                cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR))
            b64_data = base64.b64encode(png.tobytes()).decode()

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=4,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": GESTURE_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {                         # ← wrap in an object
                                    "url": f"data:image/png;base64,{b64_data}",
                                    "detail": "auto"                  # optional but recommended
                                }
                            }
                        ]
                    }
                ]
            )
            self.gesture_text = response.choices[0].message.content.strip()
            print("Gesture:", self.gesture_text)
        except Exception as e:
            self.gesture_text = f"API error: {e}"
            print(self.gesture_text)