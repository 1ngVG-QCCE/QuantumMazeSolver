import random
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt

N, S, E, W = 1, 2, 4, 8
DX = {E: 1, W: -1, N: 0, S: 0}
DY = {E: 0, W: 0, N: -1, S: 1}
OPPOSITE = {E: W, W: E, N: S, S: N}

class Maze:
    def __init__(self, grid: list[list[int]]):
        self.grid = grid
        self.width = len(grid)
        self.height = len(grid[0]) if len(grid) > 0 else 0

    def plot(self):
        fig, ax = plt.subplots(figsize=(self.width / 2, self.height / 2))
        ax.set_aspect('equal')
        ax.axis('off')
        for y in range(self.height):
            for x in range(self.width):
                cx, cy = x, self.height - y - 1  # invert y for correct display in matplotlib

                # Draw north wall if no passage north
                if (self.grid[y][x] & N) == 0:
                    ax.plot([cx, cx + 1], [cy + 1, cy + 1], color='black')

                # Draw west wall if no passage west
                if (self.grid[y][x] & W) == 0:
                    ax.plot([cx, cx], [cy, cy + 1], color='black')

                # Draw south wall if no passage south (for bottom row)
                if y == self.height - 1 and (self.grid[y][x] & S) == 0:
                    ax.plot([cx, cx + 1], [cy, cy], color='black')

                # Draw east wall if no passage east (for rightmost column)
                if x == self.width - 1 and (self.grid[y][x] & E) == 0:
                    ax.plot([cx + 1, cx + 1], [cy, cy + 1], color='black')

        # Entrance (top-left) - open the north wall of (0,0)
        ax.plot([0, 1], [self.height, self.height], color='white', linewidth=2)

        # Exit (bottom-right) - open the south wall of (width-1, height-1)
        ax.plot([self.width - 1, self.width], [0, 0], color='white', linewidth=2)

        plt.show()

    def print_ascii(self):
        # Top border with entrance at (0, 0)
        print("S  S" + "_" * (self.width * 2 - 3))
        for y in range(self.height):
            line = "|"
            for x in range(self.width):
                cell = self.grid[y][x]

                # Bottom wall: "_" if there's no South passage
                if cell & S:
                    bottom = " "
                else:
                    bottom = "_"

                # Right wall: check East wall and also South wall of neighbor
                if cell & E:
                    if (x + 1 < self.width) and (self.grid[y][x + 1] & S):
                        right = " "
                    else:
                        right = "_"
                else:
                    right = "|"

                line += bottom + right

            # Ensure proper entrance (open top of top-left cell)
            if y == 0:
                line = line[:1] + " " + line[2:]

            # Ensure proper exit (open bottom of bottom-right cell)
            if y == self.height - 1:
                line = line[:-3] + "E E"

            print(line)

    def edges(self):
        edges = []
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                if cell & N:
                    edges.append(((x, y), (x, y - 1)))
                if cell & S:
                    edges.append(((x, y), (x, y + 1)))
                if cell & E:
                    edges.append(((x, y), (x + 1, y)))
                if cell & W:
                    edges.append(((x, y), (x - 1, y)))
        undirected_edges = set()
        for a, b in edges:
            undirected_edges.add(frozenset([a, b])) #maybe is ok a /2

        return undirected_edges

class MazeGenerator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def generate_maze(self, width, height, seed = None) -> Maze:
        pass

class RecursiveBacktrackerGenerator(MazeGenerator):
    def generate_maze(self, width, height, seed = None) -> Maze:
        random.seed(seed if seed else random.randint(0, 0xFFFFFFFF))
        grid = [[0 for _ in range(height)] for _ in range(width)]
        self.carve_passages_from(0, 0, grid, width, height)
        return Maze(grid)

    def carve_passages_from(self, cx, cy, grid, width, height):
        directions = [N, S, E, W]
        random.shuffle(directions)
        for direction in directions:
            nx, ny = cx + DX[direction], cy + DY[direction]
            if 0 <= ny < height and 0 <= nx < width and grid[ny][nx] == 0:
                grid[cy][cx] |= direction
                grid[ny][nx] |= OPPOSITE[direction]
                self.carve_passages_from(nx, ny, grid, width, height)

class MazeSolver(ABC):
    def __init__(self, maze: Maze):
        self.maze = maze
        self.start = None
        self.end = None
        self.solution = []

    def solve(self, start: tuple[int, int], end: tuple[int, int]) -> 'MazeSolver':
        self.start = start
        self.end = end
        self.solution = self._solve(start, end)
        return self

    @abstractmethod
    def _solve(self, sstart: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        pass

    def plot_solution(self):
        fig, ax = plt.subplots(figsize=(self.maze.width / 2, self.maze.height / 2))
        ax.set_aspect('equal')
        ax.axis('off')

        # Draw maze walls
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                cx, cy = x, self.maze.height - y - 1

                if (self.maze.grid[y][x] & N) == 0:
                    ax.plot([cx, cx + 1], [cy + 1, cy + 1], color='black')
                if (self.maze.grid[y][x] & W) == 0:
                    ax.plot([cx, cx], [cy, cy + 1], color='black')
                if y == self.maze.height - 1 and (self.maze.grid[y][x] & S) == 0:
                    ax.plot([cx, cx + 1], [cy, cy], color='black')
                if x == self.maze.width - 1 and (self.maze.grid[y][x] & E) == 0:
                    ax.plot([cx + 1, cx + 1], [cy, cy + 1], color='black')

        # Draw solution path
        px = [x + 0.5 for x, y in self.solution]
        py = [self.maze.height - y - 0.5 for x, y in self.solution]
        ax.plot(px, py, color='red', linewidth=2)

        # Entrance & Exit
        ax.plot([0, 1], [self.maze.height, self.maze.height], color='white', linewidth=2)
        ax.plot([self.maze.width - 1, self.maze.width], [0, 0], color='white', linewidth=2)

        plt.show() 

class BFSSolver(MazeSolver):
    def _solve(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        queue = [start]
        visited = {start}
        parent = {start: None}

        while queue:
            current = queue.pop(0)
            if current == end:
                break

            for direction in [N, S, E, W]:
                nx, ny = current[0] + DX[direction], current[1] + DY[direction]
                if 0 <= nx < self.maze.width and 0 <= ny < self.maze.height:
                    if (self.maze.grid[current[1]][current[0]] & direction) and ((nx, ny) not in visited):
                        visited.add((nx, ny))
                        parent[(nx, ny)] = current
                        queue.append((nx, ny))

        path = []
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()
        return path        
