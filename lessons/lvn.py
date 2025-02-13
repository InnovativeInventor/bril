import json
import itertools
import sys
import secrets

import cfg
import hof

def lvn(block):
    table = {}
    var2num = {}
    instrs = []

    current_num = -1
    for instr_cnt, instr in enumerate(block):
        # Construct value
        if "op" not in instr: # probably a label
            instrs.append(instr)
            continue

        value_l = [instr["op"]]
        if "value" in instr:
            value_l.append(str(instr["value"]))

        if "args" in instr:
            for a in instr["args"]:
                if a in var2num:
                    print(a, file=sys.stderr)
                    value_l.append(var2num[a])
                else: # live-in var
                    current_num += 1
                    var2num[a] = current_num
                    table[((a))] = a
                    value_l.append(var2num[a])
        value = tuple(value_l)

        if value in table:
            instrs.append(
                {
                    "args": [ table[value] ],
                    "dest": instr["dest"],
                    "op": "id",
                    "type": instr["type"]
                }
            )
            for i, val in enumerate(table.values()):
                if val == value:
                    found = True
                    var2num[instr["dest"]] = i
                    break

        else:
            if "args" in instr:
                new_args = []
                for a in instr["args"]:
                    if a in var2num:
                        print(table, file=sys.stderr)
                        print("looking up:", a, var2num[str(a)], list(table.values())[var2num[a]], file = sys.stderr)
                        new_args.append(list(table.values())[var2num[str(a)]])
                    else:
                        print("fail loudly")
                instr["args"] = new_args

            if "dest" in instr:
                current_num += 1
                dest = instr["dest"]
                var2num[instr["dest"]] = current_num

                # Will be overwritten later
                for future_instr in block[instr_cnt+1:]:
                    if future_instr.get("dest") == dest:
                        dest = secrets.token_hex(8)
                        break

                table[value] = dest
                instr["dest"] = dest
                var2num[instr["dest"]] = current_num

            instrs.append(instr)

    return instrs

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    new_funcs = []
    for prog_func in program["functions"]:
        blocks, labels_map = cfg.get_blocks(prog_func)
        lvn_blocks = hof.apply_local_analysis(blocks, lvn)

        new_func = prog_func
        new_func["instrs"] = list(itertools.chain(*lvn_blocks.values()))
        new_funcs.append(new_func)
    program["functions"] = new_funcs
    print(json.dumps(program))
