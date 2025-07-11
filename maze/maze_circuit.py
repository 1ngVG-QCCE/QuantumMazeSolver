from qiskit import QuantumCircuit
from qiskit.circuit.library import XGate, ZGate, GroverOperator
import numpy as np
from maze.maze import Graph, Edge
from qiskit import QuantumCircuit

class MazeCircuitInfo:
    def __init__(self, graph: Graph, max_path_length: int = None):
        self.__graph = graph
        self.__max_path_length = max_path_length if max_path_length else graph.total_nodes - 1
        self.__num_nodes_in_max_path = self.__max_path_length + 1
        self.__bits_per_node = int(np.ceil(np.log2(graph.total_nodes)))
        self.__num_qubits_in_max_path = (self.__num_nodes_in_max_path) * self.__bits_per_node

    @property
    def graph(self) -> Graph:
        return self.__graph
    @property
    def max_path_length(self) -> int:
        return self.__max_path_length 
    @property
    def num_nodes_in_max_path(self) -> int:
        return self.__num_nodes_in_max_path  
    @property
    def bits_per_node(self) -> int:
        return self.__bits_per_node
    @property
    def num_qubits_in_max_path(self) -> int:
        return self.__num_qubits_in_max_path

class GroverDiffusionOperator(QuantumCircuit):
    def __init__(self, n_qubits: int):
        super().__init__(n_qubits, name="Grover Operator")
        self.h(range(n_qubits))
        self.x(range(n_qubits))
        self.append(ZGate().control(n_qubits - 1), range(n_qubits))
        self.x(range(n_qubits))
        self.h(range(n_qubits))

