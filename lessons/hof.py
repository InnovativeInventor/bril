def apply_local_analysis(blocks, f):
    new_blocks = {}
    for block_id, block in blocks.items():
        new_blocks[block_id] = f(block)
    return new_blocks

def apply_local_analysis_cvg(blocks, f):
    size = len(blocks.values())
    new_blocks = apply_local_analysis(blocks, f)
    new_size = len(new_blocks.values())
    while new_size != size:
        new_blocks = apply_local_analysis(blocks, f)

    return new_blocks

