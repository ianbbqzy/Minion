"""
UI Manager - responsible for managing all UI components and layout
"""
import pygame
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
        self.team1_dialogue = ""
        self.team1_thought = ""
        self.team2_dialogue = ""
        self.team2_thought = ""
        
        # Initialize UI components
        self.init_layout()
        
    def init_layout(self):
        """Initialize the layout of all UI components"""
        # Calculate board position to center it
        self.BOARD_X = (SCREEN_WIDTH - (GRID_WIDTH * TILE_SIZE)) // 2
        self.BOARD_Y = 50  # Top padding
        
        # Calculate sizes and positions for the team panels
        panel_width = 300
        panel_height = GRID_HEIGHT * TILE_SIZE
        
        # Left team panel (Team 1)
        team1_panel_x = self.BOARD_X - panel_width - 20
        team1_panel_y = self.BOARD_Y
        
        # Right team panel (Team 2)
        team2_panel_x = self.BOARD_X + (GRID_WIDTH * TILE_SIZE) + 20
        team2_panel_y = self.BOARD_Y
        
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
        
        # Calculate button positions
        button_y = self.BOARD_Y + (GRID_HEIGHT * TILE_SIZE) + 30
        button_width = 200
        button_height = 60
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

        # Create webcam button
        self.webcam_button = Button(
            pygame.Rect(webcam_button_x, button_y, button_width, button_height),
            "Query with Camera",
            self.btn_font
        )
        
        # Position webcam display below buttons
        webcam_y = button_y + button_height + 30
        webcam_x = (SCREEN_WIDTH - (WEBCAM_WIDTH * 2) - 30) // 2  # Center both webcam views

        self.webcam_display = WebcamDisplay(
            webcam_x,
            webcam_y,
            WEBCAM_WIDTH, 
            WEBCAM_HEIGHT,
            self.btn_font
        )
    
    def update(self, game_state, dialogue, thought, team1_last_move, team2_last_move, current_team, live_frame_surface, webcam_available, ai_thinking):
        """Update all UI components based on game state"""
        # NOTE: We don't set team dialogues/thoughts here anymore - they are set directly in Game.take_turn()
        # This avoids issues with them getting mixed up
        
        # Update team panels with their respective dialogue and thoughts
        self.team1_panel.update(
            game_state.team1_targets, 
            game_state.team1_collected,
            self.team1_thought,  # Use team-specific thought
            self.team1_dialogue, # Use team-specific dialogue
            team1_last_move
        )
        
        self.team2_panel.update(
            game_state.team2_targets, 
            game_state.team2_collected,
            self.team2_thought,  # Use team-specific thought
            self.team2_dialogue, # Use team-specific dialogue
            team2_last_move
        )
        
        # We no longer update self.dialogue_box here, as that's done in Game.take_turn()
        
        # Update button states
        mouse_pos = pygame.mouse.get_pos()
        self.ai_button.update(mouse_pos)
        self.webcam_button.update(mouse_pos)
        
        # Update webcam display
        self.webcam_display.last_frame = game_state.webcam_frame if hasattr(game_state, 'webcam_frame') else None
    
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