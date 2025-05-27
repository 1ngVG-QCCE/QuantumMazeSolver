from qiskit import QuantumCircuit
from qiskit.circuit.library import XGate, MCMT
from qiskit.quantum_info import Statevector


def convert_path_to_statevector(path: list[int], node_bits_size: int = 2) -> Statevector:
    return Statevector.from_label(''.join(['0' for _ in range(len(path) - 1)]) + ''.join([('{0:0' + str(node_bits_size) + 'b}').format(n) for n in path[::-1]]))


class GraphCircuitBuilder:

    def __init__(self, node_bits_size: int, max_steps_count: int, directed_graph: bool = False):
        self.__node_bits_size = node_bits_size
        self.__max_steps_count = max_steps_count
        self.__directed_graph = directed_graph
        self.__edges = []
        self.__start_node = None
        self.__last_node = None
        self.__do_init_superpositions = False

    def add_edges(self, edges: list[tuple]) -> 'GraphCircuitBuilder':
        self.__edges += edges
        return self

    def add_edge(self, edge: tuple[int]) -> 'GraphCircuitBuilder':
        self.add_edges([edge])
        return self

    def __negate(self, num_qubits: int) -> QuantumCircuit:
        n = QuantumCircuit(num_qubits)
        for i in range(num_qubits):
            n.z(i)
            n.x(i)
            n.z(i)
            n.x(i)
        return n
    
    @staticmethod
    def __number_to_binary_string(number: int, bits: int = 2) -> str:
        return ('{0:0' + str(bits) + 'b}').format(number)
    
    def __generate_graph_mapping_circuit(self):
        circ = QuantumCircuit((2 * self.__node_bits_size) + 1, name='Graph Verify')
        def map_edge(from_node: int, to_node: int):
            target_qubit = (2 * self.__node_bits_size)
            circ.append(XGate().control(
                self.__node_bits_size * 2,
                ctrl_state=self.__number_to_binary_string(to_node, self.__node_bits_size) + self.__number_to_binary_string(from_node, self.__node_bits_size)),
                list(range((2 * self.__node_bits_size))) + [target_qubit])
        for e in self.__edges:
            map_edge(e[0], e[1])
            circ.barrier()
            if not self.__directed_graph:
                map_edge(e[1], e[0])
                circ.barrier()
        return circ
    
    def set_start_node(self, start_node: int) -> 'GraphCircuitBuilder':
        self.__start_node = start_node
        return self

    def set_last_node(self, last_node: int) -> 'GraphCircuitBuilder':
        self.__last_node = last_node
        return self

    def init_superpositions(self, init_superporitions: bool = True) -> 'GraphCircuitBuilder':
        self.__do_init_superpositions = init_superporitions
        return self
    
    def __hardcode_node_initialization(self, circ: QuantumCircuit, node: int, start_qubit: int) -> QuantumCircuit:
        exp = 1
        for qubit in range(start_qubit, start_qubit + self.__node_bits_size):
            if node & exp:
                circ.x(qubit)
            exp *= 2
        return circ

    def __init_superpositions(self, circ) -> QuantumCircuit:
        for i in range(self.__node_bits_size, self.__max_steps_count * self.__node_bits_size):
            circ.h(i)
        return circ

    def generate(self):
        steps_qubit_count = (self.__max_steps_count + 1) * self.__node_bits_size
        circ = QuantumCircuit(steps_qubit_count + self.__max_steps_count)
        if self.__do_init_superpositions:
            circ = self.__init_superpositions(circ)
        if self.__start_node is not None:
            circ = self.__hardcode_node_initialization(circ, self.__start_node, 0)
        if self.__last_node is not None:
            circ = self.__hardcode_node_initialization(circ, self.__last_node, self.__max_steps_count * self.__node_bits_size)
        graph_circ = self.__generate_graph_mapping_circuit()
        for s in range(self.__max_steps_count):
            start_qubit = s * self.__node_bits_size
            circ.append(graph_circ, list(range(start_qubit, start_qubit + 2 * self.__node_bits_size)) + [steps_qubit_count + s])
        self.flip_circ = MCMT(self.__negate(1), self.__max_steps_count, steps_qubit_count)
        self.flip_circ.name = 'Flip'
        circ.append(self.flip_circ, list(range(steps_qubit_count, steps_qubit_count + self.__max_steps_count)) + list(range(steps_qubit_count)))
        return circ
