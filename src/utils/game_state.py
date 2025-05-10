"""
Game state management
"""
import numpy as np
import random
from src.utils.constants import GRID_HEIGHT, GRID_WIDTH, EMPTY, SUSHI, DONUT, BANANA, TEAM1_MINION_1, TEAM1_MINION_2, TEAM2_MINION_1, TEAM2_MINION_2, TILE_SIZE

class GameState:
    def __init__(self):
        # Initialize game state
        self.reset()
        
    def reset(self):
        """Reset the game to initial state"""
        # Grid representation
        self.grid = np.zeros((GRID_HEIGHT, GRID_WIDTH), dtype=int)
        
        # Define spawn positions
        self.TEAM1_1_SPAWN_POS = [5, 5]
        self.TEAM1_2_SPAWN_POS = [0, 3]
        self.TEAM2_1_SPAWN_POS = [4, 5]
        self.TEAM2_2_SPAWN_POS = [GRID_HEIGHT - 1, GRID_WIDTH - 3]

        self.team1_minion_1_pos = self.TEAM1_1_SPAWN_POS
        self.team1_minion_2_pos = self.TEAM1_2_SPAWN_POS
        self.team2_minion_1_pos = self.TEAM2_1_SPAWN_POS
        self.team2_minion_2_pos = self.TEAM2_2_SPAWN_POS
        
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
        self.grid[self.team1_minion_1_pos[0]][self.team1_minion_1_pos[1]] = TEAM1_MINION_1
        self.grid[self.team1_minion_2_pos[0]][self.team1_minion_2_pos[1]] = TEAM1_MINION_2
        self.grid[self.team2_minion_1_pos[0]][self.team2_minion_1_pos[1]] = TEAM2_MINION_1
        self.grid[self.team2_minion_2_pos[0]][self.team2_minion_2_pos[1]] = TEAM2_MINION_2
        
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
        
    def check_item_collection(self, minion_pos, collected_items):
        """Check if the minion has collected an item, returns (collected, item_code)"""
        y, x = minion_pos
        item = self.grid[y][x]
        
        # If the position has an item (1-3), collect it
        if 1 <= item <= 3:
            collected_items.append(item)
            # Clear the grid cell (set to empty)
            self.grid[y][x] = 0
            return True, item
        
        return False, None
        
    def check_win_conditions(self):
        """Check if a team has won"""
        # Check if team 1 has collected all targets
        team1_matches = 0
        for item in self.team1_targets:
            # Count how many of this item we need
            needed = self.team1_targets.count(item)
            # Count how many we have
            collected = self.team1_collected.count(item)
            # If we have enough of this item, count it as a match
            if collected >= needed:
                team1_matches += 1
                
        if team1_matches >= 5:
            self.game_over = True
            self.winner = 1

        # Check if team 2 has collected all targets
        team2_matches = 0
        for item in self.team2_targets:
            # Count how many of this item we need
            needed = self.team2_targets.count(item)
            # Count how many we have
            collected = self.team2_collected.count(item)
            # If we have enough of this item, count it as a match
            if collected >= needed:
                team2_matches += 1
                
        if team2_matches >= 5:
            self.game_over = True
            self.winner = 2
        
        # Check if max turns reached
        if self.turn_count >= self.max_turns:
            self.game_over = True
            if self.winner is None:
                self.winner = 0  # Draw
    
    def find_available_spawn_or_adjacent(self, base_spawn_pos, grid, occupied_by_others_this_turn):
        """
        Finds an available position for a bumped minion.
        Priority:
        1. base_spawn_pos if not taken by another minion this turn.
        2. An empty adjacent cell if not taken by another minion this turn.
        3. base_spawn_pos as a last resort.
        Args:
            base_spawn_pos: The primary position to check (e.g., minion's spawn point). List [y,x].
            grid: The current game grid (numpy array) - state before current turn's moves.
            occupied_by_others_this_turn: A list of [y, x] positions (lists) that other minions
                                           will definitively occupy in the current turn resolution.
        Returns:
            An available [y, x] position (list).
        """
        base_spawn_pos_tuple = tuple(base_spawn_pos)
        is_base_spawn_occupied_by_other = any(base_spawn_pos_tuple == tuple(occ_pos) for occ_pos in occupied_by_others_this_turn)

        if not is_base_spawn_occupied_by_other:
            return base_spawn_pos[:] # Return a copy

        # If base_spawn_pos is occupied by another, try adjacent cells
        adj_diffs = [(0, 1), (0, -1), (1, 0), (-1, 0)] # Right, Left, Down, Up
        random.shuffle(adj_diffs) 

        for dr, dc in adj_diffs:
            adj_pos_y, adj_pos_x = base_spawn_pos[0] + dr, base_spawn_pos[1] + dc
            
            if 0 <= adj_pos_y < GRID_HEIGHT and 0 <= adj_pos_x < GRID_WIDTH:
                adj_pos = [adj_pos_y, adj_pos_x]
                adj_pos_tuple = tuple(adj_pos)
                is_adj_occupied_by_other = any(adj_pos_tuple == tuple(occ_pos) for occ_pos in occupied_by_others_this_turn)
                
                # Check if the grid cell is EMPTY and not occupied by another minion
                if grid[adj_pos_y][adj_pos_x] == EMPTY and not is_adj_occupied_by_other:
                    return adj_pos 
        
        # Fallback: if spawn is taken AND no empty, non-taken adjacent spot is found
        print(f"Warning: Minion bumped to {base_spawn_pos}, which was occupied by another winner, and no suitable adjacent empty cell found. Defaulting to {base_spawn_pos}.")
        return base_spawn_pos[:] # Return a copy

    def next_turn(self):
        """Move to the next turn"""
        # Switch teams
        self.current_team = 2 if self.current_team == 1 else 1
        self.turn_count += 1
        
        # Check win conditions
        self.check_win_conditions()
