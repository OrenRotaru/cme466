# CME 466 Exam Reference: Image Processing (Module 1a + 1b)

## 1) Digital image fundamentals (imgPro_module1a)

### Digital image model
- An image is modeled as a 2D function `f(x, y)`.
- `x, y` are spatial coordinates; `f(x, y)` is intensity (gray level).
- A digital image is discrete in both coordinates and intensity.

### Image types and bit depth
- Binary image: 1 bit/pixel (`0` or `1`).
- Grayscale image: 8 bits/pixel (`0..255`).
- Color image (RGB/BGR): typically 24 bits/pixel.

### Sampling and quantization
- Sampling controls spatial resolution (number of pixels).
- Quantization controls intensity resolution (number of gray/color levels).
- Low intensity resolution causes false contouring (banding).

### Human visual perception notes
- Subjective brightness is approximately logarithmic vs physical intensity.
- Brightness adaptation, Weber ratio, Mach bands, and simultaneous contrast explain why visual quality can differ from numeric metrics.

### Spatial domain notation
- A sampled image is represented as an `M x N` matrix.
- Spatial domain operations modify pixel values directly at image coordinates.

---

## 2) OpenCV basics from class examples

### Read/write/display
```python
import cv2
img = cv2.imread("class_example_code/imgs/jackie.jpg")
cv2.imwrite("copy.jpg", img)
```

### Resize and crop
```python
# Resize (interpolation matters)
resized = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

# Crop with NumPy slicing
crop = img[600:1050, 150:1250]
```

### Color channels and color spaces
```python
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
```

### Histogram and equalization
```python
hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
eq = cv2.equalizeHist(img_gray)
```

### Arithmetic and logical operations in DIP
- Pixel-wise arithmetic operations (add/subtract/multiply) are foundational in enhancement and blending.
- Binary logical operations (`AND`, `OR`, `XOR`, `NOT`) are common in masking and region combination.

```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
bright_plus = cv2.add(gray, 30)  # arithmetic

_, bin1 = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
_, bin2 = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
mask_and = cv2.bitwise_and(bin1, bin2)  # logical
```

---

## 3) Intensity transforms and enhancement (imgPro_module1a)

### Brightness and contrast
- Linear form: `I_out = alpha * I_in + beta`
- `alpha` controls contrast.
- `beta` controls brightness offset.

```python
enhanced = cv2.convertScaleAbs(img, alpha=1.4, beta=20)
# equivalent idea in examples:
# cv2.addWeighted(img, contrast, np.zeros(img.shape, img.dtype), 0, brightness)
```

### Contrast stretching
- Expands a narrow intensity range to full dynamic range.
- Useful when histogram occupies limited range.

### Histogram equalization
- Uses CDF-based mapping to flatten/redistribute gray-level histogram.
- Improves global contrast in many low-contrast grayscale images.

### Gamma correction (power law)
- `I_out = I_in^gamma` (on normalized intensities `[0,1]`).
- `gamma < 1`: brighter image.
- `gamma > 1`: darker image.

```python
import numpy as np

def gamma_correct_bgr(img_bgr, gamma=0.8):
    lut = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)], dtype=np.uint8)
    return cv2.LUT(img_bgr, lut)
```

---

## 4) Spatial filtering and de-noising (imgPro_module1b)

### Convolution and correlation
- Filtering in spatial domain is local weighted aggregation using kernels.
- Convolution flips kernel 180 degrees; correlation does not.
- Boundary handling options: zero-padding, replicate, symmetric/reflect.

### Smoothing / low-pass filtering
- Removes high-frequency content (noise, but also edges).
- Methods emphasized in class:
  - Averaging (`cv2.blur`)
  - Gaussian (`cv2.GaussianBlur`)
  - Median (`cv2.medianBlur`)
  - Bilateral (`cv2.bilateralFilter` conceptually in lecture)

```python
box = cv2.blur(img, (5, 5))
gauss = cv2.GaussianBlur(img, (5, 5), 1.2)
median = cv2.medianBlur(img, 5)
```

