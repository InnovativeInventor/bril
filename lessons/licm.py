import cfg
import json
import dom
import sys
import itertools
import copy

def natural_loops(control_flow_graph, dominator_tree):
    header = list(range(0, len(control_flow_graph)))
    # header = [-1] * len(control_flow_graph)
    worklist = [dominator_tree]
    visited = set()
    while len(worklist):
        # print(worklist, header)
        tree = worklist.pop(0)
        worklist.extend(copy.deepcopy(tree.children))

        rest_of_loop = set(control_flow_graph.pred(tree.id))
        visited.add(tree.id)

        while len(rest_of_loop):
            curr_node = rest_of_loop.pop()
            rest_of_loop = rest_of_loop.union(set(control_flow_graph.pred(curr_node))) - visited
            if curr_node not in visited:
                header[curr_node] = tree.id
            visited.add(curr_node)

    return header

def licm(loop_headers, control_flow_graph, dominator_tree):
    # assumes SSA
    for curr_block, curr_header in enumerate(loop_headers):
        if curr_block == curr_header:
            continue

        basic_block = control_flow_graph.lookup(curr_block)

        loop_invariant_defs = dict()

        # stupid way to iterate to convergence
        prev_loop_invariant = None
        while prev_loop_invariant != hash(str(sorted(loop_invariant_defs.items()))):
            prev_loop_invariant = hash(str(sorted(loop_invariant_defs.items())))
            for block_id, block_instrs in control_flow_graph.iter_blocks():
                if (curr_header == loop_headers[block_id] and 
                    block_id != curr_header): # inside of loop and not in header
                    for b_instr in block_instrs:
                        if b_instr.get("op") == "const":
                            loop_invariant_defs[b_instr["dest"]] = b_instr
                        elif (b_instr.get("dest") and b_instr.get("args") and
                                ("labels" not in b_instr) and
                                all([x in loop_invariant_defs.keys() for x in b_instr.get("args")])):
                            loop_invariant_defs[b_instr["dest"]] = b_instr
                else:
                    for b_instr in block_instrs:
                        if b_instr.get("dest"):
                            loop_invariant_defs[b_instr["dest"]] = b_instr
        # print("loop invariants!:", loop_invariant_defs)

        new_instrs = []
        for instr in basic_block:
            # detecting loop invariant expressions, assuming SSA
            if args := instr.get("args"):
                if all(x in loop_invariant_defs.keys() for x in args):
                    # add to header
                    control_flow_graph.blocks[curr_header].append(instr)
                    # print("licm applied!:", loop_invariant_defs.keys(), args,
                    #       instr.get("op"))
                elif (instr.get("op") == "set" and args[1] in
                    loop_invariant_defs.keys()):
                    # add to header
                    control_flow_graph.blocks[curr_header].append(instr)
                    # print("licm applied!:", loop_invariant_defs.keys(), args,
                    #       instr.get("op"))
                else:
                    # not loop invariant; keep calm and carry on
                    new_instrs.append(instr)
            else:
                new_instrs.append(instr)
        control_flow_graph.blocks[curr_block] = new_instrs 
    return control_flow_graph.blocks

if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    for func in program["functions"]:
        blocks, labels_map = cfg.get_blocks(func)
        control_flow_graph = cfg.get_cfg(blocks, labels_map)

        dominator_graph = dom.dom(control_flow_graph)
        dominator_tree = dom.construct_dom_tree(dominator_graph, control_flow_graph)

        loop_headers = natural_loops(control_flow_graph, dominator_tree)

        blocks = licm(loop_headers, control_flow_graph, dominator_tree)
        func["instrs"] = list(itertools.chain(*blocks.values()))

        # print("cfg", control_flow_graph)
        # print("dominator tree", dominator_tree)
        # print("nat loop headers", loop_headers)

    # program["functions"] = new_funcs
    print(json.dumps(program))
