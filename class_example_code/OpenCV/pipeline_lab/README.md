# CV Pipeline Lab

Visual blocks pipeline GUI for CME 466.

## Features
- Drag/drop block palette to canvas
- Build DAG pipelines with branch/merge
- Manual run with topological execution
- Optional `Auto Run` mode (`Ctrl+Shift+R`) with incremental recompute (changed node + downstream)
- `Preview Fullscreen` mode (`F11`) uses a resizable side-by-side layout: large preview + narrow properties panel
- Simple adjustment blocks: `Contrast Adjustment`, `Log Transform`, `Gamma Transform`
- Interactive `Image Crop` block with draggable/resizable crop rectangle in preview
- Navigation helpers: toolbar `Recenter` and `Reset View` (`Ctrl+0`) to recover camera/zoom
- Method-aware parameter UI (for example, `Denoise / Blur` shows different controls for box/gaussian/median/bilateral)
- Binary-mask aware blocks: `Binary Morphology` (`dilate/erode/open/close/gradient/tophat/blackhat`) with kernel controls
- Contours block consumes `mask` input, exposes retrieval/approx modes, and supports area/aspect-ratio filtering
- Node preview, parameter editing, snippets, logs
- Export pipeline to JSON, Python, and Jupyter notebook

## Run

```bash
cd /Users/oren/code/cme466/class_example_code/OpenCV/pipeline_lab
uv sync
uv run cv-pipeline-lab
```

Optional:

```bash
uv run cv-pipeline-lab --image /path/to/image.jpg
uv run cv-pipeline-lab --pipeline /path/to/pipeline.json
```

## Tests

```bash
uv run pytest
```
