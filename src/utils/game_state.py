"""
Game state management
"""
import numpy as np
import random
from src.utils.constants import GRID_HEIGHT, GRID_WIDTH, EMPTY, SUSHI, DONUT, BANANA, TEAM1_MINION, TEAM2_MINION

class GameState:
    def __init__(self):
        # Initialize game state
        self.reset()
        
    def reset(self):
        """Reset the game to initial state"""
        # Grid representation
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        
        # Minion positions
        self.team1_minion_pos = [0, 0]  # [y, x]
        self.team2_minion_pos = [GRID_HEIGHT-1, GRID_WIDTH-1]  # [y, x]
        
        # Generate target items for each team
        self.team1_targets = self.generate_targets()
        self.team2_targets = self.generate_targets()
        
        # Items collected by each team
        self.team1_collected = []
        self.team2_collected = []
        
        # Game status
        self.current_team = 1
        self.turn_count = 0
        self.max_turns = 50
        self.game_over = False
        self.winner = None
        
        # Initialize grid with minions
        self.grid[self.team1_minion_pos[0]][self.team1_minion_pos[1]] = TEAM1_MINION
        self.grid[self.team2_minion_pos[0]][self.team2_minion_pos[1]] = TEAM2_MINION
        
        # Distribute items on the grid
        self.distribute_items()
    
    def generate_targets(self):
        """Generate 5 random items (1=sushi, 2=donut, 3=banana)"""
        return [random.randint(1, 3) for _ in range(5)]
        
    def distribute_items(self):
        """Distribute items randomly on the grid"""
        num_items = {
            SUSHI: 10,
            DONUT: 10,
            BANANA: 10,
        }
        
        # Place items randomly on empty cells
        for item_type, count in num_items.items():
            placed = 0
            while placed < count:
                x = random.randint(0, GRID_WIDTH-1)
                y = random.randint(0, GRID_HEIGHT-1)
                
                # If the cell is empty, place the item
                if self.grid[y][x] == EMPTY:
                    self.grid[y][x] = item_type
                    placed += 1
    
    def calculate_new_position(self, position, direction):
        """Calculate a new position based on the current position and direction"""
        new_pos = position.copy()
        if direction == "up" and position[0] > 0:
            new_pos[0] -= 1
        elif direction == "down" and position[0] < GRID_HEIGHT - 1:
            new_pos[0] += 1
        elif direction == "left" and position[1] > 0:
            new_pos[1] -= 1
        elif direction == "right" and position[1] < GRID_WIDTH - 1:
            new_pos[1] += 1
        # "stay" does nothing
        return new_pos
        
    def move_minion(self, minion_pos, direction):
        """Move a minion in the specified direction"""
        # Clear current position
        self.grid[minion_pos[0]][minion_pos[1]] = EMPTY
        
        # Calculate new position
        new_pos = self.calculate_new_position(minion_pos, direction)
        
        # Update minion position
        minion_pos[0] = new_pos[0]
        minion_pos[1] = new_pos[1]
        
        # Get the minion code for the current team
        minion_code = TEAM1_MINION if self.current_team == 1 else TEAM2_MINION
        
        # Update grid with new position
        self.grid[minion_pos[0]][minion_pos[1]] = minion_code
        
    def check_item_collection(self, minion_pos, collected_items):
        """Check if the minion has collected an item"""
        y, x = minion_pos
        item = self.grid[y][x]
        
        # If the position has an item (1-3), collect it
        if 1 <= item <= 3:
            collected_items.append(item)
            
    def check_win_conditions(self):
        """Check if a team has won"""
        # Check if team 1 has collected all targets
        team1_matches = 0
        for item in self.team1_targets:
            if self.team1_collected.count(item) > 0:
                team1_matches += 1
                
        if team1_matches >= 5:
            self.game_over = True
            self.winner = 1

        # Check if team 2 has collected all targets
        team2_matches = 0
        for item in self.team2_targets:
            if self.team2_collected.count(item) > 0:
                team2_matches += 1
                
        if team2_matches >= 5:
            self.game_over = True
            self.winner = 2
        
        # Check if max turns reached
        if self.turn_count >= self.max_turns:
            self.game_over = True
            if self.winner is None:
                self.winner = 0  # Draw
    
    def next_turn(self):
        """Move to the next turn"""
        # Switch teams
        self.current_team = 2 if self.current_team == 1 else 1
        self.turn_count += 1
        
        # Check win conditions
        self.check_win_conditions()
    
    def item_to_emoji(self, item_code):
        """Convert item code to emoji"""
        if item_code == EMPTY:
            return "0"  # Empty
        elif item_code == SUSHI:
            return "🍣"  # Sushi
        elif item_code == DONUT:
            return "🍩"  # Donut
        elif item_code == BANANA:
            return "🍌"  # Banana
        elif item_code == TEAM1_MINION:
            return "M1"  # Team 1 Minion
        elif item_code == TEAM2_MINION:
            return "M2"  # Team 2 Minion
        return "?" 