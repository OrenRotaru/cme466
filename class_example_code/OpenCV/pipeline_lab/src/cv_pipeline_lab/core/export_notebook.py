from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from cv_pipeline_lab.core.graph import topological_sort
from cv_pipeline_lab.core.registry import BlockRegistry
from cv_pipeline_lab.core.types import BlockSpec, EdgeModel, NodeModel, PipelineModel


def _slug(text: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    if not out:
        return "node"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


def _merged_params(spec: BlockSpec, node: NodeModel) -> dict[str, Any]:
    merged = {p.name: p.default for p in spec.params}
    merged.update(node.params or {})
    return merged


def _inbound_by_node_and_port(edges: list[EdgeModel], node_ids: set[str]) -> dict[str, dict[str, EdgeModel]]:
    grouped: dict[str, dict[str, EdgeModel]] = defaultdict(dict)
    for edge in sorted(edges, key=lambda e: e.id):
        if edge.src_node not in node_ids or edge.dst_node not in node_ids:
            continue
        grouped[edge.dst_node].setdefault(edge.dst_port, edge)
    return grouped


def _reachable_from_inputs(pipeline: PipelineModel, registry: BlockRegistry) -> set[str]:
    node_by_id = {n.id: n for n in pipeline.nodes}
    enabled_compute_ids = {n.id for n in pipeline.nodes if n.enabled and not registry.get_spec(n.block_type).is_concept}

    out_edges: dict[str, list[EdgeModel]] = defaultdict(list)
    for edge in pipeline.edges:
        if edge.src_node in enabled_compute_ids and edge.dst_node in enabled_compute_ids:
            out_edges[edge.src_node].append(edge)

    source_types = {"ImageInput", "VideoFrameInput"}
    q = deque([n.id for n in pipeline.nodes if n.enabled and n.block_type in source_types])
    reachable: set[str] = set()
    while q:
        nid = q.popleft()
        if nid in reachable or nid not in enabled_compute_ids:
            continue
        reachable.add(nid)
        for edge in out_edges.get(nid, []):
            if edge.dst_node not in reachable:
                q.append(edge.dst_node)
    return reachable


def _exportable_order(pipeline: PipelineModel, registry: BlockRegistry) -> tuple[list[str], dict[str, dict[str, EdgeModel]], list[str]]:
    node_by_id = {n.id: n for n in pipeline.nodes}
    try:
        order = topological_sort(pipeline)
    except Exception:  # noqa: BLE001
        order = [n.id for n in pipeline.nodes]

    reachable = _reachable_from_inputs(pipeline, registry)
    inbound = _inbound_by_node_and_port(pipeline.edges, reachable)
    selected: list[str] = []
    selected_set: set[str] = set()
    skipped_missing_inputs: list[str] = []

    for nid in order:
        if nid not in reachable:
            continue
        node = node_by_id[nid]
        if not node.enabled:
            continue
        spec = registry.get_spec(node.block_type)
        if spec.is_concept:
            continue

        missing = False
        for port in spec.input_ports:
            edge = inbound.get(nid, {}).get(port.name)
            if edge is None:
                missing = True
                break
            if edge.src_node not in selected_set:
                missing = True
                break
        if missing:
            skipped_missing_inputs.append(node.title or node.id)
            continue

        selected.append(nid)
        selected_set.add(nid)

    filtered_inbound = {
        nid: {p: e for p, e in port_edges.items() if e.src_node in selected_set and nid in selected_set}
        for nid, port_edges in inbound.items()
    }
    return selected, filtered_inbound, skipped_missing_inputs


def _build_var_map(order: list[str], node_by_id: dict[str, NodeModel], registry: BlockRegistry) -> dict[tuple[str, str], str]:
    counts: dict[str, int] = defaultdict(int)
    mapping: dict[tuple[str, str], str] = {}

    for nid in order:
        node = node_by_id[nid]
        spec = registry.get_spec(node.block_type)
        base = _slug(node.title or spec.title or node.block_type)
        counts[base] += 1
        if counts[base] > 1:
            base = f"{base}_{counts[base]}"

        single_output = len(spec.output_ports) == 1
        for port in spec.output_ports:
            if single_output:
                mapping[(nid, port.name)] = base
            else:
                mapping[(nid, port.name)] = f"{base}_{port.name}"
    return mapping


def _line_or_default(src: dict[str, str], key: str, default: str) -> str:
    return src.get(key, default)


def _render_block_code(
    node: NodeModel,
    spec: BlockSpec,
    params: dict[str, Any],
    input_vars: dict[str, str],
    output_vars: dict[str, str],
) -> str:
    lines: list[str] = [f"# {node.title or spec.title} ({node.block_type})"]

    if node.block_type == "ImageInput":
        out_image = output_vars["image"]
        image_path = str(params.get("image_path", "")).strip()
        lines.extend(
            [
                f"image_path = {image_path!r}",
                f"{out_image} = cv2.imread(str(Path(image_path).expanduser()))",
                f"if {out_image} is None:",
                "    raise FileNotFoundError(f'Unable to load image: {image_path}')",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "VideoFrameInput":
        out_image = output_vars["image"]
        out_meta = output_vars.get("meta", "video_meta")
        source = str(params.get("source", "0")).strip()
        api = int(params.get("api_preference", 0))
        frame_index = int(params.get("frame_index", 0))
        set_width = int(params.get("set_width", 0))
        set_height = int(params.get("set_height", 0))
        set_fps = float(params.get("set_fps", 0.0))
        lines.extend(
            [
                f"video_source = {source!r}",
                "source_obj = int(video_source) if str(video_source).isdigit() else str(Path(video_source).expanduser())",
                f"_cap = cv2.VideoCapture(source_obj{', ' + str(api) if api > 0 else ''})",
                "if not _cap.isOpened():",
                "    raise ValueError(f'Unable to open video source: {video_source}')",
                f"if {set_width} > 0:",
                f"    _cap.set(cv2.CAP_PROP_FRAME_WIDTH, {set_width})",
                f"if {set_height} > 0:",
                f"    _cap.set(cv2.CAP_PROP_FRAME_HEIGHT, {set_height})",
                f"if {set_fps} > 0:",
                f"    _cap.set(cv2.CAP_PROP_FPS, {set_fps})",
                f"if {frame_index} > 0:",
                f"    _cap.set(cv2.CAP_PROP_POS_FRAMES, {frame_index})",
                f"_ok, {out_image} = _cap.read()",
                "_cap.release()",
                f"if (not _ok) or ({out_image} is None):",
                "    raise RuntimeError('VideoCapture read failed')",
                f"{out_meta} = {{'source': video_source, 'frame_index': {frame_index}, 'width': int({out_image}.shape[1]), 'height': int({out_image}.shape[0])}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ImageOutputPreview":
        lines.append(f"{output_vars['image']} = ensure_bgr({_line_or_default(input_vars, 'image', 'image')})")
        return "\n".join(lines)

    if node.block_type == "SaveImage":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_meta = output_vars.get("meta", "save_meta")
        output_path = str(params.get("output_path", "")).strip()
        lines.extend(
            [
                f"{out_img} = ensure_bgr({in_img})",
                f"save_path = {output_path!r}",
                "if not save_path:",
                "    save_path = 'saved_image.png'",
                "save_path = str(Path(save_path).expanduser())",
                "Path(save_path).parent.mkdir(parents=True, exist_ok=True)",
                f"if not cv2.imwrite(save_path, {out_img}):",
                "    raise RuntimeError(f'Failed to save image: {save_path}')",
                f"{out_meta} = {{'saved_path': save_path}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "SplitImage":
        in_img = _line_or_default(input_vars, "image", "image")
        lines.extend(
            [
                f"_split_img = ensure_bgr({in_img})",
                f"{output_vars['image_a']} = _split_img.copy()",
                f"{output_vars['image_b']} = _split_img.copy()",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "MergeImage":
        a = _line_or_default(input_vars, "image_a", "image_a")
        b = _line_or_default(input_vars, "image_b", "image_b")
        out = output_vars["image"]
        mode = str(params.get("mode", "hconcat"))
        alpha = float(params.get("alpha", 0.5))
        lines.extend(
            [
                f"_merge_a = ensure_bgr({a})",
                f"_merge_b = ensure_bgr({b})",
                f"merge_mode = {mode!r}",
                f"alpha = {alpha}",
                "if merge_mode == 'choose_a':",
                f"    {out} = _merge_a",
                "elif merge_mode == 'choose_b':",
                f"    {out} = _merge_b",
                "elif merge_mode == 'alpha':",
                "    if _merge_a.shape != _merge_b.shape:",
                "        _merge_b = cv2.resize(_merge_b, (_merge_a.shape[1], _merge_a.shape[0]))",
                f"    {out} = cv2.addWeighted(_merge_a, 1.0 - alpha, _merge_b, alpha, 0)",
                "elif merge_mode == 'vconcat':",
                "    w = min(_merge_a.shape[1], _merge_b.shape[1])",
                "    a2 = cv2.resize(_merge_a, (w, int(_merge_a.shape[0] * w / _merge_a.shape[1])))",
                "    b2 = cv2.resize(_merge_b, (w, int(_merge_b.shape[0] * w / _merge_b.shape[1])))",
                f"    {out} = cv2.vconcat([a2, b2])",
                "else:",
                "    h = min(_merge_a.shape[0], _merge_b.shape[0])",
                "    a2 = cv2.resize(_merge_a, (int(_merge_a.shape[1] * h / _merge_a.shape[0]), h))",
                "    b2 = cv2.resize(_merge_b, (int(_merge_b.shape[1] * h / _merge_b.shape[0]), h))",
                f"    {out} = cv2.hconcat([a2, b2])",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "DrawDetections":
        in_img = _line_or_default(input_vars, "image", "image")
        in_det = _line_or_default(input_vars, "detections", "detections")
        out = output_vars["image"]
        show_label = bool(params.get("show_label", True))
        show_score = bool(params.get("show_score", True))
        lines.extend(
            [
                f"{out} = ensure_bgr({in_img}).copy()",
                f"draw_detections = {in_det} or []",
                f"show_label = {show_label}",
                f"show_score = {show_score}",
                "for det in draw_detections:",
                "    if isinstance(det, dict):",
                "        x, y, w, h = det.get('bbox', (0, 0, 0, 0))",
                "        label = str(det.get('label', 'obj'))",
                "        score = float(det.get('score', 1.0))",
                "    else:",
                "        x, y, w, h = getattr(det, 'bbox', (0, 0, 0, 0))",
                "        label = str(getattr(det, 'label', 'obj'))",
                "        score = float(getattr(det, 'score', 1.0))",
                "    x, y, w, h = int(x), int(y), int(w), int(h)",
                f"    cv2.rectangle({out}, (x, y), (x + w, y + h), (0, 255, 0), 2)",
                "    text = ''",
                "    if show_label:",
                "        text += label",
                "    if show_score:",
                "        text += (' ' if text else '') + f'{score:.2f}'",
                "    if text:",
                f"        cv2.putText({out}, text, (x, max(10, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ApplyMask":
        in_img = _line_or_default(input_vars, "image", "image")
        in_mask = _line_or_default(input_vars, "mask", "mask")
        out = output_vars["image"]
        lines.extend(
            [
                f"_apply_img = ensure_bgr({in_img})",
                f"_apply_mask = ensure_gray({in_mask})",
                f"{out} = cv2.bitwise_and(_apply_img, _apply_img, mask=_apply_mask)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ContourCount":
        in_img = _line_or_default(input_vars, "image", "image")
        in_det = _line_or_default(input_vars, "detections", "detections")
        out_img = output_vars["image"]
        out_det = output_vars.get("detections", "detections_out")
        out_meta = output_vars.get("meta", "contour_count_meta")
        label_filter = str(params.get("label_filter", "contour")).strip()
        exact_match = bool(params.get("exact_match", True))
        annotate = bool(params.get("annotate", False))
        title_prefix = str(params.get("title_prefix", "Contours")).strip() or "Contours"
        lines.extend(
            [
                f"{out_img} = ensure_bgr({in_img}).copy()",
                f"{out_det} = list({in_det} or [])",
                f"label_filter = {label_filter!r}",
                f"exact_match = {exact_match}",
                "contour_count = 0",
                f"for _det in ({in_det} or []):",
                "    if isinstance(_det, dict):",
                "        _label = str(_det.get('label', ''))",
                "    else:",
                "        _label = str(getattr(_det, 'label', ''))",
                "    if not label_filter:",
                "        contour_count += 1",
                "    elif exact_match and _label == label_filter:",
                "        contour_count += 1",
                "    elif (not exact_match) and label_filter.lower() in _label.lower():",
                "        contour_count += 1",
                "print(f'Contour count: {contour_count}')",
                f"if {annotate}:",
                f"    cv2.putText({out_img}, f\"{title_prefix}: {{contour_count}}\", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)",
                f"{out_meta} = {{",
                "    'contour_count': contour_count,",
                "    'label_filter': label_filter,",
                "    'exact_match': exact_match,",
                f"    'total_detections': len({in_det} or []),",
                "}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ChannelSplit":
        in_img = _line_or_default(input_vars, "image", "image")
        b_var = output_vars["image_b"]
        g_var = output_vars["image_g"]
        r_var = output_vars["image_r"]
        lines.extend(
            [
                f"_split_src = ensure_bgr({in_img})",
                "_b, _g, _r = cv2.split(_split_src)",
                f"{b_var} = cv2.cvtColor(_b, cv2.COLOR_GRAY2BGR)",
                f"{g_var} = cv2.cvtColor(_g, cv2.COLOR_GRAY2BGR)",
                f"{r_var} = cv2.cvtColor(_r, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ChannelMerge":
        b_var = _line_or_default(input_vars, "image_b", "image_b")
        g_var = _line_or_default(input_vars, "image_g", "image_g")
        r_var = _line_or_default(input_vars, "image_r", "image_r")
        out = output_vars["image"]
        lines.extend(
            [
                f"_mb = ensure_gray({b_var})",
                f"_mg = ensure_gray({g_var})",
                f"_mr = ensure_gray({r_var})",
                "if _mb.shape != _mg.shape or _mb.shape != _mr.shape:",
                "    raise ValueError('ChannelMerge expects equal channel image sizes')",
                f"{out} = cv2.merge([_mb, _mg, _mr])",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "PSNRCompare":
        a_var = _line_or_default(input_vars, "image_a", "image_a")
        b_var = _line_or_default(input_vars, "image_b", "image_b")
        out_img = output_vars["image"]
        out_meta = output_vars.get("meta", "psnr_meta")
        r = float(params.get("r", 255.0))
        use_b = bool(params.get("use_b_as_output", False))
        lines.extend(
            [
                f"_psnr_a = ensure_bgr({a_var})",
                f"_psnr_b = ensure_bgr({b_var})",
                "if _psnr_a.shape != _psnr_b.shape:",
                "    _psnr_b = cv2.resize(_psnr_b, (_psnr_a.shape[1], _psnr_a.shape[0]), interpolation=cv2.INTER_LINEAR)",
                f"psnr_value = float(cv2.PSNR(_psnr_a, _psnr_b, {r}))",
                "print(f'PSNR: {psnr_value:.4f} dB')",
                f"{out_img} = _psnr_b if {use_b} else _psnr_a",
                f"{out_meta} = {{'psnr': psnr_value, 'r': {r}}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "GrayConvert":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_mask = output_vars["mask"]
        lines.extend(
            [
                f"{out_mask} = ensure_gray({in_img})",
                f"{out_img} = cv2.cvtColor({out_mask}, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ColorConvert":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        mode = str(params.get("mode", "bgr2hsv"))
        lines.extend(
            [
                "color_mode_map = {",
                "    'bgr2rgb': cv2.COLOR_BGR2RGB,",
                "    'bgr2hsv': cv2.COLOR_BGR2HSV,",
                "    'bgr2lab': cv2.COLOR_BGR2LAB,",
                "    'rgb2bgr': cv2.COLOR_RGB2BGR,",
                "    'hsv2bgr': cv2.COLOR_HSV2BGR,",
                "    'lab2bgr': cv2.COLOR_LAB2BGR,",
                "}",
                f"color_mode = {mode!r}",
                f"{out_img} = cv2.cvtColor(ensure_bgr({in_img}), color_mode_map.get(color_mode, cv2.COLOR_BGR2HSV))",
                f"if {out_img}.ndim == 2:",
                f"    {out_img} = cv2.cvtColor({out_img}, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "PreprocessPipeline":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        alpha = float(params.get("alpha", 1.0))
        beta = int(params.get("beta", 0))
        gamma = float(params.get("gamma", 1.0))
        gray = bool(params.get("gray", False))
        equalize = bool(params.get("equalize_hist", False))
        blur_k = int(params.get("blur_k", 1))
        lines.extend(
            [
                f"{out} = ensure_bgr({in_img})",
                f"alpha = {alpha}",
                f"beta = {beta}",
                f"gamma = {gamma}",
                f"force_gray = {gray}",
                f"equalize_hist = {equalize}",
                f"blur_k = odd_ksize({blur_k}, 1)",
                f"{out} = cv2.convertScaleAbs({out}, alpha=alpha, beta=beta)",
                f"{out} = gamma_correct({out}, gamma)",
                "if blur_k > 1:",
                f"    {out} = cv2.GaussianBlur({out}, (blur_k, blur_k), 0)",
                "if force_gray:",
                f"    g = cv2.cvtColor({out}, cv2.COLOR_BGR2GRAY)",
                "    if equalize_hist:",
                "        g = cv2.equalizeHist(g)",
                f"    {out} = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)",
                "elif equalize_hist:",
                f"    ycrcb = cv2.cvtColor({out}, cv2.COLOR_BGR2YCrCb)",
                "    ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])",
                f"    {out} = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ResizeImage":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        mode = str(params.get("mode", "dsize"))
        interpolation = str(params.get("interpolation", "linear"))
        interp_code = {
            "nearest": "cv2.INTER_NEAREST",
            "linear": "cv2.INTER_LINEAR",
            "area": "cv2.INTER_AREA",
            "cubic": "cv2.INTER_CUBIC",
            "lanczos4": "cv2.INTER_LANCZOS4",
        }.get(interpolation, "cv2.INTER_LINEAR")
        lines.extend(
            [
                f"_resize_img = ensure_bgr({in_img})",
                f"resize_mode = {mode!r}",
            ]
        )
        if mode == "scale":
            fx = max(0.01, float(params.get("fx", 1.0)))
            fy = max(0.01, float(params.get("fy", 1.0)))
            lines.extend([f"{out} = cv2.resize(_resize_img, None, fx={fx}, fy={fy}, interpolation={interp_code})"])
        else:
            w = max(1, int(params.get("width", 640)))
            h = max(1, int(params.get("height", 480)))
            lines.extend([f"{out} = cv2.resize(_resize_img, ({w}, {h}), interpolation={interp_code})"])
        return "\n".join(lines)

    if node.block_type == "ImageCrop":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        out_meta = output_vars.get("meta", "crop_meta")
        x = int(params.get("x", 0))
        y = int(params.get("y", 0))
        width = int(params.get("width", 0))
        height = int(params.get("height", 0))
        lines.extend(
            [
                f"_crop_img = ensure_bgr({in_img})",
                "_h, _w = _crop_img.shape[:2]",
                f"x = max(0, min(_w - 1, {x}))",
                f"y = max(0, min(_h - 1, {y}))",
                f"crop_w = {width}",
                f"crop_h = {height}",
                "if crop_w <= 0:",
                "    crop_w = _w - x",
                "if crop_h <= 0:",
                "    crop_h = _h - y",
                "x2 = min(_w, x + max(1, crop_w))",
                "y2 = min(_h, y + max(1, crop_h))",
                "if x2 <= x or y2 <= y:",
                "    raise ValueError('Invalid crop rectangle')",
                f"{out} = _crop_img[y:y2, x:x2].copy()",
                f"{out_meta} = {{",
                "    'crop_box': {'x': x, 'y': y, 'width': x2 - x, 'height': y2 - y},",
                "    'source_size': {'width': _w, 'height': _h},",
                "}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ContrastAdjustment":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        alpha = float(params.get("alpha", 1.2))
        beta = int(params.get("beta", 0))
        lines.extend(
            [
                f"alpha = {alpha}",
                f"beta = {beta}",
                f"{out} = cv2.convertScaleAbs(ensure_bgr({in_img}), alpha=alpha, beta=beta)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "LogTransform":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        gain = float(params.get("gain", 1.0))
        normalize = bool(params.get("normalize", True))
        lines.extend(
            [
                f"gain = {gain}",
                f"normalize = {normalize}",
                f"_log_img = ensure_bgr({in_img}).astype(np.float32)",
                "c = (255.0 / np.log(256.0)) * gain",
                f"{out} = c * np.log1p(_log_img)",
                "if normalize:",
                f"    {out} = cv2.normalize({out}, None, 0, 255, cv2.NORM_MINMAX)",
                f"{out} = np.clip({out}, 0, 255).astype(np.uint8)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "GammaTransform":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        gamma = max(0.01, float(params.get("gamma", 1.0)))
        gain = float(params.get("gain", 1.0))
        lines.extend(
            [
                f"gamma = {gamma}",
                f"gain = {gain}",
                f"_gamma_img = ensure_bgr({in_img}).astype(np.float32) / 255.0",
                f"{out} = gain * np.power(_gamma_img, gamma) * 255.0",
                f"{out} = np.clip({out}, 0, 255).astype(np.uint8)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "InRangeMask":
        in_img = _line_or_default(input_vars, "image", "image")
        out_mask = output_vars["mask"]
        out_img = output_vars["image"]
        color_space = str(params.get("color_space", "hsv"))
        code = {
            "bgr": None,
            "hsv": "cv2.COLOR_BGR2HSV",
            "rgb": "cv2.COLOR_BGR2RGB",
            "gray": "cv2.COLOR_BGR2GRAY",
        }.get(color_space, "cv2.COLOR_BGR2HSV")
        low0 = int(params.get("low_0", 0))
        low1 = int(params.get("low_1", 0))
        low2 = int(params.get("low_2", 0))
        high0 = int(params.get("high_0", 255))
        high1 = int(params.get("high_1", 255))
        high2 = int(params.get("high_2", 255))
        lines.extend(
            [
                f"_range_src = ensure_bgr({in_img})",
                f"color_space = {color_space!r}",
                f"_range_proc = _range_src if color_space == 'bgr' else cv2.cvtColor(_range_src, {code})",
                f"low = [{low0}, {low1}, {low2}]",
                f"high = [{high0}, {high1}, {high2}]",
                "if _range_proc.ndim == 2:",
                "    lowerb = np.array([low[0]], dtype=np.uint8)",
                "    upperb = np.array([high[0]], dtype=np.uint8)",
                "else:",
                "    lowerb = np.array(low[: _range_proc.shape[2]], dtype=np.uint8)",
                "    upperb = np.array(high[: _range_proc.shape[2]], dtype=np.uint8)",
                f"{out_mask} = cv2.inRange(_range_proc, lowerb, upperb)",
                f"{out_img} = cv2.bitwise_and(_range_src, _range_src, mask={out_mask})",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "DenoiseBlur":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        method = str(params.get("method", "box"))
        border = {
            "default": "cv2.BORDER_DEFAULT",
            "reflect": "cv2.BORDER_REFLECT",
            "replicate": "cv2.BORDER_REPLICATE",
            "constant": "cv2.BORDER_CONSTANT",
            "reflect101": "cv2.BORDER_REFLECT_101",
        }
        lines.extend([f"_blur_img = ensure_bgr({in_img})", f"blur_method = {method!r}"])
        if method == "gaussian":
            kx = int(params.get("gauss_ksize_x", 5))
            ky = int(params.get("gauss_ksize_y", 5))
            sx = float(params.get("gauss_sigma_x", 1.2))
            sy = float(params.get("gauss_sigma_y", 0.0))
            bc = border.get(str(params.get("gauss_border", "default")), "cv2.BORDER_DEFAULT")
            lines.extend(
                [
                    f"kx = odd_ksize({kx}, 1)",
                    f"ky = odd_ksize({ky}, 1)",
                    f"sigma_x = {sx}",
                    f"sigma_y = {sy}",
                    f"{out} = cv2.GaussianBlur(_blur_img, (kx, ky), sigmaX=sigma_x, sigmaY=sigma_y, borderType={bc})",
                ]
            )
        elif method == "median":
            k = int(params.get("median_ksize", 5))
            lines.extend(
                [
                    f"k = odd_ksize({k}, 3)",
                    f"{out} = cv2.medianBlur(_blur_img, k)",
                ]
            )
        elif method == "bilateral":
            d = max(1, int(params.get("bilateral_d", 9)))
            sc = float(params.get("bilateral_sigma_color", 80.0))
            ss = float(params.get("bilateral_sigma_space", 80.0))
            bc = border.get(str(params.get("bilateral_border", "default")), "cv2.BORDER_DEFAULT")
            lines.extend(
                [
                    f"d = {d}",
                    f"sigma_color = {sc}",
                    f"sigma_space = {ss}",
                    f"{out} = cv2.bilateralFilter(_blur_img, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space, borderType={bc})",
                ]
            )
        else:
            kx = max(1, int(params.get("box_ksize_x", 5)))
            ky = max(1, int(params.get("box_ksize_y", 5)))
            normalize = bool(params.get("box_normalize", True))
            bc = border.get(str(params.get("box_border", "default")), "cv2.BORDER_DEFAULT")
            lines.extend(
                [
                    f"kx = {kx}",
                    f"ky = {ky}",
                    f"normalize = {normalize}",
                    f"{out} = cv2.boxFilter(_blur_img, ddepth=-1, ksize=(kx, ky), normalize=normalize, borderType={bc})",
                ]
            )
        return "\n".join(lines)

    if node.block_type == "Filter2D":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        ddepth_name = str(params.get("ddepth", "-1"))
        ddepth_code = {
            "-1": "-1",
            "cv_8u": "cv2.CV_8U",
            "cv_16u": "cv2.CV_16U",
            "cv_16s": "cv2.CV_16S",
            "cv_32f": "cv2.CV_32F",
            "cv_64f": "cv2.CV_64F",
        }.get(ddepth_name, "-1")
        kernel_json = str(params.get("kernel_json", "[[0,-1,0],[-1,5,-1],[0,-1,0]]")).strip()
        border_code = {
            "default": "cv2.BORDER_DEFAULT",
            "constant": "cv2.BORDER_CONSTANT",
            "reflect": "cv2.BORDER_REFLECT",
            "replicate": "cv2.BORDER_REPLICATE",
            "reflect101": "cv2.BORDER_REFLECT_101",
        }.get(str(params.get("border_type", "default")), "cv2.BORDER_DEFAULT")
        anchor_x = int(params.get("anchor_x", -1))
        anchor_y = int(params.get("anchor_y", -1))
        delta = float(params.get("delta", 0.0))
        lines.extend(
            [
                f"_f2d_src = ensure_bgr({in_img})",
                f"kernel_json = {kernel_json!r}",
                "kernel = np.array(json.loads(kernel_json), dtype=np.float32)",
                "if kernel.ndim != 2 or kernel.size == 0:",
                "    raise ValueError('kernel_json must decode to a non-empty 2D matrix')",
                f"{out_img} = cv2.filter2D(_f2d_src, ddepth={ddepth_code}, kernel=kernel, "
                f"anchor=({anchor_x}, {anchor_y}), delta={delta}, borderType={border_code})",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "Sharpen":
        in_img = _line_or_default(input_vars, "image", "image")
        out = output_vars["image"]
        method = str(params.get("method", "laplacian"))
        ksize = int(str(params.get("kernel_size", "3")))
        alpha = float(params.get("alpha", 1.0))
        blend = float(params.get("blend", 0.4))
        lines.extend(
            [
                f"_sharp_img = ensure_bgr({in_img})",
                "_gray = cv2.cvtColor(_sharp_img, cv2.COLOR_BGR2GRAY)",
                f"method = {method!r}",
                f"ksize = {ksize}",
                f"alpha = {alpha}",
                f"blend = {blend}",
                "if method == 'gradient':",
                "    gx = cv2.Sobel(_gray, cv2.CV_32F, 1, 0, ksize=ksize)",
                "    gy = cv2.Sobel(_gray, cv2.CV_32F, 0, 1, ksize=ksize)",
                "    mag = cv2.magnitude(gx, gy)",
                "    mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)",
                "    grad_vis = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)",
                f"    {out} = cv2.addWeighted(_sharp_img, 1.0 - blend, grad_vis, blend, 0)",
                "else:",
                "    lap = cv2.Laplacian(_gray, cv2.CV_32F, ksize=ksize)",
                "    out_gray = cv2.convertScaleAbs(_gray - alpha * lap)",
                f"    {out} = cv2.cvtColor(out_gray, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "CannyEdge":
        in_img = _line_or_default(input_vars, "image", "image")
        out_mask = output_vars["mask"]
        out_img = output_vars["image"]
        low = int(params.get("low", 100))
        high = max(low + 1, int(params.get("high", 200)))
        aperture = int(str(params.get("aperture", "3")))
        l2 = bool(params.get("l2gradient", False))
        dilate = int(params.get("dilate", 0))
        erode = int(params.get("erode", 0))
        lines.extend(
            [
                f"_canny_gray = ensure_gray({in_img})",
                f"low = {low}",
                f"high = {high}",
                f"aperture = {aperture}",
                f"l2gradient = {l2}",
                f"{out_mask} = cv2.Canny(_canny_gray, low, high, apertureSize=aperture, L2gradient=l2gradient)",
                f"if {dilate} > 0:",
                f"    {out_mask} = cv2.dilate({out_mask}, np.ones((3, 3), dtype=np.uint8), iterations={dilate})",
                f"if {erode} > 0:",
                f"    {out_mask} = cv2.erode({out_mask}, np.ones((3, 3), dtype=np.uint8), iterations={erode})",
                f"{out_img} = cv2.cvtColor({out_mask}, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "SimpleThreshold":
        in_img = _line_or_default(input_vars, "image", "image")
        out_mask = output_vars["mask"]
        out_img = output_vars["image"]
        thresh = int(params.get("thresh", 127))
        max_value = int(params.get("max_value", 255))
        mode_name = str(params.get("type", "binary"))
        pre_blur = int(params.get("pre_blur", 1))
        otsu = bool(params.get("otsu", False))
        mode_code = {
            "binary": "cv2.THRESH_BINARY",
            "binary_inv": "cv2.THRESH_BINARY_INV",
            "trunc": "cv2.THRESH_TRUNC",
            "tozero": "cv2.THRESH_TOZERO",
            "tozero_inv": "cv2.THRESH_TOZERO_INV",
        }.get(mode_name, "cv2.THRESH_BINARY")
        lines.extend(
            [
                f"_th_gray = ensure_gray({in_img})",
                f"thresh = {thresh}",
                f"max_value = {max_value}",
                f"threshold_mode = {mode_code}",
                f"pre_blur = odd_ksize({pre_blur}, 1)",
                "if pre_blur > 1:",
                "    _th_gray = cv2.GaussianBlur(_th_gray, (pre_blur, pre_blur), 0)",
                f"if {otsu}:",
                "    threshold_mode = threshold_mode | cv2.THRESH_OTSU",
                f"_, {out_mask} = cv2.threshold(_th_gray, thresh, max_value, threshold_mode)",
                f"{out_img} = cv2.cvtColor({out_mask}, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "AdaptiveThreshold":
        in_img = _line_or_default(input_vars, "image", "image")
        out_mask = output_vars["mask"]
        out_img = output_vars["image"]
        method = str(params.get("method", "gaussian"))
        typ = str(params.get("type", "binary"))
        block_size = int(params.get("block_size", 11))
        c = int(params.get("c", 2))
        pre_blur = int(params.get("pre_blur", 1))
        method_code = "cv2.ADAPTIVE_THRESH_MEAN_C" if method == "mean" else "cv2.ADAPTIVE_THRESH_GAUSSIAN_C"
        type_code = "cv2.THRESH_BINARY" if typ == "binary" else "cv2.THRESH_BINARY_INV"
        lines.extend(
            [
                f"_ath_gray = ensure_gray({in_img})",
                f"pre_blur = odd_ksize({pre_blur}, 1)",
                "if pre_blur > 1:",
                "    _ath_gray = cv2.GaussianBlur(_ath_gray, (pre_blur, pre_blur), 0)",
                f"block_size = odd_ksize({block_size}, 3)",
                f"c = {c}",
                f"{out_mask} = cv2.adaptiveThreshold(_ath_gray, 255, {method_code}, {type_code}, block_size, c)",
                f"{out_img} = cv2.cvtColor({out_mask}, cv2.COLOR_GRAY2BGR)",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "BinaryMorphology":
        in_mask = _line_or_default(input_vars, "mask", "mask")
        out_mask = output_vars["mask"]
        out_img = output_vars["image"]
        out_meta = output_vars.get("meta", "morph_meta")
        operation = str(params.get("operation", "dilate"))
        shape = str(params.get("kernel_shape", "rect"))
        kw = max(1, int(params.get("kernel_w", 3)))
        kh = max(1, int(params.get("kernel_h", 3)))
        iterations = max(1, int(params.get("iterations", 1)))
        anchor_x = int(params.get("anchor_x", -1))
        anchor_y = int(params.get("anchor_y", -1))
        border_type = str(params.get("border_type", "constant"))
        border_value = int(params.get("border_value", 0))
        ensure_binary = bool(params.get("ensure_binary", True))
        binary_thresh = int(params.get("binary_thresh", 127))
        invert_before = bool(params.get("invert_before", False))
        op_code = {
            "dilate": "cv2.MORPH_DILATE",
            "erode": "cv2.MORPH_ERODE",
            "open": "cv2.MORPH_OPEN",
            "close": "cv2.MORPH_CLOSE",
            "gradient": "cv2.MORPH_GRADIENT",
            "tophat": "cv2.MORPH_TOPHAT",
            "blackhat": "cv2.MORPH_BLACKHAT",
        }.get(operation, "cv2.MORPH_DILATE")
        shape_code = {
            "rect": "cv2.MORPH_RECT",
            "ellipse": "cv2.MORPH_ELLIPSE",
            "cross": "cv2.MORPH_CROSS",
        }.get(shape, "cv2.MORPH_RECT")
        border_code = {
            "default": "cv2.BORDER_DEFAULT",
            "constant": "cv2.BORDER_CONSTANT",
            "reflect": "cv2.BORDER_REFLECT",
            "replicate": "cv2.BORDER_REPLICATE",
            "reflect101": "cv2.BORDER_REFLECT_101",
        }.get(border_type, "cv2.BORDER_CONSTANT")
        lines.extend(
            [
                f"{out_mask} = ensure_gray({in_mask})",
                f"if {ensure_binary}:",
                f"    _, {out_mask} = cv2.threshold({out_mask}, {binary_thresh}, 255, cv2.THRESH_BINARY)",
                f"if {invert_before}:",
                f"    {out_mask} = cv2.bitwise_not({out_mask})",
                f"kernel = cv2.getStructuringElement({shape_code}, ({kw}, {kh}))",
                f"anchor_x = {anchor_x}",
                f"anchor_y = {anchor_y}",
                "if anchor_x >= kernel.shape[1] or anchor_x < -1:",
                "    anchor_x = -1",
                "if anchor_y >= kernel.shape[0] or anchor_y < -1:",
                "    anchor_y = -1",
                "anchor = (anchor_x, anchor_y)",
                f"{out_mask} = cv2.morphologyEx(",
                f"    {out_mask}, {op_code}, kernel, anchor=anchor, iterations={iterations},",
                f"    borderType={border_code}, borderValue={border_value}",
                ")",
                f"{out_img} = cv2.cvtColor({out_mask}, cv2.COLOR_GRAY2BGR)",
                f"{out_meta} = {{",
                f"    'operation': {operation!r},",
                f"    'kernel_shape': {shape!r},",
                f"    'kernel_size': {{'w': {kw}, 'h': {kh}}},",
                f"    'iterations': {iterations},",
                "    'anchor': {'x': anchor_x, 'y': anchor_y},",
                "}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "ContoursAnalysis":
        in_mask = _line_or_default(input_vars, "mask", "mask")
        out_img = output_vars["image"]
        out_mask = output_vars["mask"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        ensure_binary = bool(params.get("ensure_binary", True))
        binary_thresh = int(params.get("binary_thresh", 127))
        invert = bool(params.get("invert", False))
        retrieval_name = str(params.get("retrieval", "tree"))
        approx_name = str(params.get("approx_mode", "simple"))
        offset_x = int(params.get("offset_x", 0))
        offset_y = int(params.get("offset_y", 0))
        draw_mode = str(params.get("draw_mode", "both"))
        thickness = max(1, int(params.get("draw_thickness", 2)))
        filter_by_area = bool(params.get("filter_by_area", True))
        area_min = int(params.get("area_min", 200))
        area_max = max(area_min, int(params.get("area_max", 1_000_000)))
        filter_by_aspect = bool(params.get("filter_by_aspect_ratio", False))
        aspect_min = float(params.get("aspect_ratio_min", 0.1))
        aspect_max = max(aspect_min, float(params.get("aspect_ratio_max", 10.0)))
        retrieval_code = {
            "external": "cv2.RETR_EXTERNAL",
            "list": "cv2.RETR_LIST",
            "ccomp": "cv2.RETR_CCOMP",
            "tree": "cv2.RETR_TREE",
            "floodfill": "cv2.RETR_FLOODFILL",
        }.get(retrieval_name, "cv2.RETR_TREE")
        approx_code = {
            "none": "cv2.CHAIN_APPROX_NONE",
            "simple": "cv2.CHAIN_APPROX_SIMPLE",
            "tc89_l1": "cv2.CHAIN_APPROX_TC89_L1",
            "tc89_kcos": "cv2.CHAIN_APPROX_TC89_KCOS",
        }.get(approx_name, "cv2.CHAIN_APPROX_SIMPLE")
        lines.extend(
            [
                f"{out_mask} = ensure_gray({in_mask})",
                f"if {ensure_binary}:",
                f"    _, {out_mask} = cv2.threshold({out_mask}, {binary_thresh}, 255, cv2.THRESH_BINARY)",
                f"if {invert}:",
                f"    {out_mask} = cv2.bitwise_not({out_mask})",
                f"_find_input = {out_mask}.astype(np.int32) if {retrieval_code} == cv2.RETR_FLOODFILL else {out_mask}.copy()",
                f"_found = cv2.findContours(_find_input, {retrieval_code}, {approx_code}, offset=({offset_x}, {offset_y}))",
                "if len(_found) == 3:",
                "    _, contours, hierarchy = _found",
                "else:",
                "    contours, hierarchy = _found",
                f"{out_img} = cv2.cvtColor({out_mask}, cv2.COLOR_GRAY2BGR)",
                f"{out_det} = []",
                "kept = 0",
                "total_area = 0.0",
                "rejected_area = 0",
                "rejected_aspect = 0",
                "for cnt in contours:",
                "    area = float(cv2.contourArea(cnt))",
                "    x, y, w, h = cv2.boundingRect(cnt)",
                "    aspect_ratio = float(w) / float(h) if h > 0 else 9999.0",
                "    perimeter = float(cv2.arcLength(cnt, True))",
                f"    if {filter_by_area} and (area < {area_min} or area > {area_max}):",
                "        rejected_area += 1",
                "        continue",
                f"    if {filter_by_aspect} and (aspect_ratio < {aspect_min} or aspect_ratio > {aspect_max}):",
                "        rejected_aspect += 1",
                "        continue",
                "    kept += 1",
                "    total_area += area",
                f"    {out_det}.append({{'bbox': (int(x), int(y), int(w), int(h)), 'label': 'contour', 'score': 1.0, "
                "'extra': {'area': area, 'aspect_ratio': aspect_ratio, 'perimeter': perimeter}})",
                f"    if {draw_mode!r} in ('contours', 'both'):",
                f"        cv2.drawContours({out_img}, [cnt], -1, (0, 255, 0), {thickness})",
                f"    if {draw_mode!r} in ('boxes', 'both'):",
                f"        cv2.rectangle({out_img}, (x, y), (x + w, y + h), (0, 165, 255), {thickness})",
                f"{out_meta} = {{",
                "    'total_contours': len(contours),",
                "    'kept_contours': kept,",
                "    'rejected_by_area': rejected_area,",
                "    'rejected_by_aspect_ratio': rejected_aspect,",
                "    'total_kept_area': total_area,",
                "    'has_hierarchy': hierarchy is not None,",
                f"    'retrieval': {retrieval_name!r},",
                f"    'approx_mode': {approx_name!r},",
                f"    'offset': {{'x': {offset_x}, 'y': {offset_y}}},",
                "}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "HoughCircles":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        dp = max(1.0, float(params.get("dp", 1.2)))
        min_dist = max(1, int(params.get("min_dist", 70)))
        param1 = max(1, int(params.get("param1", 120)))
        param2 = max(1, int(params.get("param2", 35)))
        min_radius = max(0, int(params.get("min_radius", 10)))
        max_radius = max(1, int(params.get("max_radius", 120)))
        blur_k = int(params.get("blur_k", 5))
        lines.extend(
            [
                f"_hc_src = ensure_bgr({in_img})",
                "_hc_gray = cv2.cvtColor(_hc_src, cv2.COLOR_BGR2GRAY)",
                f"blur_k = odd_ksize({blur_k}, 1)",
                "if blur_k > 1:",
                "    _hc_gray = cv2.medianBlur(_hc_gray, blur_k)",
                f"_circles = cv2.HoughCircles(_hc_gray, cv2.HOUGH_GRADIENT, dp={dp}, minDist={min_dist}, "
                f"param1={param1}, param2={param2}, minRadius={min_radius}, maxRadius={max_radius})",
                f"{out_img} = _hc_src.copy()",
                f"{out_det} = []",
                "if _circles is not None:",
                "    _circles = np.uint16(np.around(_circles[0]))",
                "    for c in _circles:",
                "        x, y, r = int(c[0]), int(c[1]), int(c[2])",
                f"        cv2.circle({out_img}, (x, y), r, (0, 255, 0), 2)",
                f"        cv2.circle({out_img}, (x, y), 2, (0, 0, 255), 3)",
                f"        {out_det}.append({{'bbox': (x - r, y - r, 2 * r, 2 * r), 'label': 'circle', 'score': 1.0, 'extra': {{'radius': r}}}})",
                f"{out_meta} = {{'circle_count': len({out_det})}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "HaarMultiDetect":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        frontal = bool(params.get("frontal", True))
        profile = bool(params.get("profile", False))
        eyes = bool(params.get("eyes", True))
        smile = bool(params.get("smile", False))
        scale = max(1.01, float(params.get("scale_factor", 1.1)))
        min_neighbors = max(1, int(params.get("min_neighbors", 5)))
        min_size = max(10, int(params.get("min_size", 30)))
        equalize_hist = bool(params.get("equalize_hist", True))
        lines.extend(
            [
                "_haar_files = {",
                "    'frontal': 'haarcascade_frontalface_default.xml',",
                "    'profile': 'haarcascade_profileface.xml',",
                "    'eye': 'haarcascade_eye.xml',",
                "    'smile': 'haarcascade_smile.xml',",
                "}",
                "_cascades = {}",
                "for _k, _fname in _haar_files.items():",
                "    _cc = cv2.CascadeClassifier(cv2.data.haarcascades + _fname)",
                "    if not _cc.empty():",
                "        _cascades[_k] = _cc",
                "if not _cascades:",
                "    raise RuntimeError('No Haar cascades available in cv2.data.haarcascades')",
                f"_haar_src = ensure_bgr({in_img})",
                "_haar_gray = cv2.cvtColor(_haar_src, cv2.COLOR_BGR2GRAY)",
                f"if {equalize_hist}:",
                "    _haar_gray = cv2.equalizeHist(_haar_gray)",
                f"{out_img} = _haar_src.copy()",
                f"{out_det} = []",
                "_face_regions = []",
                f"if {frontal} and 'frontal' in _cascades:",
                f"    _faces = _cascades['frontal'].detectMultiScale(_haar_gray, scaleFactor={scale}, minNeighbors={min_neighbors}, minSize=({min_size}, {min_size}))",
                "    for (x, y, w, h) in _faces:",
                f"        {out_det}.append({{'bbox': (int(x), int(y), int(w), int(h)), 'label': 'frontal_face', 'score': 1.0}})",
                "        _face_regions.append((int(x), int(y), int(w), int(h)))",
                f"        cv2.rectangle({out_img}, (x, y), (x + w, y + h), (0, 255, 0), 2)",
                f"if {profile} and 'profile' in _cascades:",
                f"    _profiles = _cascades['profile'].detectMultiScale(_haar_gray, scaleFactor={scale}, minNeighbors={min_neighbors}, minSize=({min_size}, {min_size}))",
                "    for (x, y, w, h) in _profiles:",
                f"        {out_det}.append({{'bbox': (int(x), int(y), int(w), int(h)), 'label': 'profile_face', 'score': 1.0}})",
                "        _face_regions.append((int(x), int(y), int(w), int(h)))",
                f"        cv2.rectangle({out_img}, (x, y), (x + w, y + h), (255, 180, 0), 2)",
                f"if {eyes} and 'eye' in _cascades:",
                "    for (x, y, w, h) in _face_regions:",
                "        roi = _haar_gray[y:y+h, x:x+w]",
                f"        _eyes = _cascades['eye'].detectMultiScale(roi, scaleFactor=1.1, minNeighbors={max(2, min_neighbors // 2)})",
                "        for (ex, ey, ew, eh) in _eyes:",
                "            bx, by, bw, bh = int(x + ex), int(y + ey), int(ew), int(eh)",
                f"            {out_det}.append({{'bbox': (bx, by, bw, bh), 'label': 'eye', 'score': 1.0}})",
                f"            cv2.rectangle({out_img}, (bx, by), (bx + bw, by + bh), (255, 0, 0), 1)",
                f"if {smile} and 'smile' in _cascades:",
                "    for (x, y, w, h) in _face_regions:",
                "        roi = _haar_gray[y:y+h, x:x+w]",
                f"        _smiles = _cascades['smile'].detectMultiScale(roi, scaleFactor=1.7, minNeighbors={max(3, min_neighbors)})",
                "        for (sx, sy, sw, sh) in _smiles:",
                "            bx, by, bw, bh = int(x + sx), int(y + sy), int(sw), int(sh)",
                f"            {out_det}.append({{'bbox': (bx, by, bw, bh), 'label': 'smile', 'score': 1.0}})",
                f"            cv2.rectangle({out_img}, (bx, by), (bx + bw, by + bh), (0, 0, 255), 1)",
                f"{out_meta} = {{",
                f"    'total_detections': len({out_det}),",
                "    'concept': 'Haar-like features + AdaBoost + stage cascade + sliding windows',",
                "}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "CascadeDetectCustom":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        cascade_path = str(params.get("cascade_path", "")).strip()
        use_samples_findfile = bool(params.get("use_samples_findfile", False))
        equalize_hist = bool(params.get("equalize_hist", True))
        scale_factor = max(1.0001, float(params.get("scale_factor", 1.1)))
        min_neighbors = max(0, int(params.get("min_neighbors", 5)))
        flags = max(0, int(params.get("flags", 0)))
        min_w = max(0, int(params.get("min_size_w", 30)))
        min_h = max(0, int(params.get("min_size_h", 30)))
        max_w = max(0, int(params.get("max_size_w", 0)))
        max_h = max(0, int(params.get("max_size_h", 0)))
        label = str(params.get("label", "cascade_obj")).strip() or "cascade_obj"
        draw_mode = str(params.get("draw_mode", "rectangle"))
        thickness = max(1, int(params.get("draw_thickness", 2)))
        lines.extend(
            [
                f"{out_img} = ensure_bgr({in_img}).copy()",
                f"cascade_path = {cascade_path!r}",
                f"if {use_samples_findfile}:",
                "    try:",
                "        cascade_path = cv2.samples.findFile(cascade_path)",
                "    except Exception:",
                "        pass",
                "cascade_path = str(Path(cascade_path).expanduser())",
                "_cascade = cv2.CascadeClassifier(cascade_path)",
                "if _cascade.empty():",
                "    raise RuntimeError(f'Failed to load cascade XML: {cascade_path}')",
                "_gray = cv2.cvtColor(ensure_bgr(" + in_img + "), cv2.COLOR_BGR2GRAY)",
                f"if {equalize_hist}:",
                "    _gray = cv2.equalizeHist(_gray)",
                f"_rects = _cascade.detectMultiScale(_gray, scaleFactor={scale_factor}, minNeighbors={min_neighbors}, "
                f"flags={flags}, minSize=({min_w}, {min_h}), maxSize=({max_w}, {max_h}))",
                f"{out_det} = []",
                "for (x, y, w, h) in _rects:",
                "    x, y, w, h = int(x), int(y), int(w), int(h)",
                f"    {out_det}.append({{'bbox': (x, y, w, h), 'label': {label!r}, 'score': 1.0}})",
                f"    if {draw_mode!r} == 'ellipse':",
                f"        cv2.ellipse({out_img}, (x + w // 2, y + h // 2), (w // 2, h // 2), 0, 0, 360, (255, 0, 255), {thickness})",
                f"    elif {draw_mode!r} == 'circle':",
                f"        cv2.circle({out_img}, (x + w // 2, y + h // 2), int(round((w + h) * 0.25)), (255, 0, 0), {thickness})",
                f"    elif {draw_mode!r} == 'rectangle':",
                f"        cv2.rectangle({out_img}, (x, y), (x + w, y + h), (0, 255, 0), {thickness})",
                f"{out_meta} = {{'detection_count': len({out_det}), 'cascade_path': cascade_path}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "HOGDescriptor64x128":
        in_img = _line_or_default(input_vars, "image", "image")
        out_vec = output_vars["feature_vector"]
        out_img = output_vars["image"]
        out_meta = output_vars["meta"]
        roi_scale = float(params.get("roi_scale", 0.6))
        center_x = float(params.get("center_x", 0.5))
        center_y = float(params.get("center_y", 0.5))
        show_gradient = bool(params.get("show_gradient", True))
        lines.extend(
            [
                f"_hog_src = ensure_bgr({in_img})",
                "_hog_gray = cv2.cvtColor(_hog_src, cv2.COLOR_BGR2GRAY)",
                "_h, _w = _hog_gray.shape[:2]",
                f"roi_scale = {roi_scale}",
                f"center_x = {center_x}",
                f"center_y = {center_y}",
                "roi_h = max(32, int(min(_h, 2 * _w) * roi_scale))",
                "roi_w = max(16, roi_h // 2)",
                "cx = int(center_x * (_w - 1))",
                "cy = int(center_y * (_h - 1))",
                "x1 = max(0, min(_w - roi_w, cx - roi_w // 2))",
                "y1 = max(0, min(_h - roi_h, cy - roi_h // 2))",
                "x2, y2 = x1 + roi_w, y1 + roi_h",
                "_roi = _hog_gray[y1:y2, x1:x2]",
                "_roi_64x128 = cv2.resize(_roi, (64, 128), interpolation=cv2.INTER_LINEAR)",
                "_hog = cv2.HOGDescriptor()",
                f"{out_vec} = _hog.compute(_roi_64x128).reshape(-1)",
                "_left = _hog_src.copy()",
                "cv2.rectangle(_left, (x1, y1), (x2, y2), (0, 255, 0), 2)",
                f"if {show_gradient}:",
                "    gx = cv2.Sobel(_roi_64x128, cv2.CV_32F, 1, 0, ksize=1)",
                "    gy = cv2.Sobel(_roi_64x128, cv2.CV_32F, 0, 1, ksize=1)",
                "    mag = cv2.magnitude(gx, gy)",
                "    mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)",
                "    _right = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)",
                "else:",
                "    _right = cv2.cvtColor(_roi_64x128, cv2.COLOR_GRAY2BGR)",
                "_right = cv2.resize(_right, (_left.shape[1], _left.shape[0]), interpolation=cv2.INTER_NEAREST)",
                f"{out_img} = cv2.hconcat([_left, _right])",
                f"{out_meta} = {{",
                f"    'vector_length': int(len({out_vec})),",
                "    'expected_default_len': 3780,",
                "    'concept': '8x8 cells, 9 bins, 16x16 block normalization (L2-Hys)',",
                "}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "HOGDescriptorConfigurable":
        in_img = _line_or_default(input_vars, "image", "image")
        out_vec = output_vars["feature_vector"]
        out_img = output_vars["image"]
        out_meta = output_vars["meta"]
        win_w = max(8, int(params.get("win_w", 64)))
        win_h = max(8, int(params.get("win_h", 128)))
        block_w = max(2, int(params.get("block_w", 16)))
        block_h = max(2, int(params.get("block_h", 16)))
        stride_x = max(1, int(params.get("block_stride_x", 8)))
        stride_y = max(1, int(params.get("block_stride_y", 8)))
        cell_w = max(1, int(params.get("cell_w", 8)))
        cell_h = max(1, int(params.get("cell_h", 8)))
        nbins = max(2, int(params.get("nbins", 9)))
        deriv_aperture = int(params.get("deriv_aperture", 1))
        win_sigma = float(params.get("win_sigma", -1.0))
        l2_hys = float(params.get("l2_hys_threshold", 0.2))
        gamma = bool(params.get("gamma_correction", False))
        nlevels = max(1, int(params.get("nlevels", 64)))
        signed_gradient = bool(params.get("signed_gradient", False))
        region_mode = str(params.get("region_mode", "center_crop_resize"))
        roi_scale = float(params.get("roi_scale", 0.6))
        center_x = float(params.get("center_x", 0.5))
        center_y = float(params.get("center_y", 0.5))
        show_gradient = bool(params.get("show_gradient", True))
        lines.extend(
            [
                f"_hogc_src = ensure_bgr({in_img})",
                "_hogc_gray = cv2.cvtColor(_hogc_src, cv2.COLOR_BGR2GRAY)",
                "_h, _w = _hogc_gray.shape[:2]",
                f"win_size = ({win_w}, {win_h})",
                f"block_size = ({block_w}, {block_h})",
                f"block_stride = ({stride_x}, {stride_y})",
                f"cell_size = ({cell_w}, {cell_h})",
                "if block_size[0] > win_size[0] or block_size[1] > win_size[1]:",
                "    raise ValueError('blockSize must be <= winSize')",
                "if block_size[0] % cell_size[0] != 0 or block_size[1] % cell_size[1] != 0:",
                "    raise ValueError('blockSize must be divisible by cellSize')",
                "if (win_size[0] - block_size[0]) % block_stride[0] != 0 or (win_size[1] - block_size[1]) % block_stride[1] != 0:",
                "    raise ValueError('(winSize - blockSize) must be divisible by blockStride')",
                f"_hog = cv2.HOGDescriptor(_winSize=win_size, _blockSize=block_size, _blockStride=block_stride, "
                f"_cellSize=cell_size, _nbins={nbins}, _derivAperture={deriv_aperture}, _winSigma={win_sigma}, "
                f"_histogramNormType=cv2.HOGDescriptor_L2Hys, _L2HysThreshold={l2_hys}, _gammaCorrection={gamma}, _nlevels={nlevels}, _signedGradient={signed_gradient})",
                f"if {region_mode!r} == 'full_resize':",
                "    x1, y1, x2, y2 = 0, 0, _w, _h",
                "    _roi = _hogc_gray",
                "else:",
                f"    roi_h = max(8, int(min(_h, 2 * _w) * {roi_scale}))",
                f"    roi_w = max(8, int(max(1, roi_h * {win_w} / max(1, {win_h}))))",
                "    roi_w = min(roi_w, _w)",
                "    roi_h = min(roi_h, _h)",
                f"    cx = int({center_x} * (_w - 1))",
                f"    cy = int({center_y} * (_h - 1))",
                "    x1 = max(0, min(_w - roi_w, cx - roi_w // 2))",
                "    y1 = max(0, min(_h - roi_h, cy - roi_h // 2))",
                "    x2, y2 = x1 + roi_w, y1 + roi_h",
                "    _roi = _hogc_gray[y1:y2, x1:x2]",
                "_roi_norm = cv2.resize(_roi, win_size, interpolation=cv2.INTER_LINEAR)",
                f"{out_vec} = _hog.compute(_roi_norm).reshape(-1)",
                "_left = _hogc_src.copy()",
                "cv2.rectangle(_left, (x1, y1), (x2, y2), (0, 255, 0), 2)",
                f"if {show_gradient}:",
                "    gx = cv2.Sobel(_roi_norm, cv2.CV_32F, 1, 0, ksize=1)",
                "    gy = cv2.Sobel(_roi_norm, cv2.CV_32F, 0, 1, ksize=1)",
                "    mag = cv2.magnitude(gx, gy)",
                "    mag_u8 = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)",
                "    _right = cv2.applyColorMap(mag_u8, cv2.COLORMAP_TURBO)",
                "else:",
                "    _right = cv2.cvtColor(_roi_norm, cv2.COLOR_GRAY2BGR)",
                "_right = cv2.resize(_right, (_left.shape[1], _left.shape[0]), interpolation=cv2.INTER_NEAREST)",
                f"{out_img} = cv2.hconcat([_left, _right])",
                f"{out_meta} = {{'vector_length': int(len({out_vec})), 'win_size': {{'w': {win_w}, 'h': {win_h}}}, 'nbins': {nbins}}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "HOGSVMDetectPeople":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        hit_threshold = float(params.get("hit_threshold", 0.0))
        stride = max(4, int(params.get("stride", 8)))
        padding = max(0, int(params.get("padding", 8)))
        scale = max(1.01, float(params.get("scale", 1.05)))
        final_threshold = int(params.get("final_threshold", 2))
        weight_threshold = float(params.get("weight_threshold", 0.5))
        lines.extend(
            [
                f"_hogsvm_src = ensure_bgr({in_img})",
                "_hog_detector = cv2.HOGDescriptor()",
                "_hog_detector.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())",
                f"_rects, _weights = _hog_detector.detectMultiScale(_hogsvm_src, {hit_threshold}, ({stride}, {stride}), ({padding}, {padding}), {scale}, {final_threshold})",
                f"{out_img} = _hogsvm_src.copy()",
                f"{out_det} = []",
                "for (x, y, w, h), score in zip(_rects, _weights):",
                "    score = float(score)",
                f"    if score < {weight_threshold}:",
                "        continue",
                f"    {out_det}.append({{'bbox': (int(x), int(y), int(w), int(h)), 'label': 'person', 'score': score}})",
                "    color = (0, 255, 0) if score >= 1.0 else (0, 165, 255)",
                f"    cv2.rectangle({out_img}, (int(x), int(y)), (int(x + w), int(y + h)), color, 2)",
                f"    cv2.putText({out_img}, f'{{score:.2f}}', (int(x), max(12, int(y - 5))), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)",
                f"{out_meta} = {{'raw_rects': int(len(_rects)), 'kept_rects': int(len({out_det})), "
                "'concept': 'HOG feature descriptor + linear SVM over sliding windows'}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "HOGDetectMultiScaleAdvanced":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        hit = float(params.get("hit_threshold", 0.0))
        wsx = max(1, int(params.get("win_stride_x", 8)))
        wsy = max(1, int(params.get("win_stride_y", 8)))
        px = max(0, int(params.get("padding_x", 8)))
        py = max(0, int(params.get("padding_y", 8)))
        scale = max(1.001, float(params.get("scale", 1.05)))
        final_threshold = float(params.get("final_threshold", 2.0))
        use_meanshift = bool(params.get("use_meanshift_grouping", False))
        conf_th = float(params.get("confidence_threshold", 0.0))
        max_det = max(0, int(params.get("max_detections", 0)))
        draw_score = bool(params.get("draw_score", True))
        lines.extend(
            [
                f"_hogadv_src = ensure_bgr({in_img})",
                "_hogadv = cv2.HOGDescriptor()",
                "_hogadv.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())",
                "try:",
                f"    _rects, _weights = _hogadv.detectMultiScale(_hogadv_src, {hit}, ({wsx}, {wsy}), ({px}, {py}), {scale}, {final_threshold}, {use_meanshift})",
                "except Exception:",
                f"    _rects, _weights = _hogadv.detectMultiScale(_hogadv_src, {hit}, ({wsx}, {wsy}), ({px}, {py}), {scale}, {final_threshold})",
                f"{out_img} = _hogadv_src.copy()",
                f"{out_det} = []",
                "for (x, y, w, h), score in zip(_rects, _weights):",
                "    score = float(score)",
                f"    if score < {conf_th}:",
                "        continue",
                "    x, y, w, h = int(x), int(y), int(w), int(h)",
                f"    {out_det}.append({{'bbox': (x, y, w, h), 'label': 'person', 'score': score}})",
                f"    if {max_det} > 0 and len({out_det}) > {max_det}:",
                "        break",
                "    color = (0, 255, 0) if score >= 0.7 else (255, 0, 0) if score >= 0.3 else (0, 0, 255)",
                f"    cv2.rectangle({out_img}, (x, y), (x + w, y + h), color, 2)",
                f"    if {draw_score}:",
                f"        cv2.putText({out_img}, f'{{score:.2f}}', (x, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)",
                f"{out_meta} = {{'raw_rects': int(len(_rects)), 'kept_rects': int(len({out_det}))}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "DetectionStyleDraw":
        in_img = _line_or_default(input_vars, "image", "image")
        in_det = _line_or_default(input_vars, "detections", "detections")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        shape = str(params.get("shape", "rectangle"))
        line_type_code = {"8": "cv2.LINE_8", "4": "cv2.LINE_4", "aa": "cv2.LINE_AA"}.get(str(params.get("line_type", "8")), "cv2.LINE_8")
        thickness = max(1, int(params.get("thickness", 2)))
        show_label = bool(params.get("show_label", True))
        show_score = bool(params.get("show_score", True))
        font_scale = float(params.get("font_scale", 0.45))
        filter_by_score = bool(params.get("filter_by_score", False))
        min_score = float(params.get("min_score", -10.0))
        max_score = float(params.get("max_score", 10.0))
        if max_score < min_score:
            max_score = min_score
        score_low = float(params.get("score_low", 0.13))
        score_mid = max(score_low, float(params.get("score_mid", 0.3)))
        low_color = (int(params.get("low_b", 0)), int(params.get("low_g", 0)), int(params.get("low_r", 255)))
        mid_color = (int(params.get("mid_b", 255)), int(params.get("mid_g", 0)), int(params.get("mid_r", 0)))
        high_color = (int(params.get("high_b", 0)), int(params.get("high_g", 255)), int(params.get("high_r", 0)))
        label_filter = str(params.get("label_filter", "")).strip().lower()
        lines.extend(
            [
                f"{out_img} = ensure_bgr({in_img}).copy()",
                f"{out_det} = []",
                "drawn_count = 0",
                f"for _det in ({in_det} or []):",
                "    if isinstance(_det, dict):",
                "        x, y, w, h = _det.get('bbox', (0, 0, 0, 0))",
                "        label = str(_det.get('label', 'obj'))",
                "        score = float(_det.get('score', 1.0))",
                "        extra = dict(_det.get('extra', {}))",
                "    else:",
                "        x, y, w, h = getattr(_det, 'bbox', (0, 0, 0, 0))",
                "        label = str(getattr(_det, 'label', 'obj'))",
                "        score = float(getattr(_det, 'score', 1.0))",
                "        extra = dict(getattr(_det, 'extra', {}))",
                "    x, y, w, h = int(x), int(y), int(w), int(h)",
                f"    if {label_filter!r} and {label_filter!r} not in label.lower():",
                "        continue",
                f"    if {filter_by_score} and not ({min_score} <= score <= {max_score}):",
                "        continue",
                f"    color = {high_color} if score >= {score_mid} else {mid_color} if score >= {score_low} else {low_color}",
                f"    if {shape!r} == 'ellipse':",
                f"        cv2.ellipse({out_img}, (x + w // 2, y + h // 2), (w // 2, h // 2), 0, 0, 360, color, {thickness}, {line_type_code})",
                f"    elif {shape!r} == 'circle':",
                f"        cv2.circle({out_img}, (x + w // 2, y + h // 2), int(round((w + h) * 0.25)), color, {thickness}, {line_type_code})",
                "    else:",
                f"        cv2.rectangle({out_img}, (x, y), (x + w, y + h), color, {thickness}, {line_type_code})",
                "    text = ''",
                f"    if {show_label}:",
                "        text += label",
                f"    if {show_score}:",
                "        text += (' ' if text else '') + f'{score:.2f}'",
                "    if text:",
                f"        cv2.putText({out_img}, text, (x, max(12, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, {font_scale}, color, 1, {line_type_code})",
                f"    {out_det}.append({{'bbox': (x, y, w, h), 'label': label, 'score': score, 'extra': extra}})",
                "    drawn_count += 1",
                f"{out_meta} = {{'drawn_count': drawn_count, 'shape': {shape!r}, 'filter_by_score': {filter_by_score}, 'min_score': {min_score}, 'max_score': {max_score}}}",
            ]
        )
        return "\n".join(lines)

    if node.block_type == "DlibHOGFaceDetect":
        in_img = _line_or_default(input_vars, "image", "image")
        out_img = output_vars["image"]
        out_det = output_vars["detections"]
        out_meta = output_vars["meta"]
        upsample = max(0, int(params.get("upsample_num_times", 1)))
        adjust_th = float(params.get("adjust_threshold", 0.0))
        thickness = max(1, int(params.get("draw_thickness", 2)))
        lines.extend(
            [
                "try:",
                "    import dlib",
                "except Exception as exc:",
                "    raise RuntimeError('dlib is not installed. Install dlib to use DlibHOGFaceDetect.') from exc",
                f"{out_img} = ensure_bgr({in_img}).copy()",
                "_dlib_rgb = cv2.cvtColor(" + out_img + ", cv2.COLOR_BGR2RGB)",
                "_dlib_detector = dlib.get_frontal_face_detector()",
                f"_rects, _scores, _ = _dlib_detector.run(_dlib_rgb, {upsample}, {adjust_th})",
                f"{out_det} = []",
                "for _rect, _score in zip(_rects, _scores):",
                "    x1, y1, x2, y2 = int(_rect.left()), int(_rect.top()), int(_rect.right()), int(_rect.bottom())",
                "    w = max(0, x2 - x1)",
                "    h = max(0, y2 - y1)",
                f"    {out_det}.append({{'bbox': (x1, y1, w, h), 'label': 'face', 'score': float(_score)}})",
                f"    cv2.rectangle({out_img}, (x1, y1), (x2, y2), (0, 255, 255), {thickness})",
                f"    cv2.putText({out_img}, f'{{float(_score):.2f}}', (x1, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)",
                f"{out_meta} = {{'face_count': int(len({out_det})), 'backend': 'dlib_hog'}}",
            ]
        )
        return "\n".join(lines)

    # Fallback for unknown/custom blocks.
    lines.extend(
        [
            f"# Unsupported block type for standalone export: {node.block_type}",
            "# Generated snippet (may require manual edits):",
            *[f"# {line}" for line in spec.description.splitlines() if line.strip()],
        ]
    )
    return "\n".join(lines)


def _build_helpers_cell() -> str:
    return "\n".join(
        [
            "import json",
            "import cv2",
            "import numpy as np",
            "import matplotlib.pyplot as plt",
            "from pathlib import Path",
            "",
            "def ensure_gray(image):",
            "    if image is None:",
            "        raise ValueError('Expected image input')",
            "    if image.ndim == 2:",
            "        return image",
            "    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)",
            "",
            "def ensure_bgr(image):",
            "    if image is None:",
            "        raise ValueError('Expected image input')",
            "    if image.ndim == 2:",
            "        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)",
            "    if image.shape[2] == 4:",
            "        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)",
            "    return image",
            "",
            "def odd_ksize(value, minimum=1):",
            "    k = int(value)",
            "    k = max(int(minimum), k)",
            "    if k % 2 == 0:",
            "        k += 1",
            "    return k",
            "",
            "def gamma_correct(image, gamma):",
            "    gamma = max(0.01, float(gamma))",
            "    table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)",
            "    return cv2.LUT(image, table)",
            "",
            "def show(image, title='Preview', figsize=(10, 6), cmap=None):",
            "    plt.figure(figsize=figsize)",
            "    if image.ndim == 2:",
            "        plt.imshow(image, cmap=cmap or 'gray')",
            "    else:",
            "        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))",
            "    plt.title(title)",
            "    plt.axis('off')",
            "    plt.show()",
        ]
    )


def _preview_lines(node: NodeModel, spec: BlockSpec, output_vars: dict[str, str]) -> list[str]:
    lines: list[str] = []
    output_port_names = {p.name for p in spec.output_ports}
    image_var = output_vars.get("image")
    mask_var = output_vars.get("mask")

    if node.block_type == "ContourCount" and image_var:
        meta_var = output_vars.get("meta")
        if meta_var:
            safe_title = (node.title or spec.title).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f"show({image_var}, title=f\"{safe_title} (count={{{meta_var}.get('contour_count', 0)}})\")")
            return lines
    if node.block_type == "PSNRCompare" and image_var:
        meta_var = output_vars.get("meta")
        if meta_var:
            safe_title = (node.title or spec.title).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f"show({image_var}, title=f\"{safe_title} (PSNR={{{meta_var}.get('psnr', 0):.2f}} dB)\")")
            return lines

    if "image" in output_port_names and image_var:
        lines.append(f"show({image_var}, title={f'{node.title or spec.title} - image'!r})")
    if "mask" in output_port_names and mask_var:
        if image_var and mask_var == image_var:
            return lines
        lines.append(f"show({mask_var}, title={f'{node.title or spec.title} - mask'!r}, cmap='gray')")

    for port in spec.output_ports:
        if port.type != "image":
            continue
        if port.name == "image":
            continue
        var = output_vars.get(port.name)
        if not var:
            continue
        lines.append(f"show({var}, title={f'{node.title or spec.title} - {port.name}'!r})")
    return lines


def _choose_final_preview(order: list[str], pipeline: PipelineModel, var_map: dict[tuple[str, str], str], registry: BlockRegistry) -> tuple[str | None, str]:
    selected = set(order)
    node_by_id = {n.id: n for n in pipeline.nodes}
    has_outbound: dict[str, bool] = {nid: False for nid in order}
    for edge in pipeline.edges:
        if edge.src_node in selected and edge.dst_node in selected:
            has_outbound[edge.src_node] = True

    candidate_nodes = [nid for nid in order if not has_outbound.get(nid, False)]
    if not candidate_nodes:
        candidate_nodes = list(order)

    for nid in reversed(candidate_nodes):
        spec = registry.get_spec(node_by_id[nid].block_type)
        for port in ("image", "mask"):
            if any(p.name == port for p in spec.output_ports):
                var = var_map.get((nid, port))
                if var:
                    return var, port
    return None, "image"


def export_notebook(pipeline: PipelineModel, registry: BlockRegistry) -> nbformat.NotebookNode:
    node_by_id = {n.id: n for n in pipeline.nodes}
    try:
        topo = topological_sort(pipeline)
    except Exception:  # noqa: BLE001
        topo = [n.id for n in pipeline.nodes]

    concept_nodes = []
    for nid in topo:
        node = node_by_id.get(nid)
        if node is None or not node.enabled:
            continue
        if registry.get_spec(node.block_type).is_concept:
            concept_nodes.append(node)

    notes = [n for n in pipeline.notes if (n.title.strip() or n.markdown.strip())]
    order, inbound_edges, skipped = _exportable_order(pipeline, registry)
    var_map = _build_var_map(order, node_by_id, registry)

    cells: list[nbformat.NotebookNode] = [new_markdown_cell("# Image Processing Pipeline Notebook")]
    if concept_nodes:
        for concept in concept_nodes:
            md = str(concept.params.get("markdown", "")).strip()
            body = f"## {concept.title}\n\n{md}" if md else f"## {concept.title}"
            cells.append(new_markdown_cell(body))

    if notes:
        note_lines = ["## Canvas Notes"]
        for note in notes:
            title = note.title.strip() or "Note"
            text = note.markdown.strip()
            note_lines.append(f"### {title}")
            if text:
                note_lines.append(text)
        cells.append(new_markdown_cell("\n\n".join(note_lines)))

    cells.append(new_code_cell(_build_helpers_cell()))

    for nid in order:
        node = node_by_id[nid]
        spec = registry.get_spec(node.block_type)
        params = _merged_params(spec, node)
        input_vars: dict[str, str] = {}
        for port in spec.input_ports:
            edge = inbound_edges.get(nid, {}).get(port.name)
            if edge is None:
                continue
            src_var = var_map.get((edge.src_node, edge.src_port))
            if src_var:
                input_vars[port.name] = src_var
        output_vars = {p.name: var_map[(nid, p.name)] for p in spec.output_ports if (nid, p.name) in var_map}
        block_code = _render_block_code(node, spec, params, input_vars, output_vars)
        previews = _preview_lines(node, spec, output_vars)
        if previews:
            block_code = f"{block_code}\n\n" + "\n".join(previews)
        cells.append(new_code_cell(block_code))

    final_var, final_kind = _choose_final_preview(order, pipeline, var_map, registry)
    if final_var is not None:
        if final_kind == "mask":
            preview_code = (
                f"final_image = cv2.cvtColor({final_var}, cv2.COLOR_GRAY2BGR)\n"
                "show(final_image, title='Final Output')"
            )
        else:
            preview_code = f"show({final_var}, title='Final Output')"
        cells.append(new_code_cell(preview_code))

    if skipped:
        skipped_md = "## Skipped Nodes\nThese nodes were excluded because required inputs were not connected:\n\n"
        skipped_md += "\n".join(f"- {name}" for name in sorted(set(skipped)))
        cells.append(new_markdown_cell(skipped_md))

    return new_notebook(cells=cells)


def write_notebook_export(path: str | Path, pipeline: PipelineModel, registry: BlockRegistry) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    nb = export_notebook(pipeline, registry)
    nbformat.write(nb, str(p))