### Noise models covered
- Gaussian
- Gamma (Erlang)
- Exponential
- Uniform
- Impulse (salt & pepper)

---

## 5) Sharpening and edge detection (imgPro_module1b)

### Why derivatives sharpen
- Derivatives emphasize intensity discontinuities.
- First derivative -> gradient edges.
- Second derivative -> Laplacian, stronger fine detail enhancement.

### Gradient and Laplacian
- Gradient magnitude: `sqrt(gx^2 + gy^2)`.
- Laplacian kernels often center at `-4` or `-8` (with/without diagonal terms).
- Sharpening template: `I_sharp = I + c * Laplacian(I)`.

```python
kernel = np.array([[0, -1, 0],
                   [-1, 5, -1],
                   [0, -1, 0]], dtype=np.float32)
sharp = cv2.filter2D(img, -1, kernel)

lap = cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F)
```

### Canny edge detector pipeline
1. Noise reduction
2. Gradient calculation
3. Non-maximum suppression
4. Hysteresis thresholding

```python
edges = cv2.Canny(img, 100, 200)
edges_d = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
edges_e = cv2.erode(edges_d, np.ones((3, 3), np.uint8), iterations=1)
```

---

## 6) Thresholding and contours (imgPro_module1b)

### Simple/global thresholding
```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, th = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)
```

Threshold modes highlighted:
- `cv2.THRESH_BINARY`
- `cv2.THRESH_BINARY_INV`
- `cv2.THRESH_TRUNC`
- `cv2.THRESH_TOZERO`
- `cv2.THRESH_TOZERO_INV`

### Adaptive thresholding
- Better for nonuniform illumination.
- Local threshold computed from neighborhood.

```python
ad = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    11, 2
)
```

### Contours
- Contour: curve joining continuous points of equal intensity.
- Usually find on binary image (white foreground on black background).

```python
_, inv = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
contours, hierarchy = cv2.findContours(inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    if cv2.contourArea(cnt) > 200:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
```

---

## 7) Evaluation metrics and exam cautions

### Objective metrics
- `MSE`, `PSNR`
- Useful but can disagree with perceived quality.

```python
psnr_val = cv2.PSNR(reference_img, test_img)
```

### Subjective evaluation
- Human perception can rate images differently than metric rankings.
- Mention HVS effects when discussing why PSNR is not always enough.

---

## 8) High-value exam comparisons

- **Histogram equalization vs contrast stretching**:
  - Equalization uses CDF remapping.
  - Stretching linearly maps min/max to full range.

- **Gradient vs Laplacian**:
  - Gradient: edge emphasis.
  - Laplacian: fine detail enhancement and sharpening.

- **Simple vs adaptive threshold**:
  - Simple: one global threshold.
  - Adaptive: local threshold, handles varying light.

- **Blur methods**:
  - Box: fastest, coarse smoothing.
  - Gaussian: weighted smoothing, common default.
  - Median: strong for salt-and-pepper noise.
  - Bilateral: preserves edges better (costlier).

---

## 9) Code files to practice directly
- `class_example_code/module1/1_read_write_img.py`
- `class_example_code/module1/3_color_channels.py`
- `class_example_code/module1/4_color_spaces.py`
- `class_example_code/module1/5_a_resize.py`
- `class_example_code/module1/5_b_cropping.py`
- `class_example_code/module1/7_a_brightness_contrast_img.py`
- `class_example_code/module1/7_b_sharp_img.py`
- `class_example_code/module1/8_blurring_img.py`
- `class_example_code/module1/9_psnr.py`
- `class_example_code/module1/11_a_simple_thresholding_img.py`
- `class_example_code/module1/11_b_adaptive_thresholding.py`
- `class_example_code/module1/12_edge_detection_img.py`
- `class_example_code/module1/13_contours_img.py`
- `class_example_code/module1/10_object_tracking.py`
