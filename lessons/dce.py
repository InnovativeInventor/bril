import json
import itertools
import sys

import cfg
import hof

def dce(blocks):
    instrs = []
    used_vars_l = []

    for block in blocks.values():
        for instr in block:
            if "args" in instr:
                used_vars_l.extend(instr["args"])
    used_vars = set(used_vars_l)

    new_blocks = {}
    for id, block in blocks.items():
        new_block = []
        for instr in block:
            if "dest" in instr and instr["dest"] not in used_vars:
                print(instr, file=sys.stderr)
                continue
            else:
                new_block.append(instr)
        new_blocks[id] = new_block
    return new_blocks

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    new_funcs = []
    for prog_func in program["functions"]:
        size = 0
        blocks, labels_map = cfg.get_blocks(prog_func)

        while size != len(list(itertools.chain(*blocks.values()))):
            blocks = dce(blocks)
            size = len(list(itertools.chain(*blocks.values())))

        new_func = prog_func
        new_func["instrs"] = list(itertools.chain(*blocks.values()))
        new_funcs.append(new_func)

    program["functions"] = new_funcs
    print(json.dumps(program))
