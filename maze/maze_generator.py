from abc import ABC, abstractmethod
import random
from maze.maze import Maze, MazeCell

class MazeGenerator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def generate_maze(self, width, height, seed = None) -> Maze:
        pass

class PrimGenerator(MazeGenerator):
    def generate_maze(self, width: int, height: int, start:tuple[int, int], end: tuple[int, int], seed=None) -> 'Maze':
        random.seed(seed if seed else random.randint(0, 0xFFFFFFFF))
        maze = Maze(width, height, start, end)
        visited: set[int] = set()
        frontier: list[tuple[int, int]] = []

        visited.add(maze.start.id)

        def neighbor_ids(cell: MazeCell) -> list[int]:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            result = []
            for dx, dy in directions:
                nx, ny = cell.x + dx, cell.y + dy
                if 0 <= nx < maze.width and 0 <= ny < maze.height:
                    nid = ny * maze.width + nx
                    result.append(nid)
            return result

        for nid in neighbor_ids(maze.start):
            frontier.append((maze.start.id, nid))

        while frontier:
            idx = random.randint(0, len(frontier) - 1)
            from_id, to_id = frontier.pop(idx)

            if to_id in visited:
                continue

            maze.connect_nodes(from_id, to_id)
            visited.add(to_id)

            to_cell = maze.node_by_id(to_id)
            for nid in neighbor_ids(to_cell):
                if nid not in visited:
                    frontier.append((to_id, nid))
        return maze

