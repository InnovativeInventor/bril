import cfg
import copy
import json
import itertools
import sys
import os

ORDINARY_OPS = [
    "mul",
    "id",
    "lt",
    "add",
    "const",
]

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)
    trace_filename = "bbs.trace"

    trace_info = []
    if os.path.isfile(trace_filename):
        with open(trace_filename) as f:
            for line in f:
                trace_info.append(json.loads(line))

    for func in program["functions"]:
        if func["name"] == "main":
            spec_counter = 0
            new_instrs = []
            for instr in func["instrs"]:
                if instr.get("label"):
                    new_instrs.append(instr)
                    continue

                traced_instr = trace_info.pop(0)
                if instr["op"] in ORDINARY_OPS:
                    new_instrs.append(instr)
                elif instr["op"] in ["print", "call", "jmp"]: # end speculation
                    # print("ended speculation", instr, traced_instr)
                    while spec_counter != 0:
                        new_instrs.append({"op" : "commit"})
                        spec_counter -= 1
                    new_instrs.append(instr)
                elif instr["op"] in ["br"]: # start speculation
                    spec_counter += 1
                    # print("started speculation", instr, traced_instr)
                    new_instrs.append({"op": "speculate"})

                    is_cond_true = str(trace_info.pop(0)).lower()
                    cond = True # default to speculating branches eval to true
                    if is_cond_true == "true":
                        cond = True
                    elif is_cond_true == "false":
                        cond = False
                    else:
                        print("is_cond_true failed to parse", is_cond_true)

                    new_instrs.append({"op" : "guard", "args" : instr["args"], "labels" : [instr["labels"][int(cond)]]})
                    new_instrs.append({"op" : "jmp", "labels" : [instr["labels"][int(not cond)]]})
                else:
                    # print("UNSUPPORTED OP", instr["op"])
                    new_instrs.append(instr)

            while spec_counter != 0:
                new_instrs.append({"op" : "commit"})
                spec_counter -= 1
            func["instrs"] = new_instrs

    print(json.dumps(program))
