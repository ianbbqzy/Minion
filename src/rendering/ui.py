"""
UI components for the game
"""
import pygame
from src.utils.constants import WHITE, BUTTON_COLOR, BUTTON_HOVER_COLOR, PREVIEW_GAP, SPEECH_BG

class Button:
    def __init__(self, rect, text, font, color=BUTTON_COLOR, hover_color=BUTTON_HOVER_COLOR):
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.hover = False
        
    def draw(self, screen):
        """Draw the button on the screen"""
        color = self.hover_color if self.hover else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=6)
        
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def update(self, mouse_pos):
        """Update button state based on mouse position"""
        self.hover = self.rect.collidepoint(mouse_pos)
        
    def is_clicked(self, mouse_pos):
        """Check if the button was clicked"""
        return self.rect.collidepoint(mouse_pos)

class DialogueBox:
    def __init__(self, font, thought_font):
        self.font = font
        self.thought_font = thought_font
        self.dialogue = ""
        self.thought = ""
        self.timer = 0
        self.display_time = 3000  # 3 seconds
        
    def set_dialogue(self, dialogue, thought=""):
        """Set the dialogue and thought bubble text"""
        self.dialogue = dialogue
        self.thought = thought
        self.timer = pygame.time.get_ticks()
        
    def update(self):
        """Update dialogue display"""
        if self.dialogue and pygame.time.get_ticks() - self.timer >= self.display_time:
            self.dialogue = ""
            self.thought = ""
            
    def draw(self, screen, minion_pos, board_x, board_y, tile_size):
        """Draw the dialogue and thought bubbles"""
        if not self.dialogue:
            return
            
        # Calculate bubble position above the minion
        bubble_x = board_x + (minion_pos[1] * tile_size) + tile_size//2
        bubble_y = board_y + (minion_pos[0] * tile_size) - 60
        
        # Create dialogue text
        dialogue_text = self.font.render(self.dialogue, True, WHITE)
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
        bubble_surface.fill(SPEECH_BG)
        screen.blit(bubble_surface, bubble_rect)
        
        # Draw dialogue text
        screen.blit(dialogue_text, dialogue_rect)
        
        # Draw thought bubble (if space permits)
        if self.thought and bubble_y > 100:
            thought_y = bubble_y - 40
            thought_text = self.thought_font.render(f"({self.thought})", True, WHITE)
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
            screen.blit(thought_surface, thought_rect_bg)
            
            # Draw thought text
            screen.blit(thought_text, thought_rect)

class WebcamDisplay:
    def __init__(self, x, y, width, height, btn_font):
        self.rect = pygame.Rect(x, y, width, height)
        self.btn_font = btn_font
        self.last_frame = None
        self.captured_preview = None
        
    def draw_camera_feed(self, screen, frame_surface):
        """Draw the camera feed"""
        if frame_surface is not None:
            screen.blit(frame_surface, self.rect)
            pygame.draw.rect(screen, WHITE, self.rect, 2)
        else:
            self.draw_placeholder(screen, "Camera Unavailable")
    
    def draw_placeholder(self, screen, message):
        """Draw a placeholder when camera is unavailable"""
        pygame.draw.rect(screen, (100, 100, 100), self.rect)
        text = self.btn_font.render(message, True, WHITE)
        screen.blit(text, text.get_rect(center=(self.rect.centerx, self.rect.centery)))
    
    def draw_preview(self, screen):
        """Draw the captured frame preview"""
        if self.captured_preview is not None:
            screen.blit(self.captured_preview, (self.rect.x + 600, self.rect.y))
            pygame.draw.rect(screen, WHITE, (self.rect.x + 600, self.rect.y, self.rect.width, self.rect.height), 2)
            
            # Label
            label = self.btn_font.render("Last capture", True, WHITE)
            screen.blit(label, (self.rect.x + 600, self.rect.y + self.rect.height + 4))

    def set_captured_preview(self, surface):
        """Set the preview of the captured frame"""
        self.captured_preview = surface 