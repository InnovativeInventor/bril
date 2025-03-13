import cfg
import copy
import json
import itertools
import sys
import to_ssa

def from_ssa(instrs, ty_map):
    new_instrs = []
    for instr in instrs:
        new_instr = copy.deepcopy(instr)
        if instr.get("op") == "set":
            a = instr.get("args")[1]
            asgn = instr.get("args")[0]
            new_instr = {"dest": asgn, "args": [a], "op": "id", "type": ty_map[a]}
            ty_map[asgn] = ty_map[a]
            new_instrs.append(new_instr)
        elif instr.get("op") == "get":
            continue
        else:
            new_instrs.append(new_instr)
    return new_instrs

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    new_funcs = []
    for func in program["functions"]:
        blocks, labels_map = cfg.get_blocks(func)
        assigned_vars = to_ssa.get_assigned_vars_bl(blocks)

        ty_map = {v:ty for (v, ty) in assigned_vars}
        func_args = []
        if "args" in func:
            for arg in func["args"]:
                ty_map[arg["name"]] = arg["type"]
                func_args.append(arg["name"])

        new_func = func
        new_func["instrs"] = from_ssa(func["instrs"], ty_map) 
        new_funcs.append(new_func)

    program["functions"] = new_funcs
    print(json.dumps(program))
