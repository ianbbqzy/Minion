"""
UI components for the game
"""
import pygame
import numpy as np
from src.utils.constants import WHITE, BLACK, BUTTON_COLOR, BUTTON_HOVER_COLOR, PREVIEW_GAP, SPEECH_BG, SCREEN_WIDTH, SCREEN_HEIGHT

def create_gradient_background(colors, height=SCREEN_HEIGHT):
    """Create a vertical gradient background with the given colors"""
    surface = pygame.Surface((SCREEN_WIDTH, height))
    
    # Calculate the height of each color segment
    segment_height = height / (len(colors) - 1)
    
    for i in range(len(colors) - 1):
        start_color = colors[i]
        end_color = colors[i+1]
        start_y = int(i * segment_height)
        end_y = int((i + 1) * segment_height)
        
        # Draw gradient lines
        for y in range(start_y, end_y):
            # Calculate interpolation factor
            factor = (y - start_y) / segment_height
            
            # Interpolate between colors
            r = int(start_color[0] + (end_color[0] - start_color[0]) * factor)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * factor)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * factor)
            
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    return surface

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
        self.analysis_text = None
        
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
            # Position the preview next to the live feed instead of fixed offset
            preview_x = self.rect.x + self.rect.width + 30
            preview_rect = pygame.Rect(preview_x, self.rect.y, self.rect.width, self.rect.height)
            
            screen.blit(self.captured_preview, preview_rect)
            pygame.draw.rect(screen, WHITE, preview_rect, 2)
            
            # Label
            label = self.btn_font.render("Last capture", True, WHITE)
            screen.blit(label, (preview_rect.x, preview_rect.y + self.rect.height + 4))
            
            # Draw analysis results if available
            if self.analysis_text:
                # Create a semi-transparent background for text
                analysis_bg = pygame.Surface((self.rect.width, 80), pygame.SRCALPHA)
                analysis_bg.fill((0, 0, 0, 160))  # Semi-transparent black
                screen.blit(analysis_bg, (preview_rect.x, preview_rect.y + self.rect.height + 24))
                
                # Split and render analysis text lines
                lines = self.analysis_text.split('\n')
                for i, line in enumerate(lines):
                    text = self.btn_font.render(line, True, WHITE)
                    screen.blit(text, (preview_rect.x + 5, preview_rect.y + self.rect.height + 26 + (i * 20)))

    def set_captured_preview(self, surface):
        """Set the preview of the captured frame"""
        self.captured_preview = surface
        
    def set_analysis_text(self, text):
        """Set the analysis text results"""
        self.analysis_text = text

