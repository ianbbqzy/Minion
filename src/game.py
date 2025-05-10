"""
Main game controller module
"""
import pygame
import sys
import cv2
import numpy as np
import random
import os
import asyncio, threading

from src.utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, GRID_WIDTH, GRID_HEIGHT,
    WEBCAM_WIDTH, WEBCAM_HEIGHT, PREVIEW_GAP, BLACK, WHITE,
    BUTTON_COLOR, BUTTON_HOVER_COLOR, GRADIENT_COLORS
)
from src.utils.game_state import GameState
from src.rendering.sprites import SpriteManager
from src.rendering.ui import DialogueBox, WebcamDisplay
from src.rendering.board import BoardRenderer
from src.rendering.ui_manager import UIManager
from src.input.event_handler import EventHandler
from src.ai.gesture_recognition import GestureRecognizer
from src.entities.minion import Minion
from src.entities.guide import Guide
from src.ai.ai_service import AIService
from src.utils.constants import TEAM1_MINION_1, TEAM1_MINION_2, TEAM2_MINION_1, TEAM2_MINION_2, TEAM1_MINION_1_INSTRUCTIONS, TEAM1_MINION_2_INSTRUCTIONS, TEAM2_MINION_1_INSTRUCTIONS, TEAM2_MINION_2_INSTRUCTIONS

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        self.ai_service = AIService()
        
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
        
        # Calculate board position to center it (will be used by board renderer and UI manager)
        self.BOARD_X = (SCREEN_WIDTH - (GRID_WIDTH * TILE_SIZE)) // 2
        self.BOARD_Y = 30  # Reduced from 50 to 30 to match UI Manager
        
        # Initialize components
        self.initialize_components()
        
        # Game state
        self.game_state = GameState()
        
        # Initialize game objects
        self.initialize_game_objects()
        
        # AI turn controls for simultaneous moves
        self.ai_turn_processing = False  # True when AI decisions are being processed
        self.ai_threads_completed = 0    # Counter for completed AI tasks

        # Stores move data for both minions of team 1 and team 2
        # 1 is team 1 minion 1, 2 is team 1 minion 2, 3 is team 2 minion 1, 4 is team 2 minion 2
        self.pending_moves = {1: None, 2: None, 3: None, 4: None}
        self.completion_lock = threading.Lock() # For safely incrementing ai_threads_completed
        
        # Dialogue and gesture displays
        self.current_gestures = {1: "No gesture", 2: "No gesture"} # Store gestures for each team
        
        # Team panel data
        self.team1_1_last_move = ""
        self.team1_2_last_move = ""
        self.team2_1_last_move = ""
        self.team2_2_last_move = ""
        
        # Main loop control
        self.running = True

        self.async_loop = asyncio.new_event_loop()
        threading.Thread(target=self.async_loop.run_forever, daemon=True).start()
        
    def initialize_components(self):
        """Initialize game components"""
        # Create sprite manager
        self.sprites = SpriteManager(TILE_SIZE)
        
        # Create board renderer
        self.board_renderer = BoardRenderer(
            self.BOARD_X, self.BOARD_Y, 
            GRID_WIDTH, GRID_HEIGHT, 
            TILE_SIZE, self.sprites
        )
        
        # Create UI manager to handle all UI components and layout
        self.ui_manager = UIManager(self)
        
        # Webcam settings
        self.webcam = None
        self.webcam_available = False
        self.init_webcam()
            
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
        
        self.team1_minion_1 = Minion(1, self.game_state.team1_minion_1_pos, team1_personality, TEAM1_MINION_1_INSTRUCTIONS)
        self.team1_minion_2 = Minion(1, self.game_state.team1_minion_2_pos, team1_personality, TEAM1_MINION_2_INSTRUCTIONS)
        self.team2_minion_1 = Minion(2, self.game_state.team2_minion_1_pos, team2_personality, TEAM2_MINION_1_INSTRUCTIONS)
        self.team2_minion_2 = Minion(2, self.game_state.team2_minion_2_pos, team2_personality, TEAM2_MINION_2_INSTRUCTIONS)
                
        # Add this line to initialize the new attribute for the live frame
        self.live_pygame_frame_surface = None
        
    def reset_game_objects(self):
        """Reset game objects after game state reset"""
        # Update guide targets
        self.team1_guide.targets = self.game_state.team1_targets
        self.team2_guide.targets = self.game_state.team2_targets
        
        # Update minion positions
        self.team1_minion_1.grid_pos = self.game_state.team1_minion_1_pos
        self.team1_minion_2.grid_pos = self.game_state.team1_minion_2_pos
        self.team2_minion_1.grid_pos = self.game_state.team2_minion_1_pos
        self.team2_minion_2.grid_pos = self.game_state.team2_minion_2_pos
        
        # Reset dialogue and gestures
        self.ui_manager.dialogue_box.dialogue = ""
        self.ui_manager.dialogue_box.thought = ""
        self.current_gestures = {1: "No gesture", 2: "No gesture"}
        
        # Reset team move info
        self.team1_1_last_move = ""
        self.team1_2_last_move = ""
        self.team2_1_last_move = ""
        self.team2_2_last_move = ""
        
        # Reset AI turn controls
        self.ai_turn_processing = False
        self.ai_threads_completed = 0
        self.pending_moves = {1: None, 2: None, 3: None, 4: None}
        
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
        # Update dialogue display (if it's a general display)
        self.ui_manager.dialogue_box.update()
        
        # Check if both AI tasks have finished
        if self.ai_turn_processing and self.ai_threads_completed == 4:
            print("AI turn completed")
            self.process_simultaneous_moves(self.pending_moves[1], self.pending_moves[2], self.pending_moves[3], self.pending_moves[4])
            # Reset flags for the next turn
            self.ai_turn_processing = False
            self.ai_threads_completed = 0
            self.pending_moves = {1: None, 2: None, 3: None, 4: None}
        
        # Update webcam frame
        if self.webcam_available:
            ok, frame = self.webcam.read()
            if ok:
                frame = cv2.resize(frame, (WEBCAM_WIDTH, WEBCAM_HEIGHT))
                frame = cv2.flip(frame, 1) # Horizontally flip the frame
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame_surface = pygame.surfarray.make_surface(np.flipud(frame))
                # Store the pygame surface for drawing
                self.live_pygame_frame_surface = frame_surface
                # Save raw CV2 frame for API (GestureRecognizer expects this format)
                self.ui_manager.webcam_display.last_frame = frame
            else:
                # Indicate no current frame available for drawing
                self.live_pygame_frame_surface = None
        else:
            # Indicate no current frame available for drawing
            self.live_pygame_frame_surface = None
            
        # Update UI manager
        self.ui_manager.update(
            self.game_state, 
            "", # General dialogue/thought can be managed via team-specific attributes now
            "", 
            self.team1_1_last_move, 
            self.team1_2_last_move, 
            self.team2_1_last_move, 
            self.team2_2_last_move, 
            self.game_state.current_team, # Still useful for UI highlighting
            self.live_pygame_frame_surface,
            self.webcam_available,
            self.ai_turn_processing # Use this to show general "AI is thinking" if needed
        )
    
    def draw(self):
        """Render the game"""
        # Draw UI components (background, panels, buttons, webcam)
        self.ui_manager.draw(
            self.screen, 
            self.game_state, 
            self.live_pygame_frame_surface, 
            self.webcam_available, 
            self.ai_turn_processing # Pass processing state for UI elements like thinking indicator
        )
        
        # Draw game board
        self.board_renderer.draw(self.screen, self.game_state.grid)
        
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
    
    def start_both_ai_turns(self):
        """Start the AI thinking process for both teams simultaneously."""
        if self.game_state.game_over or self.ai_turn_processing:
            return # Prevent starting new AI turns if game over or already processing
            
        self.ai_turn_processing = True
        self.ai_threads_completed = 0
        self.pending_moves = {1: None, 2: None, 3: None, 4: None}

        current_grid_snapshot = [row[:] for row in self.game_state.grid]

        
        collected_items_team1_snapshot = list(self.game_state.team1_collected)
        target_items_team1_snapshot = list(self.game_state.team1_targets) if self.game_state.team1_targets else None

        
        collected_items_team2_snapshot = list(self.game_state.team2_collected)
        target_items_team2_snapshot = list(self.game_state.team2_targets) if self.game_state.team2_targets else None
        
        # Callback for when an AI task completes
        def _ai_task_callback(future, minion_id):
            move_result = None
            try:
                move_result = future.result()
            except Exception as e:
                print(f"Error in AI task for minion {minion_id}: {e}") # Proper logging recommended
                move_result = {
                    "move": "stay",
                    "dialogue": "Hmm, I'm a bit stuck.",
                    "thought": f"An error occurred: {str(e)[:50]}...",
                    "strategy": "Defaulting to a safe move."
                }
            finally:
                self.pending_moves[minion_id] = move_result
                with self.completion_lock:
                    self.ai_threads_completed += 1

        # Schedule coroutines on the existing event loop for each team's minion
        # Pass copies of mutable arguments (snapshots) to ensure thread safety if they were modified by minion internally
        # (though decide_move should ideally not modify its input snapshots)
        future1 = asyncio.run_coroutine_threadsafe(
            self.team1_minion_1.decide_move(
                [row[:] for row in current_grid_snapshot], # Fresh copy of grid snapshot
                self.ai_service,
                list(collected_items_team1_snapshot) if collected_items_team1_snapshot else None,
                list(target_items_team1_snapshot) if target_items_team1_snapshot else None
            ),
            self.async_loop
        )
        future1.add_done_callback(lambda f: _ai_task_callback(f, 1))

        future2 = asyncio.run_coroutine_threadsafe(
            self.team1_minion_2.decide_move(
                [row[:] for row in current_grid_snapshot], # Fresh copy of grid snapshot
                self.ai_service,
                list(collected_items_team1_snapshot) if collected_items_team1_snapshot else None,
                list(target_items_team1_snapshot) if target_items_team1_snapshot else None
            ),
            self.async_loop
        )
        future2.add_done_callback(lambda f: _ai_task_callback(f, 2))

        future3 = asyncio.run_coroutine_threadsafe(
            self.team2_minion_1.decide_move(
                [row[:] for row in current_grid_snapshot], # Fresh copy of grid snapshot
                self.ai_service,
                list(collected_items_team2_snapshot) if collected_items_team2_snapshot else None,
                list(target_items_team2_snapshot) if target_items_team2_snapshot else None
            ),
            self.async_loop
        )
        future3.add_done_callback(lambda f: _ai_task_callback(f, 3))

        future4 = asyncio.run_coroutine_threadsafe(
            self.team2_minion_2.decide_move(
                [row[:] for row in current_grid_snapshot], # Fresh copy of grid snapshot
                self.ai_service,
                list(collected_items_team2_snapshot) if collected_items_team2_snapshot else None,
                list(target_items_team2_snapshot) if target_items_team2_snapshot else None
            ),
            self.async_loop
        )
        future4.add_done_callback(lambda f: _ai_task_callback(f, 4))

    def send_gesture(self, team_id, gesture):
        """Send a gesture from the guide to the minion and store it."""
        self.current_gestures[team_id] = f"Team {team_id} Guide: {gesture}"
        
        if team_id == 1:
            self.team1_minion_1.receive_gesture(gesture)
            self.team1_minion_2.receive_gesture(gesture)
        else:
            self.team2_minion_1.receive_gesture(gesture)
            self.team2_minion_2.receive_gesture(gesture)
                
    def process_simultaneous_moves(self, decision_team1_1, decision_team1_2, decision_team2_1, decision_team2_2):
        """Process moves for both teams, handle collisions, and update game state."""
        if self.game_state.game_over:
            return

        move_action_team1_1 = decision_team1_1.get("move", "stay")
        dialogue_team1_1 = decision_team1_1.get("dialogue", "...")
        thought_team1_1 = decision_team1_1.get("thought", "...")

        move_action_team1_2 = decision_team1_2.get("move", "stay")
        dialogue_team1_2 = decision_team1_2.get("dialogue", "...")
        thought_team1_2 = decision_team1_2.get("thought", "...")

        move_action_team2_1 = decision_team2_1.get("move", "stay")
        dialogue_team2_1 = decision_team2_1.get("dialogue", "...")
        thought_team2_1 = decision_team2_1.get("thought", "...")
        
        move_action_team2_2 = decision_team2_2.get("move", "stay")
        dialogue_team2_2 = decision_team2_2.get("dialogue", "...")
        thought_team2_2 = decision_team2_2.get("thought", "...")

        # Store last moves and UI dialogues/thoughts
        self.team1_1_last_move = move_action_team1_1
        self.ui_manager.team1_minion_1_dialogue += dialogue_team1_1
        self.ui_manager.team1_minion_1_thought += thought_team1_1

        self.team1_2_last_move = move_action_team1_2
        self.ui_manager.team1_minion_2_dialogue += dialogue_team1_2
        self.ui_manager.team1_minion_2_thought += thought_team1_2

        self.team2_1_last_move = move_action_team2_1
        self.ui_manager.team2_minion_1_dialogue += dialogue_team2_1
        self.ui_manager.team2_minion_1_thought += thought_team2_1

        self.team2_2_last_move = move_action_team2_2
        self.ui_manager.team2_minion_2_dialogue += dialogue_team2_2
        self.ui_manager.team2_minion_2_thought += thought_team2_2
        
        # Get current positions (these are lists, so .copy() is important for calculate_new_position)
        pos_team1_1_current = self.game_state.team1_minion_1_pos
        pos_team1_2_current = self.game_state.team1_minion_2_pos
        pos_team2_1_current = self.game_state.team2_minion_1_pos
        pos_team2_2_current = self.game_state.team2_minion_2_pos

        # Calculate tentative new positions
        new_pos_team1_1 = self.game_state.calculate_new_position(pos_team1_1_current.copy(), move_action_team1_1)
        new_pos_team1_2 = self.game_state.calculate_new_position(pos_team1_2_current.copy(), move_action_team1_2)
        new_pos_team2_1 = self.game_state.calculate_new_position(pos_team2_1_current.copy(), move_action_team2_1)
        new_pos_team2_2 = self.game_state.calculate_new_position(pos_team2_2_current.copy(), move_action_team2_2)

        # Handle collisions: if minions land on the same spot
        if new_pos_team1_1 == new_pos_team1_2:
            kicked_minion_team = random.choice([1, 2])
            original_collided_pos_info = f" (Collided at {new_pos_team1_1})" # For dialogue
            if kicked_minion_team == 1:
                new_pos_team1 = self.game_state.TEAM1_SPAWN_POS[:] # Use a copy
                self.ui_manager.team1_dialogue += f"{original_collided_pos_info} Kicked back!"
            else: # kicked_minion_team == 2
                new_pos_team2 = self.game_state.TEAM2_SPAWN_POS[:] # Use a copy
                self.ui_manager.team2_dialogue += f"{original_collided_pos_info} Kicked back!"
        
        # Clear old minion positions on the grid.
        # This assumes the spot becomes empty (0). Item collection should have already updated the grid if an item was there.
        if 0 <= pos_team1_1_current[0] < GRID_HEIGHT and 0 <= pos_team1_1_current[1] < GRID_WIDTH:
            if self.game_state.grid[pos_team1_1_current[0]][pos_team1_1_current[1]] == TEAM1_MINION_1: # Minion 1 marker
                self.game_state.grid[pos_team1_1_current[0]][pos_team1_1_current[1]] = 0
        
        if 0 <= pos_team1_2_current[0] < GRID_HEIGHT and 0 <= pos_team1_2_current[1] < GRID_WIDTH:
            if self.game_state.grid[pos_team1_2_current[0]][pos_team1_2_current[1]] == TEAM1_MINION_2: # Minion 2 marker
                self.game_state.grid[pos_team1_2_current[0]][pos_team1_2_current[1]] = 0

        if 0 <= pos_team2_1_current[0] < GRID_HEIGHT and 0 <= pos_team2_1_current[1] < GRID_WIDTH:
            if self.game_state.grid[pos_team2_1_current[0]][pos_team2_1_current[1]] == TEAM2_MINION_1: # Minion 2 marker
                self.game_state.grid[pos_team2_1_current[0]][pos_team2_1_current[1]] = 0

        if 0 <= pos_team2_2_current[0] < GRID_HEIGHT and 0 <= pos_team2_2_current[1] < GRID_WIDTH:
            if self.game_state.grid[pos_team2_2_current[0]][pos_team2_2_current[1]] == TEAM2_MINION_2: # Minion 2 marker
                self.game_state.grid[pos_team2_2_current[0]][pos_team2_2_current[1]] = 0
        
        # Update state for Team 1
        self.game_state.check_item_collection(new_pos_team1_1, self.game_state.team1_collected)
        self.game_state.team1_minion_1_pos = new_pos_team1_1 # Update state tracking
        self.team1_minion_1.grid_pos = new_pos_team1_1      # Update minion object's internal position
        self.team1_guide.update_collected(self.game_state.team1_collected)
        if 0 <= new_pos_team1_1[0] < GRID_HEIGHT and 0 <= new_pos_team1_1[1] < GRID_WIDTH:
            self.game_state.grid[new_pos_team1_1[0]][new_pos_team1_1[1]] = TEAM1_MINION_1 # Place Minion 1 marker
        
        self.game_state.check_item_collection(new_pos_team1_2, self.game_state.team1_collected)
        self.game_state.team1_minion_2_pos = new_pos_team1_2 # Update state tracking
        self.team1_minion_2.grid_pos = new_pos_team1_2      # Update minion object's internal position
        self.team1_guide.update_collected(self.game_state.team1_collected)
        if 0 <= new_pos_team1_2[0] < GRID_HEIGHT and 0 <= new_pos_team1_2[1] < GRID_WIDTH:
            self.game_state.grid[new_pos_team1_2[0]][new_pos_team1_2[1]] = TEAM1_MINION_2 # Place Minion 2 marker

        # Update state for Team 2
        self.game_state.check_item_collection(new_pos_team2_1, self.game_state.team2_collected)
        self.game_state.team2_minion_1_pos = new_pos_team2_1 # Update state tracking
        self.team2_minion_1.grid_pos = new_pos_team2_1      # Update minion object's internal position
        self.team2_guide.update_collected(self.game_state.team2_collected)
        if 0 <= new_pos_team2_1[0] < GRID_HEIGHT and 0 <= new_pos_team2_1[1] < GRID_WIDTH:
            self.game_state.grid[new_pos_team2_1[0]][new_pos_team2_1[1]] = TEAM2_MINION_1 # Place Minion 1 marker

        self.game_state.check_item_collection(new_pos_team2_2, self.game_state.team2_collected)
        self.game_state.team2_minion_2_pos = new_pos_team2_2 # Update state tracking
        self.team2_minion_2.grid_pos = new_pos_team2_2      # Update minion object's internal position
        self.team2_guide.update_collected(self.game_state.team2_collected)
        if 0 <= new_pos_team2_2[0] < GRID_HEIGHT and 0 <= new_pos_team2_2[1] < GRID_WIDTH:
            self.game_state.grid[new_pos_team2_2[0]][new_pos_team2_2[1]] = TEAM2_MINION_2 # Place Minion 2 marker

        # Check win conditions (this might need to handle simultaneous wins if applicable)
        self.game_state.check_win_conditions()
        
        # Move to next turn/round (increments turn counter, etc.)
        self.game_state.next_turn()

    def query_openai(self, frame_rgb):
        """Send the captured frame to the gesture recognizer and process the result"""
        # Create a preview of the captured frame
        webcam_display = self.ui_manager.get_webcam_display()
        
        # The frame_rgb received here is already rotated (original width becomes height, original height becomes width).
        # To split the *original* view vertically (left/right halves), we need to split the *rotated* frame horizontally (top/bottom halves).
        
        processed_frame_for_api = frame_rgb.copy() 
        original_width_as_rotated_height, _original_height_as_rotated_width, _channels = processed_frame_for_api.shape
    
        # Pass the correctly cropped frame to the gesture recognizer
        preview_surface_team1 = self.gesture_recognizer.capture_frame(1, processed_frame_for_api[original_width_as_rotated_height // 2:, :, :])
        preview_surface_team2 = self.gesture_recognizer.capture_frame(2, processed_frame_for_api[:original_width_as_rotated_height // 2, :, :])
        
        if preview_surface_team1 is None:
            print("Error: Could not create preview surface for AI query in Game.query_openai.")
            webcam_display.set_captured_preview_team1(None)
            return
        
        if preview_surface_team2 is None:
            print("Error: Could not create preview surface for AI query in Game.query_openai.")
            webcam_display.set_captured_preview_team2(None)
            return
        
        webcam_display.set_captured_preview_team1(preview_surface_team1)
        webcam_display.set_captured_preview_team2(preview_surface_team2)
        
        # Analyze the gesture using the frame stored by capture_frame (which is now the correctly cropped version)
        future_team1 = asyncio.run_coroutine_threadsafe(
            self.gesture_recognizer.analyze_gesture(1), self.async_loop)

        future_team2 = asyncio.run_coroutine_threadsafe(
            self.gesture_recognizer.analyze_gesture(2), self.async_loop)

        # Handle the result asynchronously
        def process_analysis_result(future, team_id):
            try:
                result = future.result()
                facial_expression = result.get("facial_expressions", "Unknown")
                gesture = result.get("gestures", "Unknown")
                
                # Print the complete analysis
                print(f"Analysis result: Facial expression: {facial_expression}, Gesture: {gesture}")
                
                # Get current team's guide
                current_guide = self.team1_guide if team_id == 1 else self.team2_guide
                
                # Send the analysis results to both the current minion and guide
                if team_id == 1:
                    self.team1_minion_1.receive_analysis_results(facial_expression, gesture)
                    self.team1_minion_2.receive_analysis_results(facial_expression, gesture)
                elif team_id == 2:
                    self.team2_minion_1.receive_analysis_results(facial_expression, gesture)
                    self.team2_minion_2.receive_analysis_results(facial_expression, gesture)
                
                understood_guide = current_guide.receive_detection_results(facial_expression, gesture)
                
                if understood_guide:
                    print(f"Team {team_id} minion understood the gesture")
                else:
                    print(f"Team {team_id} minion ignored the unclear gesture")
                    
                # Add team info to the gesture display
                display_text = f"Team {team_id} - Expression: {facial_expression}\nGesture: {gesture}"
                
                # Update the webcam display directly
                self.ui_manager.webcam_display.set_analysis_text(display_text)
                
            except Exception as e:
                print(f"Error processing analysis result: {e}")
                
        future_team1.add_done_callback(lambda f: process_analysis_result(f, 1))
        future_team2.add_done_callback(lambda f: process_analysis_result(f, 2))

    def on_video_playback_complete(self):
        """Handle completion of a video playback"""
        # This gets called when the video is finished playing
        # We can use this to do any cleanup or additional effects after the video
        print("Video playback complete - Game notified")
