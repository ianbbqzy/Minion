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
        self.captured_preview_team1 = None
        self.captured_preview_team2 = None
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
        """Draw the captured frame previews side by side"""
        if self.captured_preview_team1 is not None and self.captured_preview_team2 is not None:
            # Position the first preview
            preview_x1 = self.rect.x + self.rect.width + 30
            preview_rect1 = pygame.Rect(preview_x1, self.rect.y, self.rect.width/2, self.rect.height)
            
            screen.blit(self.captured_preview_team1, preview_rect1)
            pygame.draw.rect(screen, WHITE, preview_rect1, 2)
            
            # Position the second preview
            preview_x2 = preview_x1 + self.rect.width/2  + 30
            preview_rect2 = pygame.Rect(preview_x2, self.rect.y, self.rect.width/2, self.rect.height)

            screen.blit(self.captured_preview_team2, preview_rect2)
            pygame.draw.rect(screen, WHITE, preview_rect2, 2)

    def set_captured_preview_team1(self, surface):
        """Set the preview of the captured frame"""
        self.captured_preview_team1 = surface

    def set_captured_preview_team2(self, surface):
        """Set the preview of the captured frame"""
        self.captured_preview_team2 = surface
        
    def set_analysis_text(self, text):
        """Set the analysis text results"""
        self.analysis_text = text

