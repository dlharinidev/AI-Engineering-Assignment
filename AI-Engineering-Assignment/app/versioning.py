import difflib
import uuid

def match_nodes_v1_v2(v1_nodes, v2_nodes):
    """Match nodes between version 1 and version 2.
    Args:
        v1_nodes: List of ORM Node objects from version 1.
        v2_nodes: List of dicts produced by the parser for version 2.
    Returns:
        List of v2 node dicts enriched with 'logical_node_id' and 'is_stale' flags.
    """
    # Build a lookup based on (level, heading) for quick matching.
    v1_map = {(n.level, n.heading): n for n in v1_nodes}
    updated_nodes = []
    for v2_node in v2_nodes:
        key = (v2_node['level'], v2_node['heading'])
        if key in v1_map:
            # Existing node – preserve logical ID.
            v1_node = v1_map[key]
            v2_node['logical_node_id'] = v1_node.logical_node_id
            # Determine staleness based on content hash.
            v2_node['is_stale'] = v1_node.content_hash != v2_node['content_hash']
        else:
            # New node – generate a fresh logical ID.
            v2_node['logical_node_id'] = str(uuid.uuid4())
            v2_node['is_stale'] = False
        updated_nodes.append(v2_node)
    return updated_nodes

def get_diff(text1: str, text2: str):
    """Generates a lightweight diff summary."""
    d = difflib.Differ()
    diff = list(d.compare(text1.splitlines(), text2.splitlines()))
    return "\n".join([line for line in diff if line.startswith('+ ') or line.startswith('- ')])