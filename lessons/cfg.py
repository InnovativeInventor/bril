import json
import sys
from enum import Enum
from dataclasses import dataclass

TERMINATORS = [
    "call", 
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

def get_blocks(func):
    # Get the basic blocks of a program.
    blocks = {}
    labels_map = {}
    id = 0
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
                labels_map[instr["label"]] = id
                block = []
            block.append(instr)
        else:
            block.append(instr)
    if len(block):
        blocks[id] = block
        id += 1
    return blocks, labels_map

def get_cfg(blocks, labels_map):
    cfg = {}
    for id, block in blocks.items():
        cfg[id] = set()

        # Check if empty
        if block:
            terminator = block[-1]

            if terminator.get("op") == "jmp":
                for label in terminator["labels"]:
                    cfg[id].add(labels_map[label])
            elif terminator.get("op") == "br":
                for label in terminator["labels"]:
                    cfg[id].add(labels_map[label])

        # Fallthrough
        if id + 1 < len(blocks):
            cfg[id].add(id + 1)
    return cfg


if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    for func in program["functions"]:
        blocks, labels_map = get_blocks(func)
        cfg = get_cfg(blocks, labels_map)
        print(f"Number of blocks in function {func['name']} is {len(blocks)}")
        print(cfg)
        print(func)
