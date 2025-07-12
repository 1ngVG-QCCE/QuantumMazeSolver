from qiskit import transpile
from qiskit_aer import AerSimulator
from maze.maze import Graph, Node, Maze
from maze.maze_circuit import QuantumMazeCircuit

class Path(list[int]):
    def __init__(self, l: list[int]):
        super().__init__()
        for e in l:
            self.append(e)

    def remove_cycles(self) -> 'Path':
        p = Path([])
        count = set()
        for x in self:
            if x in count:
                g = p.pop()
                while g != x:
                    count.discard(g)
                    g = p.pop()
            p.append(x)
            count.add(x)
        return p

    def __repr__(self):
        if len(self) > 0:
            s = [repr(e) for e in self]
            return '[' + str.join(' -> ', s) + ']'
        else:
            return '[]'
    def __hash__(self):
        return hash(repr(self))

class QuantumMazeSolver:
    def __result_to_path(self, result: str, num_nodes_in_max_path: int, node_size: int) -> Path:
        path = []
        for i in range(num_nodes_in_max_path):
            offset = i*node_size
            n = int(result[offset : offset+node_size], 2)
            path.insert(0, n)
        return Path(path)
    
    def run(self, circuit: QuantumMazeCircuit, shots: int = 1) -> list[Path]:
        sim = AerSimulator()
        transpiled = transpile(circuit, sim)
        transpiled.measure(range(len(circuit.clbits)), range(len(circuit.clbits)))
        results = sim.run(transpiled, shots=shots, memory=True).result().get_memory()
        paths = [self.__result_to_path(r, circuit.info.num_nodes_in_max_path, circuit.info.bits_per_node) for r in results]
        return paths 
     

class BFSSolver:
    def solve(self, graph: Graph) -> list[int]:
        start = graph.start
        end = graph.end
        queue = [graph.start]
        visited = {graph.start}
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
            path.append(cur.id)
            cur = parent.get(cur)
        path.reverse()

        return path