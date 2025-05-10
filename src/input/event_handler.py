"""
Event handling for the game
"""
import pygame
import sys

class EventHandler:
    def __init__(self, game):
        self.game = game
        
    def process_events(self):
        """Process all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            
            # Handle mouse events
            if event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.handle_mouse_click(event.pos)

            # Handle key presses
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event.key)
    
    def quit_game(self):
        """Exit the game"""
        pygame.quit()
        sys.exit()
    
    def handle_mouse_motion(self, pos):
        """Handle mouse motion events"""
        # No need to update button states here as UIManager handles it in its update method
        pass
                
    def handle_mouse_click(self, pos):
        """Handle mouse clicks"""
        # Check if AI button was clicked
        if self.game.ui_manager.is_ai_button_clicked(pos):
            # Only start AI turn if not already thinking
            if not self.game.game_state.game_over and not self.game.ai_turn_processing:
                self.game.start_both_ai_turns()
        
        # Check if webcam button was clicked
        elif self.game.ui_manager.is_webcam_button_clicked(pos) and self.game.ui_manager.webcam_display.last_frame is not None:
            # Send the cached frame to OpenAI
            pygame.event.set_blocked(pygame.MOUSEBUTTONDOWN)  # avoid double-click spam
            self.game.query_openai(self.game.ui_manager.webcam_display.last_frame.copy())
            pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
    
    def handle_keydown(self, key):
        """Handle key presses"""
        if key == pygame.K_SPACE:
            # Only start AI turn if not already thinking
            if not self.game.ai_turn_processing:
                # Take an AI turn
                self.game.start_both_ai_turns()
        elif key == pygame.K_r:
            # Reset game
            self.game.game_state.reset()
            self.game.reset_game_objects()
        
        # Debug keyboard handling can be added here if needed 