"""
Main game controller module
"""
import pygame
import sys
import cv2
import numpy as np
import random
import os

from src.utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, GRID_WIDTH, GRID_HEIGHT,
    WEBCAM_WIDTH, WEBCAM_HEIGHT, PREVIEW_GAP, BLACK, WHITE,
    BUTTON_COLOR, BUTTON_HOVER_COLOR
)
from src.utils.game_state import GameState
from src.rendering.sprites import SpriteManager
from src.rendering.ui import Button, DialogueBox, WebcamDisplay
from src.rendering.board import BoardRenderer
from src.input.event_handler import EventHandler
from src.ai.gesture_recognition import GestureRecognizer
from src.entities.minion import Minion
from src.entities.guide import Guide
from src.ai.ai_service import AIService

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
        
        # Create the screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Signal & Strategy: The Minion's Quest")
        self.clock = pygame.time.Clock()
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 16)
        self.thought_font = pygame.font.SysFont('Arial', 18, italic=True)
        self.btn_font = pygame.font.SysFont(None, 24)
        
        # Calculate board position to center it
        self.BOARD_X = (SCREEN_WIDTH - (GRID_WIDTH * TILE_SIZE) - 400) // 2
        self.BOARD_Y = (SCREEN_HEIGHT - (GRID_HEIGHT * TILE_SIZE) - 400) // 2
        
        # Initialize components
        self.initialize_components()
        
        # Game state
        self.game_state = GameState()
        
        # Initialize game objects
        self.initialize_game_objects()
        
        # AI turn controls
        self.ai_thinking = False
        self.ai_thinking_time = 0
        self.ai_thinking_max_time = 2000  # 2 seconds
        self.pending_move = None
        
        # Dialogue and gesture displays
        self.current_gesture = ""
        
        # Main loop control
        self.running = True
        
    def initialize_components(self):
        """Initialize UI and rendering components"""
        # Create sprite manager
        self.sprites = SpriteManager(TILE_SIZE)
        
        # Create board renderer
        self.board_renderer = BoardRenderer(
            self.BOARD_X, self.BOARD_Y, 
            GRID_WIDTH, GRID_HEIGHT, 
            TILE_SIZE, self.sprites
        )
        
        # Create dialogue box
        self.dialogue_box = DialogueBox(self.font, self.thought_font)
        
        # Create AI button
        self.ai_button_rect = pygame.Rect(20, 20, 200, 60)
        self.ai_button = Button(
            self.ai_button_rect,
            "Take AI Turn",
            self.btn_font
        )

        # Webcam settings
        self.webcam = None
        self.webcam_available = False
        self.init_webcam()
    
        # Center horizontally, place at bottom with some margin
        bottom_margin = 50
        left_shift = 300
        webcam_x = (SCREEN_WIDTH - WEBCAM_WIDTH) // 2 - left_shift
        webcam_y = SCREEN_HEIGHT - WEBCAM_HEIGHT - bottom_margin

        self.webcam_display = WebcamDisplay(
            webcam_x,
            webcam_y,
            WEBCAM_WIDTH, 
            WEBCAM_HEIGHT,
            self.btn_font
        )
        
        # Webcam button
        btn_x = self.ai_button_rect.x
        btn_y = self.ai_button_rect.y + self.ai_button_rect.height + 10  # Place just below AI button
        self.webcam_button = Button(
            pygame.Rect(btn_x, btn_y, 200, 60),
            "Query with Camera",
            self.btn_font
        )
        
        # Gesture recognizer
        self.gesture_recognizer = GestureRecognizer()
        
        # Event handler
        self.event_handler = EventHandler(self)
    
    def init_webcam(self):
        """Initialize the webcam"""
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
        
    def initialize_game_objects(self):
        """Initialize game objects based on game state"""
        # Create guides and minions
        self.team1_guide = Guide(1, self.game_state.team1_targets)
        self.team2_guide = Guide(2, self.game_state.team2_targets)
        
        # Personality for team 1 minion
        team1_personality = {
            "propensity_to_listen": 0.8,
            "intelligence": 4,
            "speed": 3,
            "power": 3,
            "style": "bubbly"
        }
        
        # Personality for team 2 minion
        team2_personality = {
            "propensity_to_listen": 0.7,
            "intelligence": 3,
            "speed": 4,
            "power": 2,
            "style": "hectic"
        }
        
        self.team1_minion = Minion(1, self.game_state.team1_minion_pos, team1_personality)
        self.team2_minion = Minion(2, self.game_state.team2_minion_pos, team2_personality)
        
        # Set OpenAI flag for minions if needed
        if self.use_openai:
            self.team1_minion.use_openai = True
            self.team2_minion.use_openai = True
        
        # Add this line to initialize the new attribute for the live frame
        self.live_pygame_frame_surface = None
        
    def reset_game_objects(self):
        """Reset game objects after game state reset"""
        # Update guide targets
        self.team1_guide.targets = self.game_state.team1_targets
        self.team2_guide.targets = self.game_state.team2_targets
        
        # Update minion positions
        self.team1_minion.grid_pos = self.game_state.team1_minion_pos
        self.team2_minion.grid_pos = self.game_state.team2_minion_pos
        
        # Reset dialogue and gestures
        self.dialogue_box.dialogue = ""
        self.dialogue_box.thought = ""
        self.current_gesture = ""
        
        # Reset AI turn controls
        self.ai_thinking = False
        self.ai_thinking_time = 0
        self.pending_move = None
        
    def run(self):
        """Main game loop"""
        while self.running:
            self.event_handler.process_events()
            self.update()
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(60)
            
    def update(self):
        """Update game state"""
        current_time = pygame.time.get_ticks()
        
        # Update dialogue display
        self.dialogue_box.update()
        
        # Update AI thinking
        if self.ai_thinking:
            self.ai_thinking_time += self.clock.get_time()
            
            # If AI has finished thinking
            if self.ai_thinking_time >= self.ai_thinking_max_time:
                # Decide AI move
                if self.game_state.current_team == 1:
                    self.pending_move = self.team1_minion.decide_move(
                        self.game_state.grid,
                        self.ai_service,
                        self.game_state.team1_collected,
                        self.game_state.team1_targets if self.use_openai else None
                    )
                else:
                    self.pending_move = self.team2_minion.decide_move(
                        self.game_state.grid,
                        self.ai_service,
                        self.game_state.team2_collected,
                        self.game_state.team2_targets if self.use_openai else None
                    )
                    
                # Execute the move
                if self.pending_move:
                    self.take_turn(self.pending_move)
        
        # Update webcam frame
        if self.webcam_available:
            ok, frame = self.webcam.read()
            if ok:
                frame = cv2.resize(frame, (WEBCAM_WIDTH, WEBCAM_HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame_surface = pygame.surfarray.make_surface(np.flipud(frame))
                # Store the pygame surface for drawing
                self.live_pygame_frame_surface = frame_surface
                # Save raw CV2 frame for API (GestureRecognizer expects this format)
                self.webcam_display.last_frame = frame
            else:
                # Indicate no current frame available for drawing
                self.live_pygame_frame_surface = None
        else:
            # Indicate no current frame available for drawing
            self.live_pygame_frame_surface = None
    
    def draw(self):
        """Render the game"""
        # Clear the screen
        self.screen.fill(BLACK)
        
        # Draw AI button
        self.ai_button.draw(self.screen)
        
        # Draw the live webcam feed or a placeholder
        if self.live_pygame_frame_surface:
            self.webcam_display.draw_camera_feed(self.screen, self.live_pygame_frame_surface)
        elif self.webcam_available: # Camera is supposed to be available but no frame / error
            self.webcam_display.draw_placeholder(self.screen, "Camera Error")
        else: # Camera is not available
            self.webcam_display.draw_placeholder(self.screen, "No Camera")
        
        # Draw webcam button
        self.webcam_button.draw(self.screen)
        
        self.webcam_display.draw_preview(self.screen)
        
        # Draw game board
        self.board_renderer.draw(self.screen, self.game_state.grid)
        
        # Draw sidebar information
        sidebar_y = self.board_renderer.draw_sidebar(
            self.screen, 
            self.game_state, 
            self.font, 
            self.small_font
        )
        
        # Draw current minion personality
        sidebar_x = self.BOARD_X + (GRID_WIDTH * TILE_SIZE) + 20
        sidebar_y += 20
        
        # Get current minion
        if self.game_state.current_team == 1:
            minion = self.team1_minion
            team_color = self.sprites.sprites["team1"].get_at((TILE_SIZE//2, TILE_SIZE//2))
        else:
            minion = self.team2_minion
            team_color = self.sprites.sprites["team2"].get_at((TILE_SIZE//2, TILE_SIZE//2))
        
        # Draw personality info
        personality_text = self.font.render(f"Team {self.game_state.current_team} Minion Personality:", True, team_color)
        self.screen.blit(personality_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        style_text = self.small_font.render(f"Style: {minion.personality['style']}", True, WHITE)
        self.screen.blit(style_text, (sidebar_x, sidebar_y))
        sidebar_y += 25
        
        intel_text = self.small_font.render(f"Intelligence: {minion.personality['intelligence']}/5", True, WHITE)
        self.screen.blit(intel_text, (sidebar_x, sidebar_y))
        sidebar_y += 25
        
        obedience_text = self.small_font.render(f"Obedience: {minion.personality['propensity_to_listen']:.1f}", True, WHITE)
        self.screen.blit(obedience_text, (sidebar_x, sidebar_y))
        sidebar_y += 40
        
        # Draw current gesture
        if self.current_gesture:
            gesture_text = self.font.render("Current Gesture:", True, (255, 255, 0))
            self.screen.blit(gesture_text, (sidebar_x, sidebar_y))
            sidebar_y += 30
            
            gesture_render = self.font.render(self.current_gesture, True, (255, 255, 0))
            self.screen.blit(gesture_render, (sidebar_x, sidebar_y))
        
        # Draw AI thinking indicator
        if self.ai_thinking:
            thinking_text = self.font.render("Thinking...", True, WHITE)
            thinking_rect = thinking_text.get_rect(center=(SCREEN_WIDTH//2, self.BOARD_Y - 30))
            self.screen.blit(thinking_text, thinking_rect)
        
        # Draw dialogue bubble
        minion_pos = self.game_state.team1_minion_pos if self.game_state.current_team == 1 else self.game_state.team2_minion_pos
        self.dialogue_box.draw(self.screen, minion_pos, self.BOARD_X, self.BOARD_Y, TILE_SIZE)
        
        # Draw game over screen if needed
        if self.game_state.game_over:
            self.board_renderer.draw_game_over(
                self.screen, 
                self.game_state.winner, 
                SCREEN_WIDTH, 
                SCREEN_HEIGHT, 
                self.font, 
                self.small_font
            )
        
        # Update the display
        pygame.display.flip()
    
    def start_ai_turn(self):
        """Start the AI thinking process for the current team"""
        if self.game_state.game_over:
            return
            
        self.ai_thinking = True
        self.ai_thinking_time = 0
        
        # Decide which gesture to send
        if self.game_state.current_team == 1:
            # Team 1 Guide decides gesture
            gesture = self.team1_guide.decide_gesture(
                self.game_state.grid, 
                self.game_state.team1_minion_pos, 
                self.game_state.team2_minion_pos
            )
            self.send_gesture(1, gesture)
        else:
            # Team 2 Guide decides gesture
            gesture = self.team2_guide.decide_gesture(
                self.game_state.grid,
                self.game_state.team2_minion_pos,
                self.game_state.team1_minion_pos
            )
            self.send_gesture(2, gesture)
                    
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
                
    def take_turn(self, move):
        """Process the current team's move"""
        if self.game_state.game_over:
            return
        
        # Reset AI thinking
        self.ai_thinking = False
        self.pending_move = None
        
        # Process the move
        if self.game_state.current_team == 1:
            # Generate dialogue for team 1 minion
            dialogue, thought = self.team1_minion.generate_dialogue(
                move, 
                self.game_state.grid,
                self.ai_service,
                self.game_state.team1_collected
            )
            self.dialogue_box.set_dialogue(dialogue, thought)
            
            # Calculate new position without updating the grid yet
            new_pos = self.game_state.calculate_new_position(self.game_state.team1_minion_pos.copy(), move)
            
            # Check if there's an item at the new position
            self.game_state.check_item_collection(new_pos, self.game_state.team1_collected)
            
            # Move team 1 minion
            self.game_state.move_minion(self.game_state.team1_minion_pos, move)
            
            # Update team 1 minion's position
            self.team1_minion.grid_pos = self.game_state.team1_minion_pos
            
            # Update team 1 guide's knowledge
            self.team1_guide.update_collected(self.game_state.team1_collected)
        else:
            # Generate dialogue for team 2 minion
            dialogue, thought = self.team2_minion.generate_dialogue(
                move, 
                self.game_state.grid,
                self.ai_service,
                self.game_state.team2_collected
            )
            self.dialogue_box.set_dialogue(dialogue, thought)
            
            # Calculate new position without updating the grid yet
            new_pos = self.game_state.calculate_new_position(self.game_state.team2_minion_pos.copy(), move)
            
            # Check if there's an item at the new position
            self.game_state.check_item_collection(new_pos, self.game_state.team2_collected)
            
            # Move team 2 minion
            self.game_state.move_minion(self.game_state.team2_minion_pos, move)
            
            # Update team 2 minion's position
            self.team2_minion.grid_pos = self.game_state.team2_minion_pos
            
            # Update team 2 guide's knowledge
            self.team2_guide.update_collected(self.game_state.team2_collected)
            
        # Check win conditions
        self.game_state.check_win_conditions()
        
        # Move to next turn
        self.game_state.next_turn()
    
    def query_openai(self, frame_rgb):
        """Send the captured frame to the gesture recognizer and process the result"""
        # Create a preview of the captured frame
        # Note: frame_rgb is already self.webcam_display.last_frame.copy()
        # The .copy() inside capture_frame call is self.game.webcam_display.last_frame.copy().copy()
        preview_surface = self.gesture_recognizer.capture_frame(frame_rgb.copy()) # Using frame_rgb directly as it's already a copy
        
        if preview_surface is None:
            print("Error: Could not create preview surface for AI query in Game.query_openai.")
            self.webcam_display.set_captured_preview(None) # Ensure old preview is cleared
            # Optionally, you could set a message to display in the UI about the error
            # For example, if you add a self.gesture_text to the Game class:
            # self.gesture_text = "Error processing frame"
            return

        self.webcam_display.set_captured_preview(preview_surface)
        
        # Analyze the gesture
        gesture = self.gesture_recognizer.analyze_gesture()
        print("Gesture:", gesture)
        
        # You can add custom handling of the gesture here
        # For example, mapping gestures to in-game actions
