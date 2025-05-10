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
    BUTTON_COLOR, BUTTON_HOVER_COLOR, GRADIENT_COLORS, EMPTY,
    TEAM1_MINION_1, TEAM1_MINION_2, TEAM2_MINION_1, TEAM2_MINION_2, TEAM1_MINION_1_INSTRUCTIONS, TEAM1_MINION_2_INSTRUCTIONS, TEAM2_MINION_1_INSTRUCTIONS, TEAM2_MINION_2_INSTRUCTIONS, TEAM1_MINION_1_POWER, TEAM1_MINION_2_POWER, TEAM2_MINION_1_POWER, TEAM2_MINION_2_POWER
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

        # Cound down logic 
        self.countdown_active = True
        self.countdown_start_time = pygame.time.get_ticks()
        self.countdown_duration = 5  # seconds

        # Signal  Result
        self.team1_signal = False
        self.team2_signal = False

        self.is_pausing = False
        
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
        
        self.team1_minion_1 = Minion(1, self.game_state.team1_minion_1_pos, TEAM1_MINION_1_POWER, "Team 1 Minion 1", team1_personality, TEAM1_MINION_1_INSTRUCTIONS)
        self.team1_minion_2 = Minion(1, self.game_state.team1_minion_2_pos, TEAM1_MINION_2_POWER, "Team 1 Minion 2", team1_personality, TEAM1_MINION_2_INSTRUCTIONS)
        self.team2_minion_1 = Minion(2, self.game_state.team2_minion_1_pos, TEAM2_MINION_1_POWER, "Team 2 Minion 1", team2_personality, TEAM2_MINION_1_INSTRUCTIONS)
        self.team2_minion_2 = Minion(2, self.game_state.team2_minion_2_pos, TEAM2_MINION_2_POWER, "Team 2 Minion 2", team2_personality, TEAM2_MINION_2_INSTRUCTIONS)
                
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
        
        # Clear team panel history
        self.ui_manager.team1_panel.clear_history()
        self.ui_manager.team2_panel.clear_history()
        
        # Reset UI Manager's step counting and tracking
        self.ui_manager.reset_tracking()
        
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
            self.countdown_active = True
        
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

        # Automate the ai turn when we get both player signals
        if self.team1_signal and self.team2_signal:
            self.start_both_ai_turns()

        # Countdown
        if self.countdown_active and not self.is_pausing:
            elapsed = (pygame.time.get_ticks() - self.countdown_start_time) // 1000
            remaining = max(0, self.countdown_duration - elapsed)

            # Update button label to show countdown
            self.ui_manager.ai_button.text = f"Capturing in {remaining}..."

            if remaining == 0 :
                self.query_openai(self.ui_manager.webcam_display.last_frame.copy())
                self.countdown_start_time = pygame.time.get_ticks()
                self.countdown_active = False
        else:
            self.countdown_start_time = pygame.time.get_ticks()
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

    def state_toggle(self):
        self.is_pausing = not self.is_pausing
        if self.is_pausing :
            self.ui_manager.webcam_button.text = "Resume"
        else:
            self.ui_manager.webcam_button.text = "Pause"
    
    def start_both_ai_turns(self):
        """Start the AI thinking process for both teams simultaneously."""
        if self.game_state.game_over or self.ai_turn_processing:
            return # Prevent starting new AI turns if game over or already processing
            
        self.ai_turn_processing = True
        self.ai_threads_completed = 0
        self.pending_moves = {1: None, 2: None, 3: None, 4: None}
        self.team1_signal = False
        self.team2_signal = False

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
        """Process moves for all teams, handle collisions based on power, and update game state."""
        if self.game_state.game_over:
            return

        # Extract decisions
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

        # Store original current positions (copies)
        orig_pos_t1m1 = self.game_state.team1_minion_1_pos[:]
        orig_pos_t1m2 = self.game_state.team1_minion_2_pos[:]
        orig_pos_t2m1 = self.game_state.team2_minion_1_pos[:]
        orig_pos_t2m2 = self.game_state.team2_minion_2_pos[:]

        # Calculate tentative new positions
        new_pos_team1_1 = self.game_state.calculate_new_position(orig_pos_t1m1[:], move_action_team1_1)
        new_pos_team1_2 = self.game_state.calculate_new_position(orig_pos_t1m2[:], move_action_team1_2)
        new_pos_team2_1 = self.game_state.calculate_new_position(orig_pos_t2m1[:], move_action_team2_1)
        new_pos_team2_2 = self.game_state.calculate_new_position(orig_pos_t2m2[:], move_action_team2_2)

        minions_status = [
            {"id": 1, "minion_obj": self.team1_minion_1, "intended_pos": new_pos_team1_1[:], "spawn_pos": self.game_state.TEAM1_1_SPAWN_POS[:], "final_pos": new_pos_team1_1[:], "marker": TEAM1_MINION_1, "gs_pos_attr": "team1_minion_1_pos", "collected_list": self.game_state.team1_collected, "guide_obj": self.team1_guide, "last_move_attr": "team1_1_last_move", "move_action": move_action_team1_1, "dialogue": dialogue_team1_1, "thought": thought_team1_1, "ui_dialogue_attr": "team1_minion_1_dialogue", "ui_thought_attr": "team1_minion_1_thought"},
            {"id": 2, "minion_obj": self.team1_minion_2, "intended_pos": new_pos_team1_2[:], "spawn_pos": self.game_state.TEAM1_2_SPAWN_POS[:], "final_pos": new_pos_team1_2[:], "marker": TEAM1_MINION_2, "gs_pos_attr": "team1_minion_2_pos", "collected_list": self.game_state.team1_collected, "guide_obj": self.team1_guide, "last_move_attr": "team1_2_last_move", "move_action": move_action_team1_2, "dialogue": dialogue_team1_2, "thought": thought_team1_2, "ui_dialogue_attr": "team1_minion_2_dialogue", "ui_thought_attr": "team1_minion_2_thought"},
            {"id": 3, "minion_obj": self.team2_minion_1, "intended_pos": new_pos_team2_1[:], "spawn_pos": self.game_state.TEAM2_1_SPAWN_POS[:], "final_pos": new_pos_team2_1[:], "marker": TEAM2_MINION_1, "gs_pos_attr": "team2_minion_1_pos", "collected_list": self.game_state.team2_collected, "guide_obj": self.team2_guide, "last_move_attr": "team2_1_last_move", "move_action": move_action_team2_1, "dialogue": dialogue_team2_1, "thought": thought_team2_1, "ui_dialogue_attr": "team2_minion_1_dialogue", "ui_thought_attr": "team2_minion_1_thought"},
            {"id": 4, "minion_obj": self.team2_minion_2, "intended_pos": new_pos_team2_2[:], "spawn_pos": self.game_state.TEAM2_2_SPAWN_POS[:], "final_pos": new_pos_team2_2[:], "marker": TEAM2_MINION_2, "gs_pos_attr": "team2_minion_2_pos", "collected_list": self.game_state.team2_collected, "guide_obj": self.team2_guide, "last_move_attr": "team2_2_last_move", "move_action": move_action_team2_2, "dialogue": dialogue_team2_2, "thought": thought_team2_2, "ui_dialogue_attr": "team2_minion_2_dialogue", "ui_thought_attr": "team2_minion_2_thought"},
        ]

        for data in minions_status:
            setattr(self, data["last_move_attr"], data["move_action"])
            current_dialogue = getattr(self.ui_manager, data["ui_dialogue_attr"], "")
            setattr(self.ui_manager, data["ui_dialogue_attr"], current_dialogue + data["dialogue"]) # Append new dialogue
            current_thought = getattr(self.ui_manager, data["ui_thought_attr"], "")
            setattr(self.ui_manager, data["ui_thought_attr"], current_thought + data["thought"]) # Append new thought

        positions_map = {}
        for i, data in enumerate(minions_status):
            pos_tuple = tuple(data["intended_pos"])
            if pos_tuple not in positions_map:
                positions_map[pos_tuple] = []
            positions_map[pos_tuple].append(i)

        bumped_minion_indices = set()
        for pos_tuple, m_indices in positions_map.items():
            if len(m_indices) > 1:
                colliding_minions_data_indexed = [(idx, minions_status[idx]) for idx in m_indices]
                random.shuffle(colliding_minions_data_indexed)
                colliding_minions_data_indexed.sort(key=lambda item: item[1]["minion_obj"].power, reverse=True)
                
                for i in range(1, len(colliding_minions_data_indexed)):
                    loser_idx, loser_data = colliding_minions_data_indexed[i]
                    bumped_minion_indices.add(loser_idx)
                    collided_at_info = f" (Collided at {list(pos_tuple)})"
                    current_dialogue = getattr(self.ui_manager, loser_data["ui_dialogue_attr"], "")
                    setattr(self.ui_manager, loser_data["ui_dialogue_attr"], current_dialogue + f"{collided_at_info} Lost contest, bumped!")

        resolved_final_positions_for_others = []
        for i, data in enumerate(minions_status):
            if i not in bumped_minion_indices:
                resolved_final_positions_for_others.append(data["final_pos"][:])
        
        sorted_bumped_indices = sorted(list(bumped_minion_indices), key=lambda idx: minions_status[idx]["id"])

        for loser_idx in sorted_bumped_indices:
            loser_data = minions_status[loser_idx]
            grid_snapshot_for_bump = self.game_state.grid # Pass current grid state
            
            new_fallback_pos = self.game_state.find_available_spawn_or_adjacent(
                loser_data["spawn_pos"],
                grid_snapshot_for_bump, 
                resolved_final_positions_for_others 
            )
            loser_data["final_pos"] = new_fallback_pos[:]
            resolved_final_positions_for_others.append(new_fallback_pos[:]) # Add to list for subsequent bumped minions

        original_minion_positions_markers = [
            (orig_pos_t1m1, TEAM1_MINION_1), (orig_pos_t1m2, TEAM1_MINION_2),
            (orig_pos_t2m1, TEAM2_MINION_1), (orig_pos_t2m2, TEAM2_MINION_2),
        ]
        for pos, marker_val in original_minion_positions_markers:
            if 0 <= pos[0] < GRID_HEIGHT and 0 <= pos[1] < GRID_WIDTH:
                if self.game_state.grid[pos[0]][pos[1]] == marker_val:
                    self.game_state.grid[pos[0]][pos[1]] = EMPTY
        
        for data in minions_status:
            final_pos = data["final_pos"]
            self.game_state.check_item_collection(final_pos, data["collected_list"])
            setattr(self.game_state, data["gs_pos_attr"], final_pos[:])
            data["minion_obj"].grid_pos = final_pos[:]
            if 0 <= final_pos[0] < GRID_HEIGHT and 0 <= final_pos[1] < GRID_WIDTH:
                self.game_state.grid[final_pos[0]][final_pos[1]] = data["marker"]

        self.team1_guide.update_collected(self.game_state.team1_collected)
        self.team2_guide.update_collected(self.game_state.team2_collected)

        self.game_state.check_win_conditions()
        if not self.game_state.game_over:
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
                    self.team1_signal = True
                elif team_id == 2:
                    self.team2_minion_1.receive_analysis_results(facial_expression, gesture)
                    self.team2_minion_2.receive_analysis_results(facial_expression, gesture)
                    self.team2_signal = True
                
                self.ui_manager.ai_button.text = "Thinking....."

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
