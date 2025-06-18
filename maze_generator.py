import random
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import sys
sys.path.insert(1, '../')
from utils import Helpers as hp


class Node:
    def __init__(self, id: int, edges: list['Edge'] = []):
        self.__id = id
    
    @property
    def id(self) -> int:
        return self.__id

    def __repr__(self) -> str:
        return f"Node({self.id})"

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if isinstance(other, Node):
            return self.id == other.id
        return False

class MazeCell(Node):
    def __init__(self, id: int, x: int, y: int):
        super().__init__(id)
        self.__x = x
        self.__y = y

    @property
    def x(self) -> int:
        return self.__x
    
    @property
    def y(self) -> int:
        return self.__y
    
    def __repr__(self) -> str:
        return f"MazeCell({self.x}, {self.y})"

class Edge:
    def __init__(self, start: Node, end: Node):
        self.__start = start
        self.__end = end

    @property
    def start(self) -> Node:
        return self.__start

    @property
    def end(self) -> Node:
        return self.__end
        
    def __repr__(self):
        return f"Edge({self.start}, {self.end})"

    def __hash__(self):
        return hash((self.start, self.end))

    def __eq__(self, other):
        if isinstance(other, Edge):
            return (self.start == other.start and self.end == other.end) or (self.start == other.end and self.end == other.start)
        return False

class Graph:
    def __init__(self, nodes: set[Node] = [], edges: list[Edge] = []):
        self.__nodes = nodes
        self.__edges = edges

    @property
    def nodes(self) -> frozenset[Node]:
        return frozenset(self.__nodes)

    @property
    def edges(self) -> frozenset[Edge]:
        return frozenset(self.__edges)
    
    @staticmethod
    def from_edges(edges: list[tuple[int, int]], bidirectional: bool = False) -> 'Graph':
        graph = Graph(list(map(lambda node_id: Node(node_id), list(set([node_id for edge in edges for node_id in edge])))))
        for e_start, e_end in edges:
            graph.connect_nodes(e_start, e_end)
            if bidirectional:
                graph.connect_nodes(e_end, e_start)
        return graph
    
    def node_by_id(self, node_id: int) -> Node:
        node = next((node for node in self.nodes if node.id == node_id), None)
        if not node:
            raise ValueError(f"Node with id {node_id} not found in the graph")
        return node

    def connect_nodes(self, n1_id: int, n2_id: int) -> None:
        n1 = self.node_by_id(n1_id)
        n2 = self.node_by_id(n2_id)
        self.__edges.append(Edge(n1, n2))

    def disconnect_nodes(self, n1_id: int, n2_id: int) -> None:
        n1 = self.node_by_id(n1_id)
        n2 = self.node_by_id(n2_id)
        self.__edges.remove(Edge(n1, n2))

    def show(self, path: list[Node] = None):
        mermaid_lines = ["flowchart LR;"]
        for edge in self.edges:
            mermaid_lines.append(f"    n{edge.start.id} --> n{edge.end.id};")

        if path:
            for start, end in zip(path, path[1:]):
                mermaid_lines.append(f"    ns{start.id} --> ns{end.id};")
        hp.mm("\n".join(mermaid_lines))

        
        
class Maze(Graph):
    def __init__(self, width: int, height: int, start: tuple[int, int] = (0, 0), end: tuple[int, int] = None):
        self.__width = width
        self.__height = height
        if end is None:
            end = (width - 1, height - 1)
        nodes = [MazeCell(y * width + x, x, y) for y in range(height) for x in range(width)]

        coord_to_node = {(node.x, node.y): node for node in nodes}

        self.__start = coord_to_node[start]
        self.__end = coord_to_node[end]
        edges = []    
        super().__init__(nodes, edges)

    @property
    def width(self) -> int:
        return self.__width 
    
    @property
    def height(self) -> int:
        return self.__height
    
    @property
    def nodes(self) -> frozenset[MazeCell]:
        return super().nodes
    
    @property
    def start(self) -> MazeCell:
        return self.__start
    
    @property
    def end(self) -> MazeCell:
        return self.__end
        
    def node_by_id(self, node_id) -> MazeCell:
        return super().node_by_id(node_id)
    
    def connect_nodes(self, n1_id: int, n2_id: int) -> None:
        super().connect_nodes(n1_id, n2_id)
        super().connect_nodes(n2_id, n1_id)

    def disconnect_nodes(self, n1_id: int, n2_id: int) -> None:
        super().disconnect_nodes(n1_id, n2_id)
        super().disconnect_nodes(n2_id, n1_id)

    def show(self, path: list[MazeCell] = None):
        fig, ax = plt.subplots(figsize=(self.width / 2, self.height / 2))
        ax.set_aspect('equal')
        ax.axis('off')

        connections = {frozenset({(e.start.x, e.start.y), (e.end.x, e.end.y)}) for e in self.edges}

        def wall_exists(x1, y1, x2, y2):
            return frozenset({(x1, y1), (x2, y2)}) not in connections

        for y in range(self.height):
            for x in range(self.width):
                cx, cy = x, self.height - y - 1

                # Draw walls only if on boundary or no connection
                if y == 0 or wall_exists(x, y, x, y - 1):  # North
                    ax.plot([cx, cx + 1], [cy + 1, cy + 1], 'k')
                if x == 0 or wall_exists(x, y, x - 1, y):  # West
                    ax.plot([cx, cx], [cy, cy + 1], 'k')
                if y == self.height - 1 or wall_exists(x, y, x, y + 1):  # South
                    ax.plot([cx, cx + 1], [cy, cy], 'k')
                if x == self.width - 1 or wall_exists(x, y, x + 1, y):  # East
                    ax.plot([cx + 1, cx + 1], [cy, cy + 1], 'k')

        def open_wall(x, y):
            cx, cy = x, self.height - y - 1
            if x == 0:
                ax.plot([cx, cx], [cy, cy + 1], 'w', linewidth=3)
            elif x == self.width - 1:
                ax.plot([cx + 1, cx + 1], [cy, cy + 1], 'w', linewidth=3)
            elif y == 0:
                ax.plot([cx, cx + 1], [cy, cy], 'w', linewidth=3)
            elif y == self.height - 1:
                ax.plot([cx, cx + 1], [cy + 1, cy + 1], 'w', linewidth=3)

        open_wall(self.start.x, self.start.y)
        open_wall(self.end.x, self.end.y)

        # Draw the path if provided
        if path:
            px = [cell.x + 0.5 for cell in path]
            py = [self.height - cell.y - 0.5 for cell in path]
            ax.plot(px, py, color='red', linewidth=2)

        plt.show()

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

class BFSSolver:
    def solve_maze(self, maze: Maze) -> list[MazeCell]:
        return self.__solve(maze, maze.start, maze.end)
    
    def solve_graph(self, graph: Graph, start: int, end: int) -> list[Node]:
        start_node = graph.node_by_id(start)
        end_node = graph.node_by_id(end)
        return self.__solve(graph, start_node, end_node)

    def __solve(self, graph: Graph, start: Node, end: Node) -> list[Node]:
        queue = [start]
        visited = {start}
        parent = {start: None}

        adjacency = {node: [] for node in graph.nodes}
        for edge in graph.edges:
            adjacency[edge.start].append(edge.end)
            adjacency[edge.end].append(edge.start)

        while queue:
            current = queue.pop(0)
            if current == end:
                break

            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        path = []
        cur = end
        while cur is not None:
            path.append(cur)
            cur = parent.get(cur)
        path.reverse()

        return path