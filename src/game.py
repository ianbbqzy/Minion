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
        self.BOARD_Y = 50  # Top padding
        
        # Initialize components
        self.initialize_components()
        
        # Game state
        self.game_state = GameState()
        
        # Initialize game objects
        self.initialize_game_objects()
        
        # AI turn controls
        self.ai_thinking = False
        self.ai_thinking_time = 0
        self.pending_move = None
        
        # Dialogue and gesture displays
        self.current_gesture = ""
        
        # Team panel data
        self.team1_last_move = ""
        self.team2_last_move = ""
        
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
        
        self.team1_minion = Minion(1, self.game_state.team1_minion_pos, team1_personality)
        self.team2_minion = Minion(2, self.game_state.team2_minion_pos, team2_personality)
                
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
        self.ui_manager.dialogue_box.dialogue = ""
        self.ui_manager.dialogue_box.thought = ""
        self.current_gesture = ""
        
        # Reset team move info
        self.team1_last_move = ""
        self.team2_last_move = ""
        
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
        self.ui_manager.dialogue_box.update()
        
        # AI is thinking if the flag is set (thread is running)
        if self.ai_thinking:
            self.ai_thinking_time += self.clock.get_time()
        
        # Check if the AI thread has finished and populated pending_move
        if self.pending_move is not None:
            self.take_turn(self.pending_move)
            self.pending_move = None
            self.ai_thinking = False
        
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
                self.ui_manager.webcam_display.last_frame = frame
            else:
                # Indicate no current frame available for drawing
                self.live_pygame_frame_surface = None
        else:
            # Indicate no current frame available for drawing
            self.live_pygame_frame_surface = None
            
        # Update UI manager - no longer passing dialogue/thought as they're set directly in take_turn
        self.ui_manager.update(
            self.game_state, 
            "", # Empty dialogue, not used anymore
            "", # Empty thought, not used anymore
            self.team1_last_move, 
            self.team2_last_move, 
            self.game_state.current_team,
            self.live_pygame_frame_surface,
            self.webcam_available,
            self.ai_thinking
        )
    
    def draw(self):
        """Render the game"""
        # Draw UI components (background, panels, buttons, webcam)
        self.ui_manager.draw(
            self.screen, 
            self.game_state, 
            self.live_pygame_frame_surface, 
            self.webcam_available, 
            self.ai_thinking
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
    
    def start_ai_turn(self):
        """Start the AI thinking process for the current team by launching a thread.
        The thread will call decide_move and populate self.pending_move.
        Also, send gesture to the minion."""
        if self.game_state.game_over or self.ai_thinking: # Prevent starting a new AI turn if one is already in progress
            return
            
        self.ai_thinking = True
        self.ai_thinking_time = 0
        self.pending_move = None # Ensure no stale pending move

        active_minion = None
        collected_items_snapshot = None
        target_items_snapshot = None
        current_grid_snapshot = [row[:] for row in self.game_state.grid] # Snapshot of the grid

        # Decide which gesture to send and identify active minion/items
        if self.game_state.current_team == 1:
            gesture = self.team1_guide.decide_gesture(
                current_grid_snapshot, # Use snapshot for guide decision too
                self.game_state.team1_minion_pos, 
                self.game_state.team2_minion_pos
            )
            self.send_gesture(1, gesture) # This updates minion.last_gesture_received
            active_minion = self.team1_minion
            collected_items_snapshot = list(self.game_state.team1_collected) # Snapshot
            if self.game_state.team1_targets:
                target_items_snapshot = list(self.game_state.team1_targets) # Snapshot
        else:
            gesture = self.team2_guide.decide_gesture(
                current_grid_snapshot, # Use snapshot
                self.game_state.team2_minion_pos,
                self.game_state.team1_minion_pos
            )
            self.send_gesture(2, gesture) # This updates minion.last_gesture_received
            active_minion = self.team2_minion
            collected_items_snapshot = list(self.game_state.team2_collected) # Snapshot
            if self.game_state.team2_targets:
                target_items_snapshot = list(self.game_state.team2_targets) # Snapshot
        
        # Define the task for the AI thread
        def _ai_task_wrapper():
            try:
                # active_minion.decide_move is async and will use its own last_gesture_received
                move_result = asyncio.run(active_minion.decide_move(
                    current_grid_snapshot,    # Pass snapshot of grid
                    self.ai_service,          # AIService instance
                    collected_items_snapshot, # Pass snapshot of collected items
                    target_items_snapshot     # Pass snapshot of target items
                ))
                self.pending_move = move_result
            except Exception as e:
                # Log the error and set a fallback move
                print(f"Error in AI thread: {e}") # Replace with proper logging
                self.pending_move = {
                    "move": "stay",
                    "dialogue": "Hmm, I'm a bit stuck.",
                    "thought": f"An error occurred: {str(e)[:50]}...", # Keep thought brief
                    "strategy": "Defaulting to a safe move."
                }
            # self.ai_thinking will be set to False by take_turn() when self.pending_move is processed.

        # Create and start the AI thread
        ai_thread = threading.Thread(target=_ai_task_wrapper)
        ai_thread.daemon = True  # Allow main program to exit even if thread is running
        ai_thread.start()
                    
    def send_gesture(self, team_id, gesture):
        """Send a gesture from the guide to the minion"""
        self.current_gesture = f"Team {team_id} Guide: {gesture}"
        
        if team_id == 1:
            # Team 1 Guide sends gesture to Team 1 Minion
            self.team1_minion.receive_gesture(gesture)
        else:
            # Team 2 Guide sends gesture to Team 2 Minion
            self.team2_minion.receive_gesture(gesture)
                
    def take_turn(self, ai_decision_data):
        """Process the current team's move using the data from AI decision."""
        if self.game_state.game_over:
            return
                
        move_action = ai_decision_data.get("move", "stay")
        dialogue = ai_decision_data.get("dialogue", "...")
        thought = ai_decision_data.get("thought", "...")
        
        # Store the move, dialogue and thought directly in UI manager for the correct team
        if self.game_state.current_team == 1:
            self.team1_last_move = move_action
            self.ui_manager.team1_dialogue = dialogue  # Set team-specific dialogue directly
            self.ui_manager.team1_thought = thought    # Set team-specific thought directly
        else:
            self.team2_last_move = move_action
            self.ui_manager.team2_dialogue = dialogue  # Set team-specific dialogue directly
            self.ui_manager.team2_thought = thought    # Set team-specific thought directly
        
        # Set dialogue box for overlay/compatibility
        self.ui_manager.dialogue_box.set_dialogue(dialogue, thought)
        
        current_minion_game_pos = None
        current_minion_collected_items = None
        current_minion_object = None
        current_guide_object = None
        
        if self.game_state.current_team == 1:
            current_minion_game_pos = self.game_state.team1_minion_pos
            current_minion_collected_items = self.game_state.team1_collected
            current_minion_object = self.team1_minion
            current_guide_object = self.team1_guide
        else:
            current_minion_game_pos = self.game_state.team2_minion_pos
            current_minion_collected_items = self.game_state.team2_collected
            current_minion_object = self.team2_minion
            current_guide_object = self.team2_guide
            
        # Calculate new position based on the move action
        new_pos = self.game_state.calculate_new_position(current_minion_game_pos.copy(), move_action)
        
        # Check if there's an item at the new position and update collected items
        self.game_state.check_item_collection(new_pos, current_minion_collected_items)
        
        # Move minion in the game state
        self.game_state.move_minion(current_minion_game_pos, move_action) # This updates current_minion_game_pos in-place
        
        # Update the minion object's internal position
        current_minion_object.grid_pos = current_minion_game_pos
        
        # Update the guide's knowledge of collected items
        current_guide_object.update_collected(current_minion_collected_items)
            
        # Check win conditions
        self.game_state.check_win_conditions()
        
        # Move to next turn
        self.game_state.next_turn()
    
    def query_openai(self, frame_rgb):
        """Send the captured frame to the gesture recognizer and process the result"""
        # Create a preview of the captured frame
        webcam_display = self.ui_manager.get_webcam_display()
        preview_surface = self.gesture_recognizer.capture_frame(frame_rgb.copy())
        
        if preview_surface is None:
            print("Error: Could not create preview surface for AI query in Game.query_openai.")
            webcam_display.set_captured_preview(None)
            return

        webcam_display.set_captured_preview(preview_surface)
        
        # Analyze the gesture
        future = asyncio.run_coroutine_threadsafe(
            self.gesture_recognizer.analyze_gesture(), self.async_loop)

        future.add_done_callback(
        lambda f: print("Detect gesture:", f.result()))
