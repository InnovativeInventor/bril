import copy
import json
import cfg
import sys

def dom(cfg):
    dom = dict()
    dom[cfg.entry()[0]] = {cfg.entry()[0]}

    traversal = cfg.reverse_pre_order_traversal()

    for id in traversal:
        if id not in dom:
            dom[id] = set()

    old_dom = dict()
    while old_dom != dom:
        old_dom = copy.deepcopy(dom)
        for v in traversal:
            if v == cfg.entry()[0]:
                continue

            if v not in dom:
                dom[v] = set()

            preds = list(dom[p] for p in cfg.pred(v))
            dom[v] = {v}.union(set.intersection(*preds))

    return dom

def invert_dom(dom):
    inv_dom = {}
    for id, doms in dom.items():
        for dominated_by in doms:
            if dominated_by not in inv_dom:
                inv_dom[dominated_by] = set()
            inv_dom[dominated_by].add(id)
    return inv_dom


def construct_dom_tree(dom, cfg):
    dom_copy = copy.deepcopy(invert_dom(dom))
    start_node = DominatorTree(cfg.entry()[0], [])
    nodes_to_visit = {start_node}

    for id in dom.keys():
        if start_node.id in dom[id]:
            dom[id].remove(start_node.id)

    while len(dom.keys()):
        current_node = nodes_to_visit.pop()
        if current_node.id in dom:
            del dom[current_node.id]

        for id in dom.keys():
            if len(dom[id]) == 1:
                for did in dom.keys():
                    if id in dom[did]:
                        dom[did].remove(id)
                new_subtree = DominatorTree(id, [])
                nodes_to_visit.add(new_subtree)
                current_node.children.append(new_subtree)
    return start_node

def dominance_frontier(dom, cfg):
    inverted_dom = invert_dom(dom)
    frontier = dict()

    for id, doms in inverted_dom.items():
        if id not in frontier:
            frontier[id] = set

        for succ in cfg.succ(id):
            if succ not in doms:
                frontier[id].add(succ)

    return frontier

class DominatorTree:
    def __init__(self, id, children):
        self.id = id
        self.children = children

    def __repr__(self):
        if self.children:
            return f"{self.id}({self.children})"
        else:
            return f"{self.id}"


if __name__ == "__main__":
    # Read program from stdin, following Bril's philosophy
    program = json.load(sys.stdin)

    for func in program["functions"]:
        blocks, labels_map = cfg.get_blocks(func)
        control_flow_graph = cfg.get_cfg(blocks, labels_map)
        print(f"Number of blocks in function {func['name']} is {len(blocks)}")
        print(control_flow_graph)
        dominator_graph = dom(control_flow_graph)
        print("doms", dominator_graph)
        print("inverted doms", invert_dom(dominator_graph))
        print("dom tree", construct_dom_tree(dominator_graph, control_flow_graph))
        print("dom frontier", dominance_frontier(dominator_graph, control_flow_graph))
