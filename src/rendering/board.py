"""
Board rendering for the game
"""
import pygame
from src.utils.constants import GRAY, WHITE

class BoardRenderer:
    def __init__(self, board_x, board_y, grid_width, grid_height, tile_size, sprites):
        self.board_x = board_x
        self.board_y = board_y
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_size = tile_size
        self.sprites = sprites
        
    def draw(self, screen, grid):
        """Draw the game board with all elements"""
        # Draw board background
        pygame.draw.rect(
            screen, 
            GRAY, 
            (self.board_x, self.board_y, 
             self.grid_width * self.tile_size, 
             self.grid_height * self.tile_size)
        )
        
        # Draw grid cells
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                # Calculate position
                rect_x = self.board_x + (x * self.tile_size)
                rect_y = self.board_y + (y * self.tile_size)
                
                # Get tile type
                item_code = grid[y][x]
                
                # Draw the colored tile background
                screen.blit(self.sprites.tile_surfaces[0], (rect_x, rect_y))  # Draw grass tile
                
                # Draw cell content based on code
                if item_code == 1:  # Sushi
                    screen.blit(self.sprites.sprites["sushi"], (rect_x, rect_y))
                elif item_code == 2:  # Donut
                    screen.blit(self.sprites.sprites["donut"], (rect_x, rect_y))
                elif item_code == 3:  # Banana
                    screen.blit(self.sprites.sprites["banana"], (rect_x, rect_y))
                elif item_code == 4:  # Team 1 Minion
                    screen.blit(self.sprites.sprites["team1"], (rect_x, rect_y))
                elif item_code == 5:  # Team 2 Minion
                    screen.blit(self.sprites.sprites["team2"], (rect_x, rect_y))
    
    def draw_sidebar(self, screen, game_state, font, small_font):
        """Draw the sidebar with game information"""
        sidebar_x = self.board_x + (self.grid_width * self.tile_size) + 20
        sidebar_y = self.board_y
        
        # Draw current turn
        turn_text = font.render(f"Turn: {game_state.turn_count}/{game_state.max_turns}", True, WHITE)
        screen.blit(turn_text, (sidebar_x, sidebar_y))
        sidebar_y += 40
        
        # Draw current team
        team_color = self.sprites.sprites["team1"].get_at((self.tile_size//2, self.tile_size//2)) if game_state.current_team == 1 else self.sprites.sprites["team2"].get_at((self.tile_size//2, self.tile_size//2))
        team_text = font.render(f"Current Team: {game_state.current_team}", True, team_color)
        screen.blit(team_text, (sidebar_x, sidebar_y))
        sidebar_y += 40
        
        # Draw team 1 targets
        team1_target_text = font.render("Team 1 Targets:", True, self.sprites.sprites["team1"].get_at((self.tile_size//2, self.tile_size//2)))
        screen.blit(team1_target_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw target items as icons
        for i, target in enumerate(game_state.team1_targets):
            icon_name = ["", "sushi", "donut", "banana"][target]
            icon_x = sidebar_x + (i * 40)
            screen.blit(self.sprites.sprites[icon_name], (icon_x, sidebar_y))
        sidebar_y += 50
        
        # Draw team 2 targets
        team2_target_text = font.render("Team 2 Targets:", True, self.sprites.sprites["team2"].get_at((self.tile_size//2, self.tile_size//2)))
        screen.blit(team2_target_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw target items as icons
        for i, target in enumerate(game_state.team2_targets):
            icon_name = ["", "sushi", "donut", "banana"][target]
            icon_x = sidebar_x + (i * 40)
            screen.blit(self.sprites.sprites[icon_name], (icon_x, sidebar_y))
        sidebar_y += 50
        
        # Draw team 1 collected items
        team1_collected_text = font.render("Team 1 Collected:", True, self.sprites.sprites["team1"].get_at((self.tile_size//2, self.tile_size//2)))
        screen.blit(team1_collected_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw collected items as icons
        if game_state.team1_collected:
            for i, item in enumerate(game_state.team1_collected):
                icon_name = ["", "sushi", "donut", "banana"][item]
                icon_x = sidebar_x + (i % 8 * 40)
                # Only show up to 8 items per row
                icon_y = sidebar_y + ((i // 8) * 40)
                screen.blit(self.sprites.sprites[icon_name], (icon_x, icon_y))
            sidebar_y += 50 + (len(game_state.team1_collected) // 8) * 40
        else:
            none_text = small_font.render("None", True, WHITE)
            screen.blit(none_text, (sidebar_x, sidebar_y))
            sidebar_y += 30
        
        # Draw team 2 collected items
        team2_collected_text = font.render("Team 2 Collected:", True, self.sprites.sprites["team2"].get_at((self.tile_size//2, self.tile_size//2)))
        screen.blit(team2_collected_text, (sidebar_x, sidebar_y))
        sidebar_y += 30
        
        # Draw collected items as icons
        if game_state.team2_collected:
            for i, item in enumerate(game_state.team2_collected):
                icon_name = ["", "sushi", "donut", "banana"][item]
                icon_x = sidebar_x + (i % 8 * 40)
                # Only show up to 8 items per row
                icon_y = sidebar_y + ((i // 8) * 40)
                screen.blit(self.sprites.sprites[icon_name], (icon_x, icon_y))
            sidebar_y += 50 + (len(game_state.team2_collected) // 8) * 40
        else:
            none_text = small_font.render("None", True, WHITE)
            screen.blit(none_text, (sidebar_x, sidebar_y))
            sidebar_y += 30
            
        return sidebar_y  # Return the new y position for additional rendering
    
    def draw_game_over(self, screen, winner, screen_width, screen_height, font, small_font):
        """Draw the game over screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        screen.blit(overlay, (0, 0))
        
        if winner == 0:
            result_text = font.render("Game Over: Draw!", True, WHITE)
        else:
            team_color = self.sprites.sprites["team1"].get_at((self.tile_size//2, self.tile_size//2)) if winner == 1 else self.sprites.sprites["team2"].get_at((self.tile_size//2, self.tile_size//2))
            result_text = font.render(f"Game Over: Team {winner} Wins!", True, team_color)
            
        text_rect = result_text.get_rect(center=(screen_width//2, screen_height//2))
        screen.blit(result_text, text_rect)
        
        restart_text = small_font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(screen_width//2, screen_height//2 + 40))
        screen.blit(restart_text, restart_rect) 