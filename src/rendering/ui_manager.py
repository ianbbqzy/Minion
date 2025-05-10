"""
UI Manager - responsible for managing all UI components and layout
"""
import pygame
import os
import random
from src.utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, GRID_WIDTH, GRID_HEIGHT,
    WEBCAM_WIDTH, WEBCAM_HEIGHT, PREVIEW_GAP, GRADIENT_COLORS
)
from src.rendering.ui import Button, DialogueBox, WebcamDisplay, TeamView, create_gradient_background

class UIManager:
    """Manages all UI components and their layout"""
    def __init__(self, game):
        self.game = game
        
        # Store references to game resources
        self.sprites = game.sprites
        self.font = game.font
        self.small_font = game.small_font
        self.thought_font = game.thought_font
        self.btn_font = game.btn_font
        
        # Create gradient background
        self.gradient_bg = create_gradient_background(GRADIENT_COLORS)
        
        # Store separate dialogue and thoughts for each team
        self.team1_minion_1_dialogue = ""
        self.team1_minion_1_thought = ""
        self.team1_minion_2_dialogue = ""
        self.team1_minion_2_thought = ""
        self.team2_minion_1_dialogue = ""
        self.team2_minion_1_thought = ""
        self.team2_minion_2_dialogue = ""
        self.team2_minion_2_thought = ""
        
        # Store previous dialogue and thoughts to calculate deltas
        self.prev_team1_minion_1_dialogue = ""
        self.prev_team1_minion_1_thought = ""
        self.prev_team1_minion_2_dialogue = ""
        self.prev_team1_minion_2_thought = ""
        self.prev_team2_minion_1_dialogue = ""
        self.prev_team2_minion_1_thought = ""
        self.prev_team2_minion_2_dialogue = ""
        self.prev_team2_minion_2_thought = ""
        
        # Track AI turns for step counting
        self.ai_turn_count = 0
        self.last_ai_thinking = False
        
        # Initialize UI components
        self.init_layout()
        
        # Initialize video elements
        self.setup_video_elements()
        
    def init_layout(self):
        """Initialize the layout of all UI components"""
        # Calculate board position to center it - reduce top padding
        self.BOARD_X = (SCREEN_WIDTH - (GRID_WIDTH * TILE_SIZE)) // 2
        self.BOARD_Y = 30  # Reduced from 50 to 30
        
        # Calculate sizes and positions for the team panels
        panel_width = 300
        # Make panels much taller to fill most of the screen
        panel_height = SCREEN_HEIGHT - 60  # Leave 30px margin on top and bottom
        
        # Account for the additional 100 pixels added in TeamView constructor
        actual_panel_width = panel_width + 100
        
        # Left team panel (Team 1) - Positioned further left to avoid overlap with the board
        team1_panel_x = self.BOARD_X - actual_panel_width - 20
        team1_panel_y = 30  # Align with top margin
        
        # Right team panel (Team 2) - Keep same position, it's already positioned correctly
        team2_panel_x = self.BOARD_X + (GRID_WIDTH * TILE_SIZE) + 20
        team2_panel_y = 30  # Align with top margin
        
        # Create team panels
        self.team1_panel = TeamView(
            1, team1_panel_x, team1_panel_y, panel_width, panel_height,
            self.font, self.small_font, self.small_font, self.sprites
        )
        
        self.team2_panel = TeamView(
            2, team2_panel_x, team2_panel_y, panel_width, panel_height,
            self.font, self.small_font, self.small_font, self.sprites
        )
        
        # Create dialogue box (legacy, still needed for some functionality)
        self.dialogue_box = DialogueBox(self.font, self.thought_font)
        
        # Calculate button positions - reduce spacing
        button_y = self.BOARD_Y + (GRID_HEIGHT * TILE_SIZE) + 20  # Reduced from 30 to 20
        button_width = 200
        button_height = 50  # Reduced from 60 to 50
        button_spacing = 30
        
        # Center buttons horizontally below the board
        ai_button_x = (SCREEN_WIDTH // 2) - button_width - (button_spacing // 2)
        webcam_button_x = (SCREEN_WIDTH // 2) + (button_spacing // 2)
        
        # Create AI button
        self.ai_button = Button(
            pygame.Rect(ai_button_x, button_y, button_width, button_height),
            "Take AI Turn",
            self.btn_font
        )

        # Create Start count button
        self.webcam_button = Button(
            pygame.Rect(webcam_button_x, button_y, button_width, button_height),
            "Pause",
            self.btn_font
        )
        
        # Position webcam display below buttons - reduce spacing
        webcam_y = button_y + button_height + 20  # Reduced from 30 to 20
        webcam_x = (SCREEN_WIDTH - (WEBCAM_WIDTH * 2) - 30) // 2  # Center both webcam views

        self.webcam_display = WebcamDisplay(
            webcam_x,
            webcam_y,
            WEBCAM_WIDTH, 
            WEBCAM_HEIGHT,
            self.btn_font
        )
    
    def update(self, game_state, dialogue, thought, team1_1_last_move, team1_2_last_move, team2_1_last_move, team2_2_last_move, current_team, live_frame_surface, webcam_available, ai_thinking):
        """Update all UI components based on game state"""
        # NOTE: We don't set team dialogues/thoughts here anymore - they are set directly in Game.take_turn()
        # This avoids issues with them getting mixed up
        
        # Track AI turn transitions to increment step counter
        ai_turn_completed = self.last_ai_thinking and not ai_thinking
        self.last_ai_thinking = ai_thinking
        
        # Calculate new dialogue/thought content (delta from previous)
        new_team1_minion_1_dialogue = self.team1_minion_1_dialogue[len(self.prev_team1_minion_1_dialogue):]
        new_team1_minion_1_thought = self.team1_minion_1_thought[len(self.prev_team1_minion_1_thought):]
        new_team1_minion_2_dialogue = self.team1_minion_2_dialogue[len(self.prev_team1_minion_2_dialogue):]
        new_team1_minion_2_thought = self.team1_minion_2_thought[len(self.prev_team1_minion_2_thought):]
        
        new_team2_minion_1_dialogue = self.team2_minion_1_dialogue[len(self.prev_team2_minion_1_dialogue):]
        new_team2_minion_1_thought = self.team2_minion_1_thought[len(self.prev_team2_minion_1_thought):]
        new_team2_minion_2_dialogue = self.team2_minion_2_dialogue[len(self.prev_team2_minion_2_dialogue):]
        new_team2_minion_2_thought = self.team2_minion_2_thought[len(self.prev_team2_minion_2_thought):]
        
        # Only increment step counter if we've completed an AI turn AND we have actual new content
        has_team1_content = any([new_team1_minion_1_dialogue, new_team1_minion_1_thought, 
                                team1_1_last_move, new_team1_minion_2_dialogue, 
                                new_team1_minion_2_thought, team1_2_last_move])
                                
        has_team2_content = any([new_team2_minion_1_dialogue, new_team2_minion_1_thought, 
                                team2_1_last_move, new_team2_minion_2_dialogue, 
                                new_team2_minion_2_thought, team2_2_last_move])
        
        # Debug prints to trace the step creation logic
        if ai_turn_completed:
            print(f"AI turn completed. Has content: Team1={has_team1_content}, Team2={has_team2_content}")
            print(f"Team1 moves: '{team1_1_last_move}', '{team1_2_last_move}'")
            print(f"Team2 moves: '{team2_1_last_move}', '{team2_2_last_move}'")
        
        if ai_turn_completed and (has_team1_content or has_team2_content):
            self.ai_turn_count += 1
            print(f"Creating new step {self.ai_turn_count}")
        
        # Update team panels with their respective dialogue and thoughts
        self.team1_panel.update(
            game_state.team1_targets, 
            game_state.team1_collected,
            new_team1_minion_1_thought,  # Pass only new content
            new_team1_minion_1_dialogue, # Pass only new content
            team1_1_last_move,
            new_team1_minion_2_thought,
            new_team1_minion_2_dialogue,
            team1_2_last_move,
            self.ai_turn_count,  # Pass current AI turn count
            has_team1_content and ai_turn_completed  # Only add history if we have content and completed a turn
        )
        
        self.team2_panel.update(
            game_state.team2_targets, 
            game_state.team2_collected,
            new_team2_minion_1_thought,  # Pass only new content
            new_team2_minion_1_dialogue, # Pass only new content
            team2_1_last_move,
            new_team2_minion_2_thought,
            new_team2_minion_2_dialogue,
            team2_2_last_move,
            self.ai_turn_count,  # Pass current AI turn count
            has_team2_content and ai_turn_completed  # Only add history if we have content and completed a turn
        )
        
        # Save current dialogue/thoughts as previous for next update
        self.prev_team1_minion_1_dialogue = self.team1_minion_1_dialogue
        self.prev_team1_minion_1_thought = self.team1_minion_1_thought
        self.prev_team1_minion_2_dialogue = self.team1_minion_2_dialogue
        self.prev_team1_minion_2_thought = self.team1_minion_2_thought
        
        self.prev_team2_minion_1_dialogue = self.team2_minion_1_dialogue
        self.prev_team2_minion_1_thought = self.team2_minion_1_thought
        self.prev_team2_minion_2_dialogue = self.team2_minion_2_dialogue
        self.prev_team2_minion_2_thought = self.team2_minion_2_thought
        
        # Update video playback
        self.update_video_playback()
        
        # Update confetti
        self.update_confetti()
        
        # Update button states
        mouse_pos = pygame.mouse.get_pos()
        self.ai_button.update(mouse_pos)
        self.webcam_button.update(mouse_pos)
    
    def draw(self, screen, game_state, live_frame_surface, webcam_available, ai_thinking):
        """Draw all UI components to the screen"""
        # Draw gradient background
        screen.blit(self.gradient_bg, (0, 0))
        
        # Draw team panels
        self.team1_panel.draw(screen)
        self.team2_panel.draw(screen)
        
        # Draw AI button
        self.ai_button.draw(screen)
        
        # Draw webcam button
        self.webcam_button.draw(screen)
        
        # Draw the live webcam feed or a placeholder
        if live_frame_surface:
            self.webcam_display.draw_camera_feed(screen, live_frame_surface)
        elif webcam_available:
            self.webcam_display.draw_placeholder(screen, "Camera Error")
        else:
            self.webcam_display.draw_placeholder(screen, "No Camera")
        
        # Draw webcam preview
        self.webcam_display.draw_preview(screen)
        
        # Draw video overlay on the specific tile if playing
        if self.playing_video and self.video_surface and self.video_tile_pos:
            # Calculate the pixel position of the tile
            tile_x = self.game.BOARD_X + self.video_tile_pos[1] * TILE_SIZE
            tile_y = self.game.BOARD_Y + self.video_tile_pos[0] * TILE_SIZE
            
            # Draw the video surface at the tile position
            screen.blit(self.video_surface, (tile_x, tile_y))
        
        # Draw confetti
        self.draw_confetti(screen)
        
        # Draw AI thinking indicator
        if ai_thinking:
            thinking_text = self.font.render("Thinking...", True, (255, 255, 255))
            thinking_rect = thinking_text.get_rect(center=(SCREEN_WIDTH//2, self.BOARD_Y - 30))
            screen.blit(thinking_text, thinking_rect)
        
        # If game is over, draw game over screen
        if game_state.game_over:
            # This would be handled by the board renderer, not here
            pass
            
    def is_ai_button_clicked(self, pos):
        """Check if the AI button was clicked"""
        return self.ai_button.is_clicked(pos)
    
    def is_webcam_button_clicked(self, pos):
        """Check if the webcam button was clicked"""
        return self.webcam_button.is_clicked(pos)
        
    def get_webcam_display(self):
        """Get the webcam display for the game to use"""
        return self.webcam_display 

    def setup_video_elements(self):
        """Initialize video playback and confetti elements"""
        # Video playback control
        self.playing_video = False
        self.video_team = None
        self.video_timer = 0
        self.video_surface = None
        self.video_tile_pos = None
        
        # Load minion celebration videos from minions folder
        self.videos = {
            1: os.path.join("assets", "minions", "videos", "green.mp4"),
            2: os.path.join("assets", "minions", "videos", "pink.mp4")
        }
        
        
        # Confetti particles
        self.confetti_particles = []
        self.confetti_active = False
        self.confetti_start_time = 0
        self.confetti_max_duration = 2000  # 2 seconds max 

    def start_video_playback(self, team_id, tile_pos):
        """Start video playback for the given team and generate confetti"""
        # Clean up any existing video playback first
        self.clean_up_video()
        
        self.playing_video = True
        self.video_team = team_id
        self.video_timer = 0
        self.video_tile_pos = tile_pos
        
        # Create confetti around the specific tile
        self.generate_confetti(tile_pos)
        
        # Load the appropriate video using pygame movie
        try:
            video_path = self.videos[team_id]
            # Using cv2 to handle the video frames
            import cv2
            print(f"Starting video playback: {video_path}")
            self.video_capture = cv2.VideoCapture(video_path)
            if not self.video_capture.isOpened():
                print(f"Error: Could not open video {video_path}")
                self.playing_video = False
        except Exception as e:
            print(f"Error loading video: {e}")
            self.playing_video = False
    
    def generate_confetti(self, tile_pos):
        """Generate confetti particles around a specific tile"""
        self.confetti_active = True
        self.confetti_particles = []
        self.confetti_start_time = pygame.time.get_ticks()
        
        # Calculate the pixel position of the tile
        tile_x = self.BOARD_X + tile_pos[1] * TILE_SIZE
        tile_y = self.BOARD_Y + tile_pos[0] * TILE_SIZE
        
        # Create multiple confetti particles around the tile
        for _ in range(50):
            # Generate particles within a small radius around the tile
            particle = {
                'x': random.randint(tile_x - TILE_SIZE//2, tile_x + TILE_SIZE + TILE_SIZE//2),
                'y': random.randint(tile_y - TILE_SIZE//2, tile_y + TILE_SIZE + TILE_SIZE//2),
                'size': random.randint(3, 8),
                'color': (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                ),
                'speed_y': random.uniform(0.5, 2.0),  # Vertical speed
                'speed_x': random.uniform(-1.0, 1.0), # Horizontal speed
                'rotation': random.uniform(0, 360),
                'rotation_speed': random.uniform(-8, 8)  # Rotation speed
            }
            self.confetti_particles.append(particle)
    
    def update_video_playback(self):
        """Update video playback state"""
        if not self.playing_video or not hasattr(self, 'video_capture') or self.video_capture is None:
            return
            
        # Read the next frame from the video
        import cv2
        import numpy as np
        
        try:
            ret, frame = self.video_capture.read()
            
            if ret:
                # Resize the frame to the size of a single tile
                frame = cv2.resize(frame, (TILE_SIZE, TILE_SIZE))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                self.video_surface = pygame.surfarray.make_surface(np.flipud(frame))
            else:
                # Video finished or error occurred, clean up
                print("Video playback ended")
                self.video_capture.release()
                self.playing_video = False
                self.video_surface = None
                
                # Clear confetti when video ends
                self.confetti_active = False
                self.confetti_particles = []
                
                # Signal the game that the video is done
                self.game.on_video_playback_complete()
        except Exception as e:
            print(f"Error during video playback: {e}")
            self.clean_up_video()
    
    def update_confetti(self):
        """Update confetti particles"""
        if not self.confetti_active:
            return
            
        # Check for timeout
        current_time = pygame.time.get_ticks()
        if current_time - self.confetti_start_time > self.confetti_max_duration:
            self.confetti_active = False
            self.confetti_particles = []
            return
            
        for particle in self.confetti_particles[:]:
            # Update position
            particle['y'] += particle['speed_y']
            particle['x'] += particle['speed_x']
            
            # Update rotation
            particle['rotation'] += particle['rotation_speed']
            
            # Remove particles that have fallen off the screen
            if particle['y'] > SCREEN_HEIGHT:
                self.confetti_particles.remove(particle)
                
        # If all particles are gone, confetti is no longer active
        if not self.confetti_particles:
            self.confetti_active = False
    
    def draw_confetti(self, screen):
        """Draw confetti particles"""
        if not self.confetti_active:
            return
            
        for particle in self.confetti_particles:
            # Create a surface for the particle
            surf = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
            pygame.draw.rect(surf, particle['color'], (0, 0, particle['size'], particle['size']))
            
            # Rotate the surface
            rotated_surf = pygame.transform.rotate(surf, particle['rotation'])
            
            # Draw the rotated surface
            screen.blit(rotated_surf, (particle['x'], particle['y']))
    
    def clean_up_video(self):
        """Clean up video resources"""
        try:
            if self.playing_video and hasattr(self, 'video_capture') and self.video_capture:
                self.video_capture.release()
                print("Video resources released")
        except Exception as e:
            print(f"Error cleaning up video: {e}")
        finally:
            # Always reset these attributes even if there was an error
            self.playing_video = False
            self.video_surface = None
            self.confetti_active = False
            self.confetti_particles = []
            if hasattr(self, 'video_capture'):
                self.video_capture = None
    
    def draw_background(self, screen):
        """Draw only the gradient background"""
        screen.blit(self.gradient_bg, (0, 0))
    
    def draw_elements(self, screen, game_state, live_frame_surface, webcam_available, ai_thinking):
        """Draw UI elements without the background"""
        # Draw team panels
        self.team1_panel.draw(screen)
        self.team2_panel.draw(screen)
        
        # Draw AI button
        self.ai_button.draw(screen)
        
        # Draw webcam button
        self.webcam_button.draw(screen)
        
        # Draw the live webcam feed or a placeholder
        if live_frame_surface:
            self.webcam_display.draw_camera_feed(screen, live_frame_surface)
        elif webcam_available:
            self.webcam_display.draw_placeholder(screen, "Camera Error")
        else:
            self.webcam_display.draw_placeholder(screen, "No Camera")
        
        # Draw webcam preview
        self.webcam_display.draw_preview(screen)
        
        # Draw video overlay on the specific tile if playing
        if self.playing_video and self.video_surface and self.video_tile_pos:
            # Calculate the pixel position of the tile
            tile_x = self.game.BOARD_X + self.video_tile_pos[1] * TILE_SIZE
            tile_y = self.game.BOARD_Y + self.video_tile_pos[0] * TILE_SIZE
            
            # Draw the video surface at the tile position
            screen.blit(self.video_surface, (tile_x, tile_y))
        
        # Draw confetti
        self.draw_confetti(screen)
        
        # Draw AI thinking indicator
        if ai_thinking:
            thinking_text = self.font.render("Thinking...", True, (255, 255, 255))
            thinking_rect = thinking_text.get_rect(center=(SCREEN_WIDTH//2, self.BOARD_Y - 30))
            screen.blit(thinking_text, thinking_rect) 

    def reset_tracking(self):
        """Reset step counter and dialogue tracking for a new game"""
        self.ai_turn_count = 0
        self.last_ai_thinking = False
        
        # Reset previous dialogue/thought tracking
        self.prev_team1_minion_1_dialogue = ""
        self.prev_team1_minion_1_thought = ""
        self.prev_team1_minion_2_dialogue = ""
        self.prev_team1_minion_2_thought = ""
        self.prev_team2_minion_1_dialogue = ""
        self.prev_team2_minion_1_thought = ""
        self.prev_team2_minion_2_dialogue = ""
        self.prev_team2_minion_2_thought = "" 