class MazeOracle(QuantumCircuit):
    def __init__(self, maze_circuit_info: MazeCircuitInfo, turn_back_check: bool = False):
        self.__maze_circuit_info = maze_circuit_info
        self.__turn_back_check = turn_back_check
        self.__num_ancillas = self.__maze_circuit_info.max_path_length
        if turn_back_check:
            self.__num_ancillas += self.__maze_circuit_info.max_path_length - 1
        self.__total_size = self.__maze_circuit_info.num_qubits_in_max_path + self.__num_ancillas
        super().__init__(self.__total_size, name='Maze Oracle')
        self.__generate()

        
    # maps the x-gates on the correct bits, given the number
    def __node_to_binary(self, number):
        number_of_qubits = self.__maze_circuit_info.bits_per_node
        quantum_circuit = QuantumCircuit(number_of_qubits, name=f'Node {number} to Binary')
        bitmask = 1
        for qubit in range(number_of_qubits):
            if not (number & bitmask):
                quantum_circuit.x(qubit)
            bitmask <<= 1 # shift bitmask left)
        return quantum_circuit
    
    # encodes the nodes of an edge with their binary quantum circuit representation
    def __encode_edge_nodes(self, from_node: int, to_node: int):
        number_of_qubits_for_a_node = self.__maze_circuit_info.bits_per_node
        number_of_qubits_for_two_nodes = 2 * number_of_qubits_for_a_node
        quantum_circuit = QuantumCircuit(number_of_qubits_for_two_nodes, name=f'Edge Encoder {from_node} -> {to_node}')
        quantum_circuit.append(self.__node_to_binary(from_node), range(number_of_qubits_for_a_node))
        quantum_circuit.append(self.__node_to_binary(to_node), range(number_of_qubits_for_a_node, number_of_qubits_for_two_nodes))
        return quantum_circuit

    # checks if an edge is valid (input: pair of nodes, output: ancilla)
    def __map_edge(self, from_node: int, to_node: int):
        number_of_qubits_for_a_node = self.__maze_circuit_info.bits_per_node
        ancilla_index = number_of_qubits_for_two_nodes = 2 * number_of_qubits_for_a_node
        quantum_circuit = QuantumCircuit(number_of_qubits_for_two_nodes + 1, name=f'Edge Check {from_node} -> {to_node}')
        edge_encoder_quantum_circuit = self.__encode_edge_nodes(from_node, to_node)
              
        quantum_circuit.append(edge_encoder_quantum_circuit, range(number_of_qubits_for_two_nodes))
        quantum_circuit.append(XGate().control(number_of_qubits_for_two_nodes), list(range(number_of_qubits_for_two_nodes)) + [ancilla_index])
        quantum_circuit.append(edge_encoder_quantum_circuit.inverse(), range(number_of_qubits_for_two_nodes))

        return quantum_circuit
       
    # creates the circuit for all edges check, given a list of edges
    def __generate_edge_check_circuit(self, edges: list[Edge]):
        number_of_qubits_for_two_nodes = 2 * self.__maze_circuit_info.bits_per_node
        total_size = number_of_qubits_for_two_nodes + 1
        quantum_circuit = QuantumCircuit(total_size, name='Edge Check Circuit')
        for e in edges:
            quantum_circuit.append(self.__map_edge(e.start.id, e.end.id), range(total_size))
            quantum_circuit.barrier()
        return quantum_circuit
    
    # check if the nodes are equal 
    def __generate_turn_back_check_circuit(self):
        number_of_qubits_for_a_node = self.__maze_circuit_info.bits_per_node
        ancilla_index = number_of_qubits_for_three_nodes = 3 * number_of_qubits_for_a_node
        total_size = number_of_qubits_for_three_nodes + 1
        circ = QuantumCircuit(total_size, name='Turn Back Check')

        # first check: two nodes are different
        different_nodes_check_circuit = QuantumCircuit(number_of_qubits_for_three_nodes, name='Different Nodes Check')
        for i in range(number_of_qubits_for_a_node):
            different_nodes_check_circuit.cx(i, i + 2 * number_of_qubits_for_a_node)
            different_nodes_check_circuit.x(i + 2 * number_of_qubits_for_a_node)

        circ.append(different_nodes_check_circuit, range(number_of_qubits_for_three_nodes))    
        circ.append(XGate().control(number_of_qubits_for_a_node), range(2*number_of_qubits_for_a_node, total_size))
        circ.x(ancilla_index)
        circ.append(different_nodes_check_circuit.inverse(), range(number_of_qubits_for_three_nodes))    

        # second check: first node is equal to the last node
        last_id = self.__maze_circuit_info.graph.end.id
        circ.append(self.__node_to_binary(last_id), range(number_of_qubits_for_a_node))
        circ.append(self.__node_to_binary(last_id), range(number_of_qubits_for_a_node, 2*number_of_qubits_for_a_node))
        circ.append(XGate().control(2*number_of_qubits_for_a_node), list(range(2*number_of_qubits_for_a_node)) + [ancilla_index])
        circ.append(self.__node_to_binary(last_id), range(number_of_qubits_for_a_node, 2*number_of_qubits_for_a_node))
        circ.append(self.__node_to_binary(last_id), range(number_of_qubits_for_a_node))

        return circ

    def __generate(self):
        full_edge_check = QuantumCircuit(self.__total_size, name='Full Edge Check')
        edges = list(self.__maze_circuit_info.graph.edges)

        # add self-cycle to last node (for termination)
        edges.append(Edge(self.__maze_circuit_info.graph.end, self.__maze_circuit_info.graph.end))
        last_edge_check  = self.__generate_edge_check_circuit(filter(lambda e: e.end == self.__maze_circuit_info.graph.end, edges)) # only check edges containing the last node
        last_edge_check_ancilla = self.__maze_circuit_info.num_qubits_in_max_path + self.__maze_circuit_info.max_path_length - 1
        full_edge_check.append(last_edge_check, list(range(self.__maze_circuit_info.num_qubits_in_max_path - 2 * self.__maze_circuit_info.bits_per_node, self.__maze_circuit_info.num_qubits_in_max_path)) + [last_edge_check_ancilla])

        first_edge_check = self.__generate_edge_check_circuit(filter(lambda e: e.start == self.__maze_circuit_info.graph.start, edges)) # only check edges containing the first node
        first_edge_check_ancilla = self.__maze_circuit_info.num_qubits_in_max_path
        full_edge_check.append(first_edge_check, list(range(2 * self.__maze_circuit_info.bits_per_node)) + [first_edge_check_ancilla]) 

        edge_check = self.__generate_edge_check_circuit(edges) # check all other edges
        for s in range(1, self.__maze_circuit_info.max_path_length - 1):
            start_qubit    = s * self.__maze_circuit_info.bits_per_node
            full_edge_check.append(edge_check, list(range(start_qubit, start_qubit + 2 * self.__maze_circuit_info.bits_per_node)) + [self.__maze_circuit_info.num_qubits_in_max_path + s])

        if self.__turn_back_check:
            turn_back_check = self.__generate_turn_back_check_circuit()
            for s in range(1, self.__maze_circuit_info.max_path_length):
                start_qubit    = s * self.__maze_circuit_info.bits_per_node
                previous_qubit = (s-1) * self.__maze_circuit_info.bits_per_node
                next_qubit     = (s+1) * self.__maze_circuit_info.bits_per_node
                full_edge_check.append(turn_back_check, list(range(previous_qubit, next_qubit + self.__maze_circuit_info.bits_per_node)) + [self.__maze_circuit_info.max_path_length + self.__maze_circuit_info.num_qubits_in_max_path + s - 1])

        self.append(full_edge_check, range(self.__total_size))
        self.append(ZGate().control(self.__num_ancillas - 1), range(self.__maze_circuit_info.num_qubits_in_max_path, self.__total_size))
        self.append(full_edge_check.inverse(), range(self.__total_size)) 

class QuantumMazeCircuit(Graph, QuantumCircuit):
    def __init__(self, graph: Graph, max_path_length: int = None, turn_back_check: bool = False, number_of_solutions: int = 1):
        self.__info = MazeCircuitInfo(graph, max_path_length)
        oracle = MazeOracle(self.__info, turn_back_check)
        grover_operator = GroverDiffusionOperator(self.info.num_qubits_in_max_path)
        
        grover_iteration_circuit = QuantumCircuit(len(oracle.qubits), name='Grover Iteration')
        grover_iteration_circuit.append(oracle, range(len(oracle.qubits)))  
        grover_iteration_circuit.append(grover_operator, range(self.info.num_qubits_in_max_path))

        QuantumCircuit.__init__(self, len(oracle.qubits), self.info.num_qubits_in_max_path) # init quantum circuit
        self.name = 'Maze Solver'
        
        iterations = int(np.ceil((np.pi / 4) * np.sqrt((2 ** self.info.num_qubits_in_max_path) / number_of_solutions )))
        for i in range(self.info.num_qubits_in_max_path):
            self.h(i)

        for i in range(iterations):
            self.barrier()
            self.append(grover_iteration_circuit, range(len(oracle.qubits)))  

    @property
    def info(self) -> int:
        return self.__info
    
    def __getattr__(self, name):
        return getattr(self.info.graph, name)


