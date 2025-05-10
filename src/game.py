import pygame
import sys
import random
import cv2
import numpy as np
import base64
import openai
import os
from src.minion import Minion
from src.guide import Guide
from src.ai_service import AIService
from src.tilemap import TileMap

class Game:
    def __init__(self, use_openai=False):
        # Initialize pygame
        pygame.init()
        
        # Flag for using OpenAI
        self.use_openai = use_openai
        if use_openai:
            self.ai_service = AIService()
        else:
            self.ai_service = None
        
        # Constants
        self.SCREEN_WIDTH = 1200
        self.SCREEN_HEIGHT = 800
        self.TILE_SIZE = 60
        self.GRID_WIDTH = 8
        self.GRID_HEIGHT = 10

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
        
        # Calculate board position to center it
        self.BOARD_X = (self.SCREEN_WIDTH - (self.GRID_WIDTH * self.TILE_SIZE)) // 2
        self.BOARD_Y = (self.SCREEN_HEIGHT - (self.GRID_HEIGHT * self.TILE_SIZE)) // 2
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.LIGHT_BLUE = (173, 216, 230)
        self.YELLOW = (255, 255, 0)
        self.SPEECH_BG = (50, 50, 50, 180)  # Semi-transparent dark gray
        self.BUTTON_COLOR = (70, 130, 180)  # Steel blue
        self.BUTTON_HOVER_COLOR = (100, 160, 210)  # Lighter blue for hover
        
        # Tile colors (similar to original)
        self.TILE_COLORS = {
            "empty": (34, 139, 34),    # Forest green (grass)
            "sushi": (30, 144, 255),   # Blue
            "donut": (139, 69, 19),    # Brown
            "banana": (238, 214, 175), # Sandy/Yellow
            "team1": (255, 100, 100),  # Red-ish
            "team2": (100, 100, 255)   # Blue-ish
        }
        
        # Create the screen
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Signal & Strategy: The Minion's Quest")
        self.clock = pygame.time.Clock()
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 16)
        self.thought_font = pygame.font.SysFont('Arial', 18, italic=True)
        
        # Create minions
        self.minions = []
        for i in range(5):
            self.minions.append(Minion(
                random.randint(0, self.GRID_WIDTH-1),
                random.randint(0, self.GRID_HEIGHT-1),
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

        # Create sprite placeholders
        self.create_sprites()
        
        # Create AI button - make it larger and more prominent
        self.ai_button_rect = pygame.Rect(20, 20, 200, 60)
        self.ai_button_hover = False
        
        # Game state
        self.initialize_game()
        
    def create_sprites(self):
        """Create placeholder sprites for minions and items"""
        self.sprites = {}
        
        # Create minion sprites (team 1)
        self.sprites["team1"] = self.create_minion_sprite(self.TILE_COLORS["team1"], self.TILE_SIZE)
        
        # Create minion sprites (team 2)
        self.sprites["team2"] = self.create_minion_sprite(self.TILE_COLORS["team2"], self.TILE_SIZE)
        
        # Create item sprites
        self.sprites["sushi"] = self.create_item_sprite("🍣", self.TILE_SIZE)
        self.sprites["donut"] = self.create_item_sprite("🍩", self.TILE_SIZE)
        self.sprites["banana"] = self.create_item_sprite("🍌", self.TILE_SIZE)
        
    def create_minion_sprite(self, color, size):
        """Create a simple minion sprite with the given color"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw minion body (circle)
        pygame.draw.circle(surf, color, (size//2, size//2), size//3)
        
        # Draw eyes
        eye_offset = 8
        pygame.draw.circle(surf, self.WHITE, (size//2 - eye_offset, size//2 - 5), 5)
        pygame.draw.circle(surf, self.WHITE, (size//2 + eye_offset, size//2 - 5), 5)
        pygame.draw.circle(surf, self.BLACK, (size//2 - eye_offset, size//2 - 5), 2)
        pygame.draw.circle(surf, self.BLACK, (size//2 + eye_offset, size//2 - 5), 2)
        
        # Draw smile
        pygame.draw.arc(surf, self.BLACK, (size//3, size//2, size//3, size//4), 0, 3.14, 2)
        
        return surf
    
    def create_item_sprite(self, emoji, size):
        """Create a sprite for an item using emojis on a colored background"""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Render the emoji text
        font = pygame.font.SysFont('Arial', size//2)
        text = font.render(emoji, True, self.WHITE)
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
            color = self.TILE_COLORS["empty"]
        elif tile_type == 1:  # Sushi
            color = self.TILE_COLORS["sushi"]
        elif tile_type == 2:  # Donut
            color = self.TILE_COLORS["donut"]
        elif tile_type == 3:  # Banana
            color = self.TILE_COLORS["banana"]
        elif tile_type == 4:  # Team 1 Minion
            color = self.TILE_COLORS["team1"]
        elif tile_type == 5:  # Team 2 Minion
            color = self.TILE_COLORS["team2"]
        else:
            color = self.GRAY
            
        surf.fill(color)
        
        # Add some texture to tiles
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
        
    def initialize_game(self):
        # Grid representation (0=empty, 1=sushi, 2=donut, 3=banana)
        self.grid = np.zeros((self.GRID_HEIGHT, self.GRID_WIDTH), dtype=int)
        
        # Minion positions
        self.team1_minion_pos = [0, 0]  # [y, x]
        self.team2_minion_pos = [self.GRID_HEIGHT-1, self.GRID_WIDTH-1]  # [y, x]
        
        # Generate target items for each team
        self.team1_targets = self.generate_targets()
        self.team2_targets = self.generate_targets()
        
        # Create guides and minions
        self.team1_guide = Guide(1, self.team1_targets)
        self.team2_guide = Guide(2, self.team2_targets)
        
        # Personality for team 1 minion (can be randomized)
        team1_personality = {
            "propensity_to_listen": 0.8,
            "intelligence": 4,
            "speed": 3,
            "power": 3,
            "style": "bubbly"
        }
        
        # Personality for team 2 minion (can be randomized)
        team2_personality = {
            "propensity_to_listen": 0.7,
            "intelligence": 3,
            "speed": 4,
            "power": 2,
            "style": "hectic"
        }
        
        self.team1_minion = Minion(1, self.team1_minion_pos, team1_personality)
        self.team2_minion = Minion(2, self.team2_minion_pos, team2_personality)
        
        # Set OpenAI flag for minions if needed
        if self.use_openai:
            self.team1_minion.use_openai = True
            self.team2_minion.use_openai = True
        
        # Create tile surfaces for each type
        self.tile_surfaces = {}
        for i in range(6):  # 0-5: empty, sushi, donut, banana, team1, team2
            self.tile_surfaces[i] = self.create_tile(i, self.TILE_SIZE)
        
        # Place minions on grid (4=team1 minion, 5=team2 minion)
        self.grid[self.team1_minion_pos[0]][self.team1_minion_pos[1]] = 4
        self.grid[self.team2_minion_pos[0]][self.team2_minion_pos[1]] = 5
        
        # Items collected by each team
        self.team1_collected = []
        self.team2_collected = []
        
        # Current turn (1 = team1, 2 = team2)
        self.current_team = 1
        
        # Game status
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        self.max_turns = 50
        
        # AI turn controls
        self.ai_thinking = False
        self.ai_thinking_time = 0
        self.ai_thinking_max_time = 2000  # 2 seconds
        self.pending_move = None
        
        # Dialogue and gesture displays
        self.current_dialogue = ""
        self.current_thought = ""
        self.current_gesture = ""
        self.dialogue_timer = 0
        self.dialogue_display_time = 3000  # 3 seconds
        
        # Distribute items on the grid
        self.distribute_items()
        
    def generate_targets(self):
        # Generate 5 random items (1=sushi, 2=donut, 3=banana)
        return [random.randint(1, 3) for _ in range(5)]
        
    def distribute_items(self):
        # Distribute items on the grid
        num_items = {
            1: 10,  # sushi count
            2: 10,  # donut count
            3: 10,  # banana count
        }
        
        # Place items randomly on empty cells
        for item_type, count in num_items.items():
            placed = 0
            while placed < count:
                x = random.randint(0, self.GRID_WIDTH-1)
                y = random.randint(0, self.GRID_HEIGHT-1)
                
                # If the cell is empty, place the item
                if self.grid[y][x] == 0:
                    self.grid[y][x] = item_type
                    placed += 1
                    
    def item_to_emoji(self, item_code):
        if item_code == 0:
            return "0"  # Empty
        elif item_code == 1:
            return "🍣"  # Sushi
        elif item_code == 2:
            return "🍩"  # Donut
        elif item_code == 3:
            return "🍌"  # Banana
        elif item_code == 4:
            return "M1"  # Team 1 Minion
        elif item_code == 5:
            return "M2"  # Team 2 Minion
        return "?"
        
    def run(self):
        # Main game loop
        self.running = True
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(60)
            
        # Quit pygame
        pygame.quit()
        sys.exit()
        
    def handle_events(self):
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Handle mouse events
            if event.type == pygame.MOUSEMOTION:
                # Check if mouse is hovering over the AI button
                self.ai_button_hover = self.ai_button_rect.collidepoint(event.pos)
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    # Check if AI button was clicked
                    if self.ai_button_rect.collidepoint(event.pos):
                        # Skip AI thinking time if already thinking
                        if self.ai_thinking:
                            self.ai_thinking_time = self.ai_thinking_max_time
                        else:
                            # Take an AI turn
                            self.start_ai_turn()
                    elif self.btn_rect.collidepoint(event.pos) and self.last_frame_for_api is not None:
                        # send the cached frame to OpenAI
                        pygame.event.set_blocked(pygame.MOUSEBUTTONDOWN)  # avoid double-click spam
                        self.query_openai(self.last_frame_for_api.copy())
                        pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)

            # Handle key presses for human players and debugging
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Skip AI thinking time if already thinking
                    if self.ai_thinking:
                        self.ai_thinking_time = self.ai_thinking_max_time
                    else:
                        # Take an AI turn
                        self.start_ai_turn()
                elif event.key == pygame.K_r:
                    # Reset game
                    self.initialize_game()
                
                # Human gestures for team 1 (testing)
                elif event.key == pygame.K_1:
                    self.send_gesture(1, "wink left eye")
                elif event.key == pygame.K_2:
                    self.send_gesture(1, "wink right eye")
                elif event.key == pygame.K_3:
                    self.send_gesture(1, "nod twice")
                elif event.key == pygame.K_UP:
                    self.send_gesture(1, "point up")
                elif event.key == pygame.K_DOWN:
                    self.send_gesture(1, "point down")
                elif event.key == pygame.K_LEFT:
                    self.send_gesture(1, "point left")
                elif event.key == pygame.K_RIGHT:
                    self.send_gesture(1, "point right")
                    
    def send_gesture(self, team_id, gesture):
        """Send a gesture from the guide to the minion"""
        self.current_gesture = f"Team {team_id} Guide: {gesture}"
        
        if team_id == 1:
            # Team 1 Guide sends gesture to Team 1 Minion
            move_override = self.team1_minion.receive_gesture(gesture)
            if move_override is not None:
                # If the gesture directly indicates a move, use it
                self.pending_move = move_override
                self.take_turn(self.pending_move)
        else:
            # Team 2 Guide sends gesture to Team 2 Minion
            move_override = self.team2_minion.receive_gesture(gesture)
            if move_override is not None:
                # If the gesture directly indicates a move, use it
                self.pending_move = move_override
                self.take_turn(self.pending_move)
                    
    def start_ai_turn(self):
        """Start the AI thinking process for the current team"""
        if self.game_over:
            return
            
        self.ai_thinking = True
        self.ai_thinking_time = 0
        
        # Decide which gesture to send
        if self.current_team == 1:
            # Team 1 Guide decides gesture
            gesture = self.team1_guide.decide_gesture(
                self.grid, 
                self.team1_minion_pos, 
                self.team2_minion_pos
            )
            self.send_gesture(1, gesture)
        else:
            # Team 2 Guide decides gesture
            gesture = self.team2_guide.decide_gesture(
                self.grid,
                self.team2_minion_pos,
                self.team1_minion_pos
            )
            self.send_gesture(2, gesture)
                
    def take_turn(self, move):
        """Process the current team's move"""
        if self.game_over:
            return
        
        # Reset AI thinking
        self.ai_thinking = False
        self.pending_move = None
        
        # Process the move
        if self.current_team == 1:
            # Generate dialogue for team 1 minion
            self.current_dialogue, self.current_thought = self.team1_minion.generate_dialogue(
                move, 
                self.grid,
                self.ai_service,
                self.team1_collected
            )
            
            # Calculate new position without updating the grid yet
            new_pos = self.calculate_new_position(self.team1_minion_pos.copy(), move)
            
            # Check if there's an item at the new position
            self.check_item_collection(new_pos, self.team1_collected, self.team1_targets)
            
            # Move team 1 minion
            self.move_minion(self.team1_minion_pos, move)
            
            # Update team 1 minion's position
            self.team1_minion.grid_pos = self.team1_minion_pos
            
            # Update team 1 guide's knowledge
            self.team1_guide.update_collected(self.team1_collected)
        else:
            # Generate dialogue for team 2 minion
            self.current_dialogue, self.current_thought = self.team2_minion.generate_dialogue(
                move, 
                self.grid,
                self.ai_service,
                self.team2_collected
            )
            
            # Calculate new position without updating the grid yet
            new_pos = self.calculate_new_position(self.team2_minion_pos.copy(), move)
            
            # Check if there's an item at the new position
            self.check_item_collection(new_pos, self.team2_collected, self.team2_targets)
            
            # Move team 2 minion
            self.move_minion(self.team2_minion_pos, move)
            
            # Update team 2 minion's position
            self.team2_minion.grid_pos = self.team2_minion_pos
            
            # Update team 2 guide's knowledge
            self.team2_guide.update_collected(self.team2_collected)
            
        # Start dialogue timer
        self.dialogue_timer = pygame.time.get_ticks()
            
        # Check win conditions
        self.check_win_conditions()
        
        # Switch teams
        self.current_team = 2 if self.current_team == 1 else 1
        self.turn_count += 1
        
        # Check if max turns reached
        if self.turn_count >= self.max_turns:
            self.game_over = True
            self.winner = 0  # Draw
        
    def calculate_new_position(self, position, direction):
        """Calculate a new position based on the current position and direction"""
        new_pos = position.copy()
        if direction == "up" and position[0] > 0:
            new_pos[0] -= 1
        elif direction == "down" and position[0] < self.GRID_HEIGHT - 1:
            new_pos[0] += 1
        elif direction == "left" and position[1] > 0:
            new_pos[1] -= 1
        elif direction == "right" and position[1] < self.GRID_WIDTH - 1:
            new_pos[1] += 1
        # "stay" does nothing
        return new_pos
        
    def move_minion(self, minion_pos, direction):
        """Move a minion in the specified direction"""
        # Clear current position
        self.grid[minion_pos[0]][minion_pos[1]] = 0
        
        # Calculate new position
        new_pos = minion_pos.copy()
        if direction == "up" and minion_pos[0] > 0:
            new_pos[0] -= 1
        elif direction == "down" and minion_pos[0] < self.GRID_HEIGHT - 1:
            new_pos[0] += 1
        elif direction == "left" and minion_pos[1] > 0:
            new_pos[1] -= 1
        elif direction == "right" and minion_pos[1] < self.GRID_WIDTH - 1:
            new_pos[1] += 1
        # "stay" does nothing
        
        # Update minion position
        minion_pos[0] = new_pos[0]
        minion_pos[1] = new_pos[1]
        
        # Get the minion code for the current team
        minion_code = 4 if self.current_team == 1 else 5
        
        # Update grid with new position
        self.grid[minion_pos[0]][minion_pos[1]] = minion_code
        
    def check_item_collection(self, minion_pos, collected_items, target_items):
        """Check if the minion has collected an item"""
        y, x = minion_pos
        item = self.grid[y][x]
        
        # If the position has an item (1-3), collect it
        if 1 <= item <= 3:
            collected_items.append(item)
            
    def check_win_conditions(self):
        """Check if a team has won"""
        # Check if team 1 has collected all targets
        team1_matches = 0
        for item in self.team1_targets:
            if self.team1_collected.count(item) > 0:
                team1_matches += 1
                
        if team1_matches >= 5:
            self.game_over = True
            self.winner = 1
            
        # Check if team 2 has collected all targets
        team2_matches = 0
        for item in self.team2_targets:
            if self.team2_collected.count(item) > 0:
                team2_matches += 1
                
        if team2_matches >= 5:
            self.game_over = True
            self.winner = 2
            
    def update(self):
        """Update game state"""
        current_time = pygame.time.get_ticks()
        
        # Update AI thinking
        if self.ai_thinking:
            self.ai_thinking_time += self.clock.get_time()
            
            # If AI has finished thinking
            if self.ai_thinking_time >= self.ai_thinking_max_time:
                # Decide AI move
                if self.current_team == 1:
                    self.pending_move = self.team1_minion.decide_move(
                        self.grid,
                        self.ai_service,
                        self.team1_collected,
                        self.team1_targets if self.use_openai else None  # Only pass targets in OpenAI mode for debugging
                    )
                else:
                    self.pending_move = self.team2_minion.decide_move(
                        self.grid,
                        self.ai_service,
                        self.team2_collected,
                        self.team2_targets if self.use_openai else None  # Only pass targets in OpenAI mode for debugging
                    )
                    
                # Execute the move
                if self.pending_move:
                    self.take_turn(self.pending_move)
        
        # Check if dialogue display time has expired
        if self.current_dialogue and current_time - self.dialogue_timer >= self.dialogue_display_time:
            self.current_dialogue = ""
            self.current_thought = ""
            
    def draw(self):
        """Render the game"""
        # Clear the screen
        self.screen.fill(self.BLACK)
        
        # Draw AI button - position at top-left, make it larger and more visible
        button_color = self.BUTTON_HOVER_COLOR if self.ai_button_hover else self.BUTTON_COLOR
        pygame.draw.rect(self.screen, button_color, self.ai_button_rect)
        pygame.draw.rect(self.screen, self.WHITE, self.ai_button_rect, 3)  # Thicker white border
        
        # Button text - more prominent
        button_text = self.font.render("Take AI Turn", True, self.WHITE)
        button_text_rect = button_text.get_rect(center=self.ai_button_rect.center)
        self.screen.blit(button_text, button_text_rect)
        
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
        # Draw game board background
        pygame.draw.rect(
            self.screen, 
            self.GRAY, 
            (self.BOARD_X, self.BOARD_Y, 
             self.GRID_WIDTH * self.TILE_SIZE, 
             self.GRID_HEIGHT * self.TILE_SIZE)
        )
        
        # Draw grid cells
        for y in range(self.GRID_HEIGHT):
            for x in range(self.GRID_WIDTH):
                # Calculate position
                rect_x = self.BOARD_X + (x * self.TILE_SIZE)
                rect_y = self.BOARD_Y + (y * self.TILE_SIZE)
                
                # Get tile type
                item_code = self.grid[y][x]
                
                # Draw the colored tile background
                self.screen.blit(self.tile_surfaces[0], (rect_x, rect_y))  # Draw grass tile
                
                # Draw cell content based on code
                if item_code == 1:  # Sushi
                    self.screen.blit(self.sprites["sushi"], (rect_x, rect_y))
                elif item_code == 2:  # Donut
                    self.screen.blit(self.sprites["donut"], (rect_x, rect_y))
                elif item_code == 3:  # Banana
                    self.screen.blit(self.sprites["banana"], (rect_x, rect_y))
                elif item_code == 4:  # Team 1 Minion
                    self.screen.blit(self.sprites["team1"], (rect_x, rect_y))
                elif item_code == 5:  # Team 2 Minion
                    self.screen.blit(self.sprites["team2"], (rect_x, rect_y))
        
        # Draw sidebar information
        sidebar_x = self.BOARD_X + (self.GRID_WIDTH * self.TILE_SIZE) + 20
        sidebar_y = self.BOARD_Y
        
        # Draw current turn
        turn_text = self.font.render(f"Turn: {self.turn_count}/{self.max_turns}", True, self.WHITE)
        self.screen.blit(turn_text, (sidebar_x, sidebar_y))
        sidebar_y += 40
        
        # Draw current team
        team_color = self.TILE_COLORS["team1"] if self.current_team == 1 else self.TILE_COLORS["team2"]
        team_text = self.font.render(f"Current Team: {self.current_team}", True, team_color)
        self.screen.blit(team_text, (sidebar_x, sidebar_y))
        sidebar_y += 40
        
        # Draw team 1 targets (only visible to team 1 guide in real implementation)
        team1_target_text = self.font.render("Team 1 Targets:", True, self.TILE_COLORS["team1"])
        self.screen.blit(team1_target_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw target items as icons
        for i, target in enumerate(self.team1_targets):
            icon_name = ["", "sushi", "donut", "banana"][target]
            icon_x = sidebar_x + (i * 40)
            self.screen.blit(self.sprites[icon_name], (icon_x, sidebar_y))
        sidebar_y += 50
        
        # Draw team 2 targets (only visible to team 2 guide in real implementation)
        team2_target_text = self.font.render("Team 2 Targets:", True, self.TILE_COLORS["team2"])
        self.screen.blit(team2_target_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw target items as icons
        for i, target in enumerate(self.team2_targets):
            icon_name = ["", "sushi", "donut", "banana"][target]
            icon_x = sidebar_x + (i * 40)
            self.screen.blit(self.sprites[icon_name], (icon_x, sidebar_y))
        sidebar_y += 50
        
        # Draw team 1 collected items
        team1_collected_text = self.font.render("Team 1 Collected:", True, self.TILE_COLORS["team1"])
        self.screen.blit(team1_collected_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw collected items as icons
        if self.team1_collected:
            for i, item in enumerate(self.team1_collected):
                icon_name = ["", "sushi", "donut", "banana"][item]
                icon_x = sidebar_x + (i * 40)
                # Only show up to 8 items per row
                icon_y = sidebar_y + ((i // 8) * 40)
                self.screen.blit(self.sprites[icon_name], (icon_x, icon_y))
            sidebar_y += 50
        else:
            none_text = self.small_font.render("None", True, self.WHITE)
            self.screen.blit(none_text, (sidebar_x, sidebar_y))
            sidebar_y += 30
        
        # Draw team 2 collected items
        team2_collected_text = self.font.render("Team 2 Collected:", True, self.TILE_COLORS["team2"])
        self.screen.blit(team2_collected_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw collected items as icons
        if self.team2_collected:
            for i, item in enumerate(self.team2_collected):
                icon_name = ["", "sushi", "donut", "banana"][item]
                icon_x = sidebar_x + (i * 40)
                # Only show up to 8 items per row
                icon_y = sidebar_y + ((i // 8) * 40)
                self.screen.blit(self.sprites[icon_name], (icon_x, icon_y))
            sidebar_y += 50
        else:
            none_text = self.small_font.render("None", True, self.WHITE)
            self.screen.blit(none_text, (sidebar_x, sidebar_y))
            sidebar_y += 30
            
        sidebar_y += 20
        
        # Draw personality information for current team
        if self.current_team == 1:
            minion = self.team1_minion
            team_color = self.TILE_COLORS["team1"]
        else:
            minion = self.team2_minion
            team_color = self.TILE_COLORS["team2"]
            
        personality_text = self.font.render(f"Team {self.current_team} Minion Personality:", True, team_color)
        self.screen.blit(personality_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        style_text = self.small_font.render(f"Style: {minion.personality['style']}", True, self.WHITE)
        self.screen.blit(style_text, (sidebar_x, sidebar_y))
        sidebar_y += 25
        
        intel_text = self.small_font.render(f"Intelligence: {minion.personality['intelligence']}/5", True, self.WHITE)
        self.screen.blit(intel_text, (sidebar_x, sidebar_y))
        sidebar_y += 25
        
        obedience_text = self.small_font.render(f"Obedience: {minion.personality['propensity_to_listen']:.1f}", True, self.WHITE)
        self.screen.blit(obedience_text, (sidebar_x, sidebar_y))
        sidebar_y += 40
        
        # Draw current gesture
        if self.current_gesture:
            gesture_text = self.font.render("Current Gesture:", True, self.YELLOW)
            self.screen.blit(gesture_text, (sidebar_x, sidebar_y))
            sidebar_y += 30
            
            gesture_render = self.font.render(self.current_gesture, True, self.YELLOW)
            self.screen.blit(gesture_render, (sidebar_x, sidebar_y))
            
        # Draw AI thinking indicator
        if self.ai_thinking:
            thinking_text = self.font.render("Thinking...", True, self.WHITE)
            thinking_rect = thinking_text.get_rect(center=(self.SCREEN_WIDTH//2, self.BOARD_Y - 30))
            self.screen.blit(thinking_text, thinking_rect)
            
        # Draw dialogue bubble if there's current dialogue
        if self.current_dialogue:
            # Create a bubble above the minion
            minion_pos = self.team1_minion_pos if self.current_team == 1 else self.team2_minion_pos
            bubble_x = self.BOARD_X + (minion_pos[1] * self.TILE_SIZE) + self.TILE_SIZE//2
            bubble_y = self.BOARD_Y + (minion_pos[0] * self.TILE_SIZE) - 60
            
            # Create dialogue text
            dialogue_text = self.font.render(self.current_dialogue, True, self.WHITE)
            dialogue_rect = dialogue_text.get_rect(center=(bubble_x, bubble_y))
            
            # Draw bubble background
            bubble_padding = 10
            bubble_rect = pygame.Rect(
                dialogue_rect.left - bubble_padding,
                dialogue_rect.top - bubble_padding,
                dialogue_rect.width + bubble_padding * 2,
                dialogue_rect.height + bubble_padding * 2
            )
            
            # Create a surface with alpha for the semi-transparent background
            bubble_surface = pygame.Surface((bubble_rect.width, bubble_rect.height), pygame.SRCALPHA)
            bubble_surface.fill(self.SPEECH_BG)
            self.screen.blit(bubble_surface, bubble_rect)
            
            # Draw dialogue text
            self.screen.blit(dialogue_text, dialogue_rect)
            
            # Draw thought bubble (if space permits)
            if self.current_thought and bubble_y > 100:
                thought_y = bubble_y - 40
                thought_text = self.thought_font.render(f"({self.current_thought})", True, self.WHITE)
                thought_rect = thought_text.get_rect(center=(bubble_x, thought_y))
                
                # Draw thought bubble background
                thought_padding = 5
                thought_rect_bg = pygame.Rect(
                    thought_rect.left - thought_padding,
                    thought_rect.top - thought_padding,
                    thought_rect.width + thought_padding * 2,
                    thought_rect.height + thought_padding * 2
                )
                
                thought_surface = pygame.Surface((thought_rect_bg.width, thought_rect_bg.height), pygame.SRCALPHA)
                thought_surface.fill((100, 100, 100, 120))  # Lighter, more transparent
                self.screen.blit(thought_surface, thought_rect_bg)
                
                # Draw thought text
                self.screen.blit(thought_text, thought_rect)
        
        # If game over, display winner
        if self.game_over:
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            if self.winner == 0:
                result_text = self.font.render("Game Over: Draw!", True, self.WHITE)
            else:
                team_color = self.TILE_COLORS["team1"] if self.winner == 1 else self.TILE_COLORS["team2"]
                result_text = self.font.render(f"Game Over: Team {self.winner} Wins!", True, team_color)
                
            text_rect = result_text.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2))
            self.screen.blit(result_text, text_rect)
            
            restart_text = self.small_font.render("Press R to restart", True, self.WHITE)
            restart_rect = restart_text.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2 + 40))
            self.screen.blit(restart_text, restart_rect)
        
        # Update the display
        pygame.display.flip()


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
