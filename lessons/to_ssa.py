import cfg
import copy
import json
import itertools
import sys

def get_incoming_vars(block, func_args):
    assigned_vars = set()
    used_vars = set()
    for instr in block:
        if args := instr.get("args"):
            for arg in args:
                if (arg not in assigned_vars):
                    used_vars.add(arg)
        if dst := instr.get("dest"):
            assigned_vars.add(dst)
    return list(used_vars)

def get_assigned_vars(block):
    assigned_vars = []
    for instr in block:
        if dst := instr.get("dest"):
            assigned_vars.append((dst, instr.get("type")))
    return assigned_vars

def get_assigned_vars_bl(blocks):
    assigned_vars = []
    for block in blocks.values():
        for instr in block:
            if dst := instr.get("dest"):
                assigned_vars.append((dst, instr.get("type")))
    return assigned_vars

def to_ssa(blocks, func_vars, ty_map, labels_map, control_flow_graph):
    new_blocks = []
    first = True
    for blk_id, block in blocks.items():
        new_block = []
        v_map = dict()

        if first: # if at top of func
            for a in func_vars:
                for blk_id in blocks.keys():
                    new_block.append(
                        {"args": [f"{a}.{blk_id}.0", a], "op" : "set"}
                    )
                    v_map[a] = 0
            first = False

        # print("incoming before", get_incoming_vars(block, func_vars), block, func_vars)
        if len(block) and cfg.is_label(block[0]):
            new_block.append(copy.deepcopy(block[0]))
            block = copy.deepcopy(block[1:])
        # print("incoming after", get_incoming_vars(block, func_vars), block, func_vars)

        for v in get_incoming_vars(block, func_vars):
            private_name_start = f"{v}.{blk_id}.0"
            v_map[v] = 0
            new_block.append({"args": [], "dest": private_name_start, "op": "get", "type": ty_map[v]})

        terminated = False
        for instr in block:
            if cfg.is_terminator(instr):
                terminated = True
                for set_var, _ in get_assigned_vars(block):
                    for other_blk_id in blocks.keys():
                        new_block.append({"args": [f"{set_var}.{other_blk_id}.0", f"{set_var}.{blk_id}.{v_map[set_var]}"], "op" : "set"})

            new_instr = copy.deepcopy(instr)
            if args := instr.get("args"):
                new_args = []
                for a in args:
                    if a in v_map:
                        new_args.append(f"{a}.{blk_id}.{v_map[a]}")
                    elif a in func_vars:
                        v_map[a] = 0
                        new_args.append(f"{a}.{blk_id}.0")
                    else:
                        raise ValueError("new arg ugh")

                new_instr["args"] = new_args

            if dst := instr.get("dest"):
                if dst in v_map:
                    v_map[dst] += 1
                    dst_name = f"{dst}.{blk_id}.{v_map[dst]}"
                else:
                    dst_name = f"{dst}.{blk_id}.0"
                    v_map[dst] = 0

                new_instr["dest"] = dst_name

            new_block.append(new_instr)

        if not terminated:
            for set_var, _ in get_assigned_vars(block):
                for other_blk_id in blocks.keys():
                    new_block.append({"args": [f"{set_var}.{other_blk_id}.0", f"{set_var}.{blk_id}.{v_map[set_var]}"], "op" : "set"})

        new_blocks.append(new_block)
    return new_blocks

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    new_funcs = []
    for func in program["functions"]:
        blocks, labels_map = cfg.get_blocks(func)
        control_flow_graph = cfg.get_cfg(blocks, labels_map)
        # print(blocks)
        assigned_vars = get_assigned_vars_bl(blocks)
        func_args = []
        ty_map = {v:ty for (v, ty) in assigned_vars}
        if "args" in func:
            for arg in func["args"]:
                ty_map[arg["name"]] = arg["type"]
                func_args.append(arg["name"])
        ssa_instrs = list(itertools.chain(*to_ssa(blocks, func_args, ty_map, labels_map, control_flow_graph)))

        new_func = func
        new_func["instrs"] = ssa_instrs
        new_funcs.append(new_func)

    program["functions"] = new_funcs
    print(json.dumps(program))
