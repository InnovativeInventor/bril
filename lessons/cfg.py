import json
import itertools
import sys
from enum import Enum
from dataclasses import dataclass

TERMINATORS = [
#     "call", 
    "jmp", 
    "ret",
    "br",
]

def is_op(instruction) -> bool:
    if instruction.get("op"):
        return True
    return False

def is_terminator(instruction) -> bool:
    if instruction.get("op") in TERMINATORS:
        return True
    return False

def is_label(instruction) -> bool:
    if instruction.get("label"):
        return True
    return False

def get_blocks(func, blocks = False, labels_map = False, id=0):
    # Get the basic blocks of a program.
    if not isinstance(blocks, dict):
        blocks = {}
    if not isinstance(labels_map, dict):
        labels_map = {}

    block = []
    for instr in func["instrs"]:
        if is_terminator(instr):
            block.append(instr)
            blocks[id] = block
            id += 1
            block = []
        elif is_label(instr):
            if len(block):
                blocks[id] = block
                id += 1
                block = []
            labels_map[instr["label"]] = id
            block.append(instr)
        else:
            block.append(instr)
    if len(block):
        blocks[id] = block
        id += 1
    return blocks, labels_map

def get_prog_blocks(program):
    blocks = False
    labels_map = False
    id = 0
    for func in program["functions"]:
        blocks, labels_map = get_blocks(func, blocks = blocks, labels_map = labels_map, id = id)
        print(blocks, labels_map)
        id = len(blocks)

    return blocks, labels_map

def reconstruct_func(prog_func, labels_map, new_blocks):
    if len(labels_map.items()):
        new_instrs = []
        for label, loc in labels_map.items():
            new_instrs.extend(new_blocks[loc])
        prog_func["instrs"] = new_instrs
    else:
        prog_func["instrs"] = list(itertools.chain(*new_blocks.values()))
    return prog_func

class CFG:
    def __init__(self, blocks, labels_map, succ_map):
        self.blocks = blocks
        self.labels_map = labels_map
        self.succ_map = succ_map

        self.pred_map = {}
        for node, succs in self.succ_map.items():
            for succ in succs:
                if succ not in self.pred_map:
                    self.pred_map[succ] = set()
                self.pred_map[succ].add(node)

    def __str__(self):
        return f'Blocks: {self.blocks}\nSucc map: {self.succ_map}\nPred map: {self.pred_map}'

    def iter_blocks(self):
        for id, block in self.blocks.items():
            yield (id, block)

    def pred(self, id: int):
        if id in self.pred_map:
            return self.pred_map[id]
        return set()

    def succ(self, id: int):
        return self.succ_map[id]

    def lookup(self, id: int):
        return self.blocks[id]

    def entry(self):
        # no longe true if doing whole program analysis...
        return (0, self.blocks[0])

    # def exit(self):
    #     # no longer true if blocks get modified while running
    #     return (-1, self.blocks[-1])

    def pre_order_traversal(self):
        traversal = []
        nodes_visited = set()
        nodes_to_visit = {self.entry()[0]}

        while nodes_to_visit:
            node_id = nodes_to_visit.pop()
            for neighbor in self.succ(node_id):
                if neighbor not in nodes_visited:
                    nodes_to_visit.add(neighbor)
            nodes_visited.add(node_id)
            traversal.append(node_id)

        return traversal

    def reverse_pre_order_traversal(self):
        return list(reversed(self.pre_order_traversal()))


def get_cfg(blocks, labels_map):
    succ_map = {}
    # succ_map[-1] = set() # exit
    for id, block in blocks.items():
        succ_map[id] = set()

        # Check if empty
        if block:
            terminator = block[-1]

            if terminator.get("op") == "jmp":
                for label in terminator["labels"]:
                    succ_map[id].add(labels_map[label])
            elif terminator.get("op") == "br":
                for label in terminator["labels"]:
                    succ_map[id].add(labels_map[label])
            # elif terminator.get("op") == "ret":
            #     succ_map[id].add(-1)

        # Fallthrough
        # if id + 2 < len(blocks):
        if id + 1 < len(blocks):
            succ_map[id].add(id + 1)

    # blocks.append([]) # dummy block

    return CFG(blocks, labels_map, succ_map)

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    for func in program["functions"]:
        blocks, labels_map = get_blocks(func)
        cfg = get_cfg(blocks, labels_map)
        print(f"Number of blocks in function {func['name']} is {len(blocks)}")
        print(cfg)
        print(func)
