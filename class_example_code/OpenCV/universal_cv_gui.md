# Universal CV GUI (`universal_cv_gui.py`)

## Run

From repo root:

```bash
python3 class_example_code/OpenCV/universal_cv_gui.py
```

Optional starting image:

```bash
python3 class_example_code/OpenCV/universal_cv_gui.py --image class_example_code/imgs/people3.jpg
```

## Supported techniques

- Preprocess pipeline (brightness/contrast/gamma/gray/equalization/blur)
- Blur / denoise:
  - Box blur
  - Gaussian blur
  - Median blur
  - Bilateral filter
- Sharpening:
  - Laplacian sharpening
  - Gradient magnitude enhancement
- Canny edge detection
- Simple thresholding
- Adaptive thresholding
- Contours + contour analysis
- Hough circles
- Haar cascade multi-detect:
  - Frontal face
  - Profile face
  - Eyes
  - Smile
- HOG descriptor playground:
  - 64x128 patch
  - Feature length check (3780 with defaults)
  - Gradient visualization
- HOG + SVM people detection

## Keyboard shortcuts

- `o`: open a new image (macOS uses AppleScript picker; fallback is terminal path input)
- `s`: save current output to `tmp/cv_gui_outputs/`
- `n`: next technique
- `p`: previous technique
- `r`: reset sliders for current technique
- `h`: print help
- `q` or `Esc`: quit
