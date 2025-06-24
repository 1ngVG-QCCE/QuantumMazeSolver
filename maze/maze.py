import matplotlib.pyplot as plt
import utils.Helpers as hp

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
    def __init__(self, nodes: set[Node], start: Node, end: Node, edges: list[Edge] = None):
        self.__nodes = nodes
        if start in nodes:
            self.__start = start
        else:
            raise ValueError(f"Start node {start} is not in the graph nodes")
        if end in nodes:
            self.__end = end
        else:
            raise ValueError(f"End node {end} is not in the graph nodes")
        if edges is None:
            self.__edges = []
        else:
            self.__edges = list(edges)

    @property
    def nodes(self) -> frozenset[Node]:
        return frozenset(self.__nodes)

    @property
    def edges(self) -> frozenset[Edge]:
        return frozenset(self.__edges)
    
    @property
    def start(self) -> Node:
        return self.__start
    
    @property
    def end(self) -> Node:
        return self.__end
    
    @property
    def total_nodes(self) -> int:
        return len(self.nodes)
    
    @staticmethod
    def from_edges(edges: list[tuple[int, int]], start: int, end: int, bidirectional: bool = False) -> 'Graph':
        graph = Graph(list(map(lambda node_id: Node(node_id), list(set([node_id for edge in edges for node_id in edge])))), Node(start), Node(end))
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

    def show(self, path: list[int] = None):
        mermaid_lines = ["flowchart LR;"]
        for edge in self.edges:
            mermaid_lines.append(f"    n{edge.start.id} --> n{edge.end.id};")
        if path:
            path = [self.node_by_id(cell_id) for cell_id in path]
            for start, end in zip(path, path[1:]):
                mermaid_lines.append(f"    ns{start.id} --> ns{end.id};")
        hp.mm("\n".join(mermaid_lines))
 
class Maze(Graph):
    def __init__(self, width: int, height: int, start: tuple[int, int] = (0, 0), end: tuple[int, int] = None):
        self.__width = width
        self.__height = height
        if end is None:
            end = (width - 1, height - 1)
        if not self.__coordinate_on_boundary(*start):
            raise ValueError(f"Start {start} must be on the maze boundary")
        if not self.__coordinate_on_boundary(*end):
            raise ValueError(f"End {end} must be on the maze boundary")
        nodes = [MazeCell(y * width + x, x, y) for y in range(height) for x in range(width)]
        edges = []    
        coord_to_node = {(node.x, node.y): node for node in nodes}

        super().__init__(nodes, coord_to_node[start], coord_to_node[end], edges)

    def __coordinate_on_boundary(self, x: int, y: int) -> bool:
        return x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1

    @property
    def width(self) -> int:
        return self.__width 
    
    @property
    def height(self) -> int:
        return self.__height
    
    @property
    def start(self) -> MazeCell:
        return super().start
    
    @property
    def end(self) -> MazeCell:
        return super().end
    
    @property
    def nodes(self) -> frozenset[MazeCell]:
        return super().nodes
        
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

        def open_wall(node: MazeCell):
            if node.x == 0: # connect to the left
                new_connection = {(node.x, node.y), (node.x - 1, node.y)}
            elif node.x == self.width - 1: # connect to the right
                new_connection = {(node.x, node.y), (node.x + 1, node.y)}
            elif node.y == 0: # connect to the top
                new_connection = {(node.x, node.y), (node.x, node.y - 1)}
            elif node.y == self.height - 1: # connect to the bottom  
                new_connection = {(node.x, node.y), (node.x, node.y + 1)}
            return new_connection    

        connections = {frozenset({(e.start.x, e.start.y), (e.end.x, e.end.y)}) for e in self.edges}
        connections.add(frozenset(open_wall(self.start)))
        connections.add(frozenset(open_wall(self.end)))

        def wall_exists(x1, y1, x2, y2):
            return frozenset({(x1, y1), (x2, y2)}) not in connections

        for y in range(self.height):
            for x in range(self.width):
                cx, cy = x, self.height - y - 1
                if wall_exists(x, y, x, y - 1):  # North
                    ax.plot([cx, cx + 1], [cy + 1, cy + 1], 'k')
                if wall_exists(x, y, x - 1, y):  # West
                    ax.plot([cx, cx], [cy, cy + 1], 'k')
                if wall_exists(x, y, x, y + 1):  # South
                    ax.plot([cx, cx + 1], [cy, cy], 'k')
                if wall_exists(x, y, x + 1, y):  # East
                    ax.plot([cx + 1, cx + 1], [cy, cy + 1], 'k')

        if path:
            cells = [self.node_by_id(cell_id) for cell_id in path]
            px = [cell.x + 0.5 for cell in cells]
            py = [self.height - cell.y - 0.5 for cell in cells]
            ax.plot(px, py, color='red', linewidth=2)

        plt.show()