class TeamView:
    """A modern UI component that displays team information in a Tailwind-like style"""
    def __init__(self, team_id, x, y, width, height, font_large, font_medium, font_small, sprites):
        self.team_id = team_id
        self.rect = pygame.Rect(x, y, width + 100, height)  # Make panel wider by adding 100 pixels
        self.font_large = font_large
        self.font_medium = font_medium
        self.font_small = font_small
        self.sprites = sprites
        
        # Team data
        self.targets = []
        self.collected = []
        
        # History storage - for step by step tracking
        self.step_history = []
        self.current_step = 0
        
        # UI colors
        self.bg_color = (0, 0, 0, 160)  # Semi-transparent black background
        self.text_color = WHITE
        self.accent_color = (255, 100, 100) if team_id == 1 else (100, 100, 255)  # Red for team 1, blue for team 2
        self.border_color = self.accent_color
        
        # Scrolling
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_area_start = 0  # Y position where scrollable area starts
        self.scroll_bar_rect = None
        self.scroll_bar_active = False
        self.scroll_drag_start = None
        
    def update(self, targets, collected, thought1, dialogue1, move1, thought2, dialogue2, move2, step_count=None, should_add_history=True):
        """Update the team information"""
        self.targets = targets
        self.collected = collected
        
        # Only add to history if there's content to add AND we should add history
        if should_add_history and any([thought1, dialogue1, move1, thought2, dialogue2, move2]):
            # Use the provided step count, or increment our own if none provided
            if step_count is not None:
                self.current_step = step_count
            else:
                self.current_step += 1
                
            # Add new step at the beginning of the list (most recent first)
            self.step_history.insert(0, {
                'step': self.current_step,
                'minion1': {
                    'thought': thought1 if thought1 else "",
                    'dialogue': dialogue1 if dialogue1 else "",
                    'move': move1 if move1 else ""
                },
                'minion2': {
                    'thought': thought2 if thought2 else "",
                    'dialogue': dialogue2 if dialogue2 else "",
                    'move': move2 if move2 else ""
                }
            })
            
    def clear_history(self):
        """Clear the step history when refreshing"""
        self.step_history = []
        self.current_step = 0
        self.scroll_offset = 0
        
    def handle_scroll(self, event):
        """Handle scroll events"""
        if event.type == pygame.MOUSEWHEEL:
            # Check if mouse is over this panel
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                # Scroll up or down
                self.scroll_offset -= event.y * 30  # Adjust scroll speed as needed
                self.clamp_scroll()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left mouse button
                mouse_pos = pygame.mouse.get_pos()
                if self.scroll_bar_rect and self.scroll_bar_rect.collidepoint(mouse_pos):
                    self.scroll_drag_start = mouse_pos[1]
                    self.scroll_bar_active = True
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button
                self.scroll_bar_active = False
                self.scroll_drag_start = None
                
        elif event.type == pygame.MOUSEMOTION:
            if self.scroll_bar_active and self.scroll_drag_start is not None:
                # Calculate scroll based on drag distance
                drag_distance = event.pos[1] - self.scroll_drag_start
                
                # Calculate scroll amount based on drag distance and content height
                scroll_ratio = drag_distance / (self.rect.height - self.scroll_area_start)
                scroll_amount = scroll_ratio * self.max_scroll
                
                # Update scroll position and drag start point
                self.scroll_offset += scroll_amount
                self.scroll_drag_start = event.pos[1]
                self.clamp_scroll()
    
    def clamp_scroll(self):
        """Ensure scroll offset stays within valid range"""
        if self.scroll_offset < 0:
            self.scroll_offset = 0
        elif self.scroll_offset > self.max_scroll:
            self.scroll_offset = self.max_scroll
        
    def draw(self, screen):
        """Draw the team information panel with modern UI style and scrolling"""
        # Draw main container with rounded corners
        panel_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surface, self.bg_color, (0, 0, self.rect.width, self.rect.height), border_radius=10)
        pygame.draw.rect(panel_surface, self.border_color, (0, 0, self.rect.width, self.rect.height), width=2, border_radius=10)
        
        # Create a separate surface for the scrollable content
        content_surface = pygame.Surface((self.rect.width - 40, 5000), pygame.SRCALPHA)  # Height is temporary
        
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
        
        # Save the starting position of scrollable content
        self.scroll_area_start = y_pos
        
        # Create a clip rect for the scrollable area
        scroll_clip_rect = pygame.Rect(0, 0, self.rect.width - 25, self.rect.height - self.scroll_area_start)
        content_y_pos = 0  # This will track position in the content surface
        
        # Start drawing the scrollable history content - one section per step
        if len(self.step_history) > 0:
            # Render steps with most recent first
            for step_data in self.step_history:
                step_number = step_data['step']
                
                # Draw step header with step number
                step_title = self.font_medium.render(f"Step {step_number}", True, self.accent_color)
                content_surface.blit(step_title, (20, content_y_pos))
                content_y_pos += step_title.get_height() + 10
                
                # Draw separator line
                pygame.draw.line(content_surface, (100, 100, 100), 
                                (20, content_y_pos), 
                                (self.rect.width - 60, content_y_pos), 1)
                content_y_pos += 10
                
                # Minion 1 section
                minion1_title = self.font_medium.render("Minion 1", True, self.text_color)
                content_surface.blit(minion1_title, (20, content_y_pos))
                content_y_pos += minion1_title.get_height() + 5
                
                # Minion 1 thought
                if step_data['minion1']['thought']:
                    thought_title = self.font_small.render("Thought:", True, (150, 150, 150))
                    content_surface.blit(thought_title, (30, content_y_pos))
                    content_y_pos += thought_title.get_height() + 2
                    
                    thought_lines = self._wrap_text(step_data['minion1']['thought'], self.font_small, self.rect.width - 80)
                    for line in thought_lines:
                        line_surf = self.font_small.render(line, True, (180, 180, 180))
                        content_surface.blit(line_surf, (40, content_y_pos))
                        content_y_pos += line_surf.get_height() + 2
                    content_y_pos += 5
                
                # Minion 1 dialogue
                if step_data['minion1']['dialogue']:
                    dialogue_title = self.font_small.render("Dialogue:", True, self.text_color)
                    content_surface.blit(dialogue_title, (30, content_y_pos))
                    content_y_pos += dialogue_title.get_height() + 2
                    
                    dialogue_lines = self._wrap_text(step_data['minion1']['dialogue'], self.font_small, self.rect.width - 80)
                    for line in dialogue_lines:
                        line_surf = self.font_small.render(line, True, self.text_color)
                        content_surface.blit(line_surf, (40, content_y_pos))
                        content_y_pos += line_surf.get_height() + 2
                    content_y_pos += 5
                
                # Minion 1 move
                if step_data['minion1']['move']:
                    move_title = self.font_small.render("Move:", True, self.text_color)
                    content_surface.blit(move_title, (30, content_y_pos))
                    content_y_pos += move_title.get_height() + 2
                    
                    move_text = self.font_small.render(step_data['minion1']['move'], True, self.text_color)
                    content_surface.blit(move_text, (40, content_y_pos))
                    content_y_pos += move_text.get_height() + 10
                
                # Minion 2 section
                minion2_title = self.font_medium.render("Minion 2", True, self.text_color)
                content_surface.blit(minion2_title, (20, content_y_pos))
                content_y_pos += minion2_title.get_height() + 5
                
                # Minion 2 thought
                if step_data['minion2']['thought']:
                    thought_title = self.font_small.render("Thought:", True, (150, 150, 150))
                    content_surface.blit(thought_title, (30, content_y_pos))
                    content_y_pos += thought_title.get_height() + 2
                    
                    thought_lines = self._wrap_text(step_data['minion2']['thought'], self.font_small, self.rect.width - 80)
                    for line in thought_lines:
                        line_surf = self.font_small.render(line, True, (180, 180, 180))
                        content_surface.blit(line_surf, (40, content_y_pos))
                        content_y_pos += line_surf.get_height() + 2
                    content_y_pos += 5
                
                # Minion 2 dialogue
                if step_data['minion2']['dialogue']:
                    dialogue_title = self.font_small.render("Dialogue:", True, self.text_color)
                    content_surface.blit(dialogue_title, (30, content_y_pos))
                    content_y_pos += dialogue_title.get_height() + 2
                    
                    dialogue_lines = self._wrap_text(step_data['minion2']['dialogue'], self.font_small, self.rect.width - 80)
                    for line in dialogue_lines:
                        line_surf = self.font_small.render(line, True, self.text_color)
                        content_surface.blit(line_surf, (40, content_y_pos))
                        content_y_pos += line_surf.get_height() + 2
                    content_y_pos += 5
                
                # Minion 2 move
                if step_data['minion2']['move']:
                    move_title = self.font_small.render("Move:", True, self.text_color)
                    content_surface.blit(move_title, (30, content_y_pos))
                    content_y_pos += move_title.get_height() + 2
                    
                    move_text = self.font_small.render(step_data['minion2']['move'], True, self.text_color)
                    content_surface.blit(move_text, (40, content_y_pos))
                    content_y_pos += move_text.get_height() + 20
        else:
            # Display a message when no history is available
            no_history_text = self.font_small.render("No action history yet", True, (150, 150, 150))
            content_surface.blit(no_history_text, (20, content_y_pos))
            content_y_pos += no_history_text.get_height() + 10
                
        # Calculate the total content height and max scroll offset
        total_content_height = content_y_pos
        visible_height = self.rect.height - self.scroll_area_start
        self.max_scroll = max(0, total_content_height - visible_height)
        
        # Draw the visible portion of the scrollable content
        visible_content = content_surface.subsurface(pygame.Rect(0, self.scroll_offset, self.rect.width - 40, min(visible_height, total_content_height - self.scroll_offset)))
        panel_surface.blit(visible_content, (20, self.scroll_area_start))
        
        # Draw scroll bar if content is scrollable
        if self.max_scroll > 0:
            # Draw scroll track
            scroll_track_rect = pygame.Rect(self.rect.width - 20, self.scroll_area_start, 10, visible_height)
            pygame.draw.rect(panel_surface, (80, 80, 80), scroll_track_rect, border_radius=5)
            
            # Calculate scroll thumb size and position
            thumb_height = max(30, visible_height * (visible_height / total_content_height))
            thumb_pos = self.scroll_area_start + (self.scroll_offset / total_content_height) * visible_height
            
            # Draw scroll thumb
            scroll_thumb_rect = pygame.Rect(self.rect.width - 20, thumb_pos, 10, thumb_height)
            pygame.draw.rect(panel_surface, (150, 150, 150), scroll_thumb_rect, border_radius=5)
            
            # Store the scroll bar rect for interaction (adjust to screen coordinates)
            self.scroll_bar_rect = pygame.Rect(
                self.rect.x + self.rect.width - 20,
                self.rect.y + thumb_pos,
                10,
                thumb_height
            )
        else:
            self.scroll_bar_rect = None
            
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
