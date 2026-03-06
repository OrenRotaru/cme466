# CME 466 Exam Prep Pack

## What was generated

### Markdown references
- `exam_prep/lecture_concepts_image_processing.md`
- `exam_prep/lecture_concepts_face_detection.md`
- `exam_prep/all_methods_index.md`
- `exam_prep/example_code_map.md`

### Runnable notebooks (example-code focused)
- `exam_prep/notebooks/image_processing_methods_demo.ipynb`
- `exam_prep/notebooks/face_detection_methods_demo.ipynb`

## Run prerequisites

Install Python packages:
```bash
pip install opencv-python numpy matplotlib jupyter
```

## Open notebooks

From repo root:
```bash
jupyter notebook exam_prep/notebooks
```

## Notes

- Notebooks auto-locate `class_example_code/imgs` by walking parent directories.
- If OpenCV is missing in your environment, notebook cells that import `cv2` will fail until installed.
- These notebooks use `matplotlib` display instead of `cv2.imshow` so they run cleanly in Jupyter.
