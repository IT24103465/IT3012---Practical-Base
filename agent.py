# agent.py
from collections import deque
import heapq
import random
import tkinter as tk


# ==========================================
# AGENT MODULE (agent.py or embedded)
# ==========================================

class GreedyGridAgent:
    """A simple agent that tries to move around systematically to clear the grid."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        return random.choice(self.actions_pool)


class SearchAgent:
    """An agent that uses uninformed search strategies (BFS, DFS, UCS) to navigate and find goals."""

    def __init__(self, search_strategy='bfs'):
        self.search_strategy = search_strategy.lower()
        self.plan = []
        self.active_algo = search_strategy.upper()  # 'BFS', 'DFS', or 'UCS'
        self.last_agent_pos = None

    def _get_neighbors(self, pos, grid_size, walls):
        """Returns valid neighboring (x, y) coordinates and the action taken to reach them."""
        x, y = pos
        width, height = grid_size
        walls_set = set(tuple(w) for w in walls)
        
        neighbors = []
        candidates = [
            ('Up', (x, y + 1)),
            ('Down', (x, y - 1)),
            ('Left', (x - 1, y)),
            ('Right', (x + 1, y))
        ]
        
        for action, (nx, ny) in candidates:
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in walls_set:
                    neighbors.append((action, (nx, ny)))
                    
        return neighbors

    def bfs_search(self, start_pos, target_pos, grid_size, walls):
        """Breadth-First Search (FIFO Queue using deque)."""
        frontier = deque([(start_pos, [])])
        reached = {start_pos}

        while frontier:
            current_pos, path = frontier.popleft()

            if current_pos == target_pos:
                return path

            for action, neighbor in self._get_neighbors(current_pos, grid_size, walls):
                if neighbor not in reached:
                    reached.add(neighbor)
                    frontier.append((neighbor, path + [action]))
        return []

    def dfs_search(self, start_pos, target_pos, grid_size, walls):
        """Depth-First Search (LIFO Stack using standard list)."""
        frontier = [(start_pos, [])]
        reached = {start_pos}

        while frontier:
            current_pos, path = frontier.pop()

            if current_pos == target_pos:
                return path

            for action, neighbor in self._get_neighbors(current_pos, grid_size, walls):
                if neighbor not in reached:
                    reached.add(neighbor)
                    frontier.append((neighbor, path + [action]))
        return []

    def ucs_search(self, start_pos, target_pos, grid_size, walls):
        """Uniform Cost Search (Priority Queue ordered by path cost g(n))."""
        frontier = [(0, start_pos, [])]
        reached = {start_pos: 0}

        while frontier:
            cost, current_pos, path = heapq.heappop(frontier)

            if current_pos == target_pos:
                return path

            for action, neighbor in self._get_neighbors(current_pos, grid_size, walls):
                new_cost = cost + 1  # Uniform step cost of 1
                if neighbor not in reached or new_cost < reached[neighbor]:
                    reached[neighbor] = new_cost
                    heapq.heappush(frontier, (new_cost, neighbor, path + [action]))
        return []

    def sense_and_act(self, percept: dict) -> str:
        grid_size = percept.get('grid_size', (10, 10))
        walls = percept.get('walls', [])
        all_food = percept.get('all_food', [])
        agent_pos = percept.get('agent_pos')

        if agent_pos is None:
            return random.choice(['Up', 'Down', 'Left', 'Right'])

        # If plan is empty, formulate a new plan to the closest food pellet
        if not self.plan:
            if not all_food:
                return 'Stay'
            
            # Target closest food using Manhattan distance
            target_pos = min(all_food, key=lambda f: abs(f[0] - agent_pos[0]) + abs(f[1] - agent_pos[1]))

            algo = self.active_algo.lower()
            if algo == 'bfs':
                self.plan = self.bfs_search(agent_pos, target_pos, grid_size, walls)
            elif algo == 'dfs':
                self.plan = self.dfs_search(agent_pos, target_pos, grid_size, walls)
            elif algo == 'ucs':
                self.plan = self.ucs_search(agent_pos, target_pos, grid_size, walls)
            else:
                self.plan = self.bfs_search(agent_pos, target_pos, grid_size, walls)

        if self.plan:
            return self.plan.pop(0)
        
        return 'Stay'


# ==========================================
# ENVIRONMENT MODULE (visual_grid_game.py)
# ==========================================

class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.agent_facing = 'Up'

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        self.toxic_traps = set()
        while len(self.toxic_traps) < 3:
            tx = random.randint(0, self.width - 1)
            ty = random.randint(0, self.height - 1)
            trap_pos = (tx, ty)
            if (
                trap_pos != (0, 0)
                and trap_pos not in self.walls
                and trap_pos not in self.food_positions
            ):
                self.toxic_traps.add(trap_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_percept(self) -> dict:
        ax, ay = self.agent_pos
        dx, dy = 0, 0

        if self.agent_facing == 'Up':
            dy = 1
        elif self.agent_facing == 'Down':
            dy = -1
        elif self.agent_facing == 'Left':
            dx = -1
        elif self.agent_facing == 'Right':
            dx = 1

        ahead_pos = (ax + dx, ay + dy)

        is_out_of_bounds = not (0 <= ahead_pos[0] < self.width and 0 <= ahead_pos[1] < self.height)
        wall_ahead = is_out_of_bounds or (ahead_pos in self.walls)

        return {
            'wall_ahead': wall_ahead,
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'trap_here': tuple(self.agent_pos) in self.toxic_traps,
            'smells_food_ahead': ahead_pos in self.food_positions,
            'collision': self.collision,
            'score': self.score,
            'remaining_food': len(self.food_positions),
            # --- Exposed for Search Agents (Step 1.1 & Fix) ---
            'grid_size': (self.width, self.height),
            'walls': list(self.walls),
            'all_food': list(self.food_positions),
            'agent_pos': tuple(self.agent_pos)
        }

    def execute_action(self, action: str):
        self.steps += 1
        
        if action in ['Up', 'Down', 'Left', 'Right']:
            self.agent_facing = action

        new_pos = list(self.agent_pos)

        if action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) in self.walls:
            self.score -= 5
        else:
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20

        if tuple_pos in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, walls=None):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents,
                                     custom_walls=walls)
        
        # You can change search strategy here: 'bfs', 'dfs', or 'ucs'
        self.agent = SearchAgent(search_strategy='bfs')

        max_canvas_dim = 600
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066",
                             fg="white")
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                       outline="#7a0000")

        for tx, ty in self.env.toxic_traps:
            offset = self.cell_size * 0.25
            x1 = tx * self.cell_size + offset
            y1 = (self.env.height - 1 - ty) * self.cell_size + offset
            x2 = x1 + self.cell_size * 0.5
            y2 = y1 + self.cell_size * 0.5
            
            self.canvas.create_line(x1, y1, x2, y2, fill="#dc2626", width=3)
            self.canvas.create_line(x1, y2, x2, y1, fill="#dc2626", width=3)

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                self.env.execute_action(action)

                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(250, step)
            else:
                end_text = f"Collision! Game Over! Final Score: {self.env.score}" if self.env.collision else f"Finished! Final Score: {self.env.score}"
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


if __name__ == "__main__":
    root = tk.Tk()
    app = GridGameGUI(root, width=12, height=12, num_food=15, num_opponents=0)
    root.mainloop()