class TeamView:
    """A modern UI component that displays team information in a Tailwind-like style"""
    def __init__(self, team_id, x, y, width, height, font_large, font_medium, font_small, sprites):
        self.team_id = team_id
        self.rect = pygame.Rect(x, y, width, height)
        self.font_large = font_large
        self.font_medium = font_medium
        self.font_small = font_small
        self.sprites = sprites
        
        # Team data
        self.targets = []
        self.collected = []
        self.last_thought = ""
        self.last_dialogue = ""
        self.last_move = ""
        
        # UI colors
        self.bg_color = (0, 0, 0, 160)  # Semi-transparent black background
        self.text_color = WHITE
        self.accent_color = (255, 100, 100) if team_id == 1 else (100, 100, 255)  # Red for team 1, blue for team 2
        self.border_color = self.accent_color
        
    def update(self, targets, collected, thought, dialogue, move):
        """Update the team information"""
        self.targets = targets
        self.collected = collected
        self.last_thought = thought if thought else ""
        self.last_dialogue = dialogue if dialogue else ""
        self.last_move = move if move else ""
        
    def draw(self, screen):
        """Draw the team information panel with modern UI style"""
        # Draw main container with rounded corners
        panel_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, self.bg_color, (0, 0, self.rect.width, self.rect.height), border_radius=10)
        pygame.draw.rect(panel_surface, self.border_color, (0, 0, self.rect.width, self.rect.height), width=2, border_radius=10)
        
        # Team header
        header_text = f"Team {self.team_id}"
        header_surf = self.font_large.render(header_text, True, self.accent_color)
        header_rect = header_surf.get_rect(topleft=(20, 20))
        panel_surface.blit(header_surf, header_rect)
        
        # Content y position tracker
        y_pos = header_rect.bottom + 15
        
        # Targets section
        section_title = self.font_medium.render("Targets", True, self.text_color)
        panel_surface.blit(section_title, (20, y_pos))
        y_pos += section_title.get_height() + 10
        
        # Draw target sprites horizontally
        sprite_size = 40
        sprite_gap = 5
        for i, target in enumerate(self.targets):
            sprite_name = ["", "sushi", "donut", "banana"][target]
            if sprite_name and sprite_name in self.sprites.sprites:
                sprite = pygame.transform.scale(self.sprites.sprites[sprite_name], (sprite_size, sprite_size))
                panel_surface.blit(sprite, (20 + i * (sprite_size + sprite_gap), y_pos))
        
        y_pos += sprite_size + 20
        
        # Collected items section
        section_title = self.font_medium.render("Collected", True, self.text_color)
        panel_surface.blit(section_title, (20, y_pos))
        y_pos += section_title.get_height() + 10
        
        # Draw collected sprites in a grid (4 per row)
        items_per_row = 4
        for i, item in enumerate(self.collected):
            sprite_name = ["", "sushi", "donut", "banana"][item]
            if sprite_name and sprite_name in self.sprites.sprites:
                row = i // items_per_row
                col = i % items_per_row
                sprite = pygame.transform.scale(self.sprites.sprites[sprite_name], (sprite_size, sprite_size))
                panel_surface.blit(sprite, (20 + col * (sprite_size + sprite_gap), y_pos + row * (sprite_size + sprite_gap)))
        
        # Calculate height based on number of collected items
        collected_rows = max(1, (len(self.collected) + items_per_row - 1) // items_per_row)
        y_pos += (collected_rows * (sprite_size + sprite_gap)) + 20
        
        # Last move section - only if we have a move
        if self.last_move:
            section_title = self.font_medium.render("Last Move", True, self.text_color)
            panel_surface.blit(section_title, (20, y_pos))
            y_pos += section_title.get_height() + 5
            
            move_text = self.font_small.render(self.last_move, True, self.text_color)
            panel_surface.blit(move_text, (20, y_pos))
            y_pos += move_text.get_height() + 15
        
        # Dialogue section - only if we have dialogue
        if self.last_dialogue:
            section_title = self.font_medium.render("Dialogue", True, self.text_color)
            panel_surface.blit(section_title, (20, y_pos))
            y_pos += section_title.get_height() + 5
            
            # Wrap text to fit width
            dialogue_lines = self._wrap_text(self.last_dialogue, self.font_small, self.rect.width - 40)
            for line in dialogue_lines:
                line_surf = self.font_small.render(line, True, self.text_color)
                panel_surface.blit(line_surf, (20, y_pos))
                y_pos += line_surf.get_height() + 2
            
            y_pos += 15
        
        # Thought section - only if we have a thought
        if self.last_thought:
            section_title = self.font_medium.render("Thought", True, self.text_color)
            panel_surface.blit(section_title, (20, y_pos))
            y_pos += section_title.get_height() + 5
            
            # Wrap text to fit width
            thought_lines = self._wrap_text(self.last_thought, self.font_small, self.rect.width - 40)
            for line in thought_lines:
                line_surf = self.font_small.render(line, True, (180, 180, 180))  # Lighter color for thoughts
                panel_surface.blit(line_surf, (20, y_pos))
                y_pos += line_surf.get_height() + 2
        
        # Blit the panel to the screen
        screen.blit(panel_surface, self.rect)
    
    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within the given width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width, _ = font.size(test_line)
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word is too long, split it
                    lines.append(word)
                    current_line = []
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines 