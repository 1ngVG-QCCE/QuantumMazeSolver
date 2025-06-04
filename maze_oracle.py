# Imports

from qiskit import QuantumCircuit
from qiskit.circuit.library import XGate, ZGate
from PIL import Image as im
import requests
import base64
import matplotlib.pyplot as plt
import numpy as np
import io

# Utility classes

Edge = tuple[int, int]

class MazeOracleGenerator:

    def __init__(self, total_nodes: int, max_path_length: int | None = None, directed_graph: bool = False):
        self.__node_bits_size = int(np.ceil( np.log2(total_nodes) ))
        self.__max_path_length = max_path_length if max_path_length else total_nodes - 1
        self.__directed_graph = directed_graph
        self.__edges = []
        self.__first_node = None
        self.__last_node = None

    def add_edges(self, edges: list[Edge]) -> 'MazeOracleGenerator':
        self.__edges += edges
        return self

    def add_edge(self, edge: Edge) -> 'MazeOracleGenerator':
        self.add_edges([edge])
        return self
    
    def set_first_node(self, node: int) -> 'MazeOracleGenerator':
        self.__first_node = node
        return self
    
    def set_last_node(self, node: int) -> 'MazeOracleGenerator':
        self.__last_node = node
        return self
    
    def __generate_edge_check_circuit(self, edges: list, directed_graph: bool):
        size = self.__node_bits_size

        circ = QuantumCircuit((2 * size) + 1, name='Edge Check')
        def map_edge(from_node: int, to_node: int):
            target_qubit = (2 * size)
            def add_x(number, start_qubit):
                exp = 1
                for qubit in range(start_qubit, start_qubit + size):
                    if not (number & exp):
                        circ.x(qubit)
                    exp *= 2

            add_x(from_node, 0)
            add_x(to_node, size)
            circ.append(XGate().control(size * 2), list(range((2 * size))) + [target_qubit])
            add_x(from_node, 0)
            add_x(to_node, size)

        for e in edges:
            map_edge(e[0], e[1])
            circ.barrier()

            if not directed_graph:
                map_edge(e[1], e[0])
                circ.barrier()

        return circ

    def generate(self):
        num_qubit_in_path = (self.__max_path_length + 1) * self.__node_bits_size
        total_size = num_qubit_in_path + self.__max_path_length

        # generate circuit for edge checking on whole graph
        full_edge_check = QuantumCircuit(total_size, name='Full Edge Check')
        starting_check = 0
        ending_check = self.__max_path_length

        # first node special check
        if self.__first_node is not None:
            first_edge_check = self.__generate_edge_check_circuit(filter(lambda e: e[0] == self.__first_node, self.__edges), True)
            starting_check = 1
            full_edge_check.append(first_edge_check, list(range(2 * self.__node_bits_size)) + [num_qubit_in_path])

        # last node special check
        if self.__last_node is not None:
            last_edge_check  = self.__generate_edge_check_circuit(filter(lambda e: e[1] == self.__last_node, self.__edges), True)
            ending_check = self.__max_path_length - 1
            start_qubit = ending_check * self.__node_bits_size
            full_edge_check.append(last_edge_check, list(range(start_qubit, start_qubit + 2 * self.__node_bits_size)) + [num_qubit_in_path + ending_check])

        # all other nodes check
        edge_check = self.__generate_edge_check_circuit(self.__edges, self.__directed_graph)
        for s in range(starting_check, ending_check):
            start_qubit = s * self.__node_bits_size
            full_edge_check.append(edge_check, list(range(start_qubit, start_qubit + 2 * self.__node_bits_size)) + [num_qubit_in_path + s])
        
        circ = QuantumCircuit(total_size, name='Maze Oracle')
        circ.append(full_edge_check, range(total_size))                                                 # apply graph check
        circ.append(ZGate().control(self.__max_path_length - 1), range(num_qubit_in_path, total_size))  # flip correct combination
        circ.append(full_edge_check, range(total_size))                                                 # re-apply graph check (to reset ancillas)
        return circ
