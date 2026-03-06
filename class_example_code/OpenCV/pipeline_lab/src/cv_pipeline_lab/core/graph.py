from __future__ import annotations

from collections import defaultdict, deque

from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.types import EdgeModel, PipelineModel


def _port_map(spec_ports):
    return {p.name: p.type for p in spec_ports}


def is_compatible(src_type: str, dst_type: str) -> bool:
    if src_type == dst_type:
        return True
    if dst_type == "meta":
        return True
    # Allow mask to image consumers; many nodes can auto-convert grayscale.
    if src_type == "mask" and dst_type == "image":
        return True
    return False


def validate_pipeline(pipeline: PipelineModel, registry: BlockRegistry) -> list[str]:
    errors: list[str] = []
    node_by_id = {n.id: n for n in pipeline.nodes}

    if len(node_by_id) != len(pipeline.nodes):
        errors.append("Duplicate node IDs detected.")

    for node in pipeline.nodes:
        if not registry.has(node.block_type):
            errors.append(f"Node {node.id}: unknown block type '{node.block_type}'.")

    source_types = {"ImageInput", "VideoFrameInput"}
    input_nodes = [n for n in pipeline.nodes if n.block_type in source_types and n.enabled]
    if len(input_nodes) != 1:
        errors.append(f"Exactly one enabled source node is required (ImageInput or VideoFrameInput). Found {len(input_nodes)}.")

    seen_edge_ids: set[str] = set()
    for edge in pipeline.edges:
        if edge.id in seen_edge_ids:
            errors.append(f"Duplicate edge ID: {edge.id}")
        seen_edge_ids.add(edge.id)

        if edge.src_node not in node_by_id:
            errors.append(f"Edge {edge.id}: unknown src_node '{edge.src_node}'.")
            continue
        if edge.dst_node not in node_by_id:
            errors.append(f"Edge {edge.id}: unknown dst_node '{edge.dst_node}'.")
            continue

        src_node = node_by_id[edge.src_node]
        dst_node = node_by_id[edge.dst_node]
        if not registry.has(src_node.block_type) or not registry.has(dst_node.block_type):
            continue

        src_spec = registry.get_spec(src_node.block_type)
        dst_spec = registry.get_spec(dst_node.block_type)

        src_ports = _port_map(src_spec.output_ports)
        dst_ports = _port_map(dst_spec.input_ports)

        if edge.src_port not in src_ports:
            errors.append(f"Edge {edge.id}: src_port '{edge.src_port}' not in outputs of {src_node.block_type}.")
            continue
        if edge.dst_port not in dst_ports:
            errors.append(f"Edge {edge.id}: dst_port '{edge.dst_port}' not in inputs of {dst_node.block_type}.")
            continue

        src_type = src_ports[edge.src_port]
        dst_type = dst_ports[edge.dst_port]
        if not is_compatible(src_type, dst_type):
            errors.append(
                f"Edge {edge.id}: type mismatch {src_type} -> {dst_type} ({src_node.block_type}.{edge.src_port} -> {dst_node.block_type}.{edge.dst_port})"
            )

    if not errors:
        try:
            _ = topological_sort(pipeline)
        except ValueError as exc:
            errors.append(str(exc))

    return errors


def topological_sort(pipeline: PipelineModel) -> list[str]:
    node_ids = [n.id for n in pipeline.nodes]
    indegree = {nid: 0 for nid in node_ids}
    adj: dict[str, list[str]] = defaultdict(list)

    for edge in pipeline.edges:
        if edge.src_node not in indegree or edge.dst_node not in indegree:
            continue
        adj[edge.src_node].append(edge.dst_node)
        indegree[edge.dst_node] += 1

    q = deque(sorted([nid for nid, deg in indegree.items() if deg == 0]))
    order: list[str] = []

    while q:
        nid = q.popleft()
        order.append(nid)
        for nxt in sorted(adj.get(nid, [])):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    if len(order) != len(node_ids):
        raise ValueError("Graph has at least one cycle; DAG required.")

    return order


def inbound_edges_by_node(edges: list[EdgeModel]) -> dict[str, list[EdgeModel]]:
    mapping: dict[str, list[EdgeModel]] = defaultdict(list)
    for e in edges:
        mapping[e.dst_node].append(e)
    return mapping


def outbound_edges_by_node(edges: list[EdgeModel]) -> dict[str, list[EdgeModel]]:
    mapping: dict[str, list[EdgeModel]] = defaultdict(list)
    for e in edges:
        mapping[e.src_node].append(e)
    return mapping
