import json
import itertools
import sys
import secrets
import copy
from collections import defaultdict

from cfg import *
import hof

def make_lookup_sym(lookup):
    new_lookup = dict()
    for pair, value in lookup.items():
        new_lookup[pair] = value
        new_pair = (pair[1], pair[0])
        new_lookup[new_pair] = value
    return new_lookup

ADD_LOOKUP = {
    (-1, 0): {-1},
    (1, 0): {1},
    (0, 0): {0},
    (-1, -1): {-1},
    (-1, 1): {-1, 0, 1},
    (1, 1): {1}
}
ADD_LOOKUP = make_lookup_sym(ADD_LOOKUP)

MUL_LOOKUP = {
    (-1, 0): {0},
    (1, 0): {0},
    (0, 0): {0},
    (-1, -1): {1},
    (-1, 1): {-1},
    (1, 1): {1}
}
MUL_LOOKUP = make_lookup_sym(MUL_LOOKUP)

SUB_LOOKUP = {
    (-1, 0): {-1},
    (0, -1): {-1},
    (1, 0): {1},
    (0, 1): {1},
    (0, 0): {0},
    (-1, -1): {-1, 0, 1},
    (-1, 1): {-1},
    (1, -1): {-1},
    (1, 1): {-1, 0, 1}
}

def sign_analysis_merge(abstract_domains):
    final_abstract_domain = {}
    for domain in abstract_domains:
        for var, signs in domain.items():
            if var in final_abstract_domain:
                final_abstract_domain[var].update(copy.deepcopy(signs))
            else:
                final_abstract_domain[var] = copy.deepcopy(signs)
    return final_abstract_domain

def sign_analysis_transfer(block, abstract_domain):
    for instr in block:
        # init arg if not there (handle live-in vars, etc.)
        if "args" in instr:
            for arg in instr["args"]:
                if arg not in abstract_domain:
                    print('adding for arg:', arg)
                    abstract_domain[arg] = {-1, 0, 1}

        dest = instr.get("dest")

        if instr.get("op") == "const":
            print("const for", dest, instr["value"], type(instr["value"]))
            if instr["value"] == 0:
                abstract_domain[dest] = {0}
            elif instr["value"] < 0:
                abstract_domain[dest] = {-1}
            elif instr["value"] > 0:
                abstract_domain[dest] = {1}

        elif instr.get("op") == "add":
            left = copy.deepcopy(abstract_domain[instr["args"][0]])
            right = copy.deepcopy(abstract_domain[instr["args"][1]])
            abstract_domain[dest] = set()
            print("add for", dest, left, right, abstract_domain[dest], instr["args"])
            for l, r in itertools.product(left, right):
                abstract_domain[dest] = abstract_domain[dest].union(ADD_LOOKUP[(l, r)])

        elif instr.get("op") == "mul":
            left = copy.deepcopy(abstract_domain[instr["args"][0]])
            right = copy.deepcopy(abstract_domain[instr["args"][1]])
            abstract_domain[dest] = set()
            for l, r in itertools.product(left, right):
                abstract_domain[dest] = abstract_domain[dest].union(MUL_LOOKUP[(l, r)])

        elif instr.get("op") == "sub":
            left = copy.deepcopy(abstract_domain[instr["args"][0]])
            right = copy.deepcopy(abstract_domain[instr["args"][1]])
            abstract_domain[dest] = set()
            for l, r in itertools.product(left, right):
                abstract_domain[dest] = abstract_domain[dest].union(SUB_LOOKUP[(l, r)])

        elif dest: # unhandled, e.g. call
            print("unhandled", dest, instr)
            abstract_domain[dest] = {-1, 0, 1}

    return abstract_domain

def forwards_worklist_algo(cfg, init, merge, transfer):
    in_df = dict()
    in_df[cfg.entry()[0]] = copy.deepcopy(init)

    out_df = dict()
    for id, block in cfg.iter_blocks():
        out_df[id] = init

    worklist = list(cfg.iter_blocks())
    while len(worklist):
        id_b, b = worklist.pop()
        print("popping one off . . .", id_b)
        orig_out = copy.deepcopy(out_df[id_b])

        in_df[id_b] = merge(out_df[id_p] for id_p in cfg.pred(id_b))
        out_df[id_b] = transfer(b, in_df[id_b])
        if out_df[id_b] != orig_out:
            for id_s in cfg.succ(id_b):
                worklist.append((id_s, cfg.blocks[id_s]))
    return out_df

def sign_analysis(cfg):
    # return forwards_worklist_algo(cfg, dict(), sign_analysis_merge, sign_analysis_transfer)
    return forwards_worklist_algo(cfg, defaultdict(lambda: {-1, 0, 1}), sign_analysis_merge, sign_analysis_transfer)

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    for func in program["functions"]:
        blocks, labels_map = get_blocks(func)
        prog_cfg = get_cfg(blocks, labels_map)
        print(f"Number of blocks in function {func['name']} is {len(blocks)}")
        print(prog_cfg)
        print("analysis", sign_analysis(prog_cfg), "\n")
        print(func)
