# CME 466 Method Index (Image Processing + Face Detection)

This is a consolidated checklist of methods and concepts from:
- `imgPro_module1a.pdf`
- `imgPro_module1b.pdf`
- `FaceDetect_module1.pdf`
- `FaceDetect_module1b.pdf`
- `class_example_code/` scripts and notebooks

---

## A) Core concepts by lecture

### imgPro_module1a
- Digital image model `f(x, y)`
- Binary / grayscale / color representation
- Sampling and quantization
- Spatial domain coordinates
- Intensity resolution and false contouring
- HVS perception effects (Weber ratio, Mach bands, simultaneous contrast)
- OpenCV basics (read/write/display)
- Resizing and interpolation
- Cropping
- Color channels and color spaces
- Histogram, brightness/contrast adjustment
- Histogram equalization
- Contrast stretching
- Gamma correction

### imgPro_module1b
- Spatial filtering as convolution
- Correlation vs convolution
- Boundary handling (zero/replicate/symmetric)
- Objective vs subjective quality evaluation
- MSE and PSNR concepts
- Noise models: Gaussian, Gamma, Exponential, Uniform, Salt-and-Pepper
- De-noising/blurring (box, Gaussian, median, bilateral)
- Image sharpening (gradient/Laplacian)
- Canny edge detection
- Simple thresholding
- Adaptive thresholding
- Contours and contour drawing/analysis

### FaceDetect_module1
- Image classification pipeline (preprocess -> features -> classifier)
- Preprocessing for detection/classification
- Haar-like features
- AdaBoost for weak feature/classifier selection
- Cascade stages for fast rejection
- Sliding-window detection intuition

### FaceDetect_module1b
- HOG feature descriptor motivation
- Gradient magnitude/direction features
- 8x8 cell histograms (9 bins)
- 16x16 block normalization (L2-Hys style)
- 3780-D descriptor for 64x128 patch
- HOG + SVM detector in OpenCV

---

## B) OpenCV methods used in class examples

### Image I/O and display
- `cv2.imread`
- `cv2.imwrite`
- `cv2.imshow`
- `cv2.waitKey`
- `cv2.destroyAllWindows`

### Video/camera
- `cv2.VideoCapture`
- `cv2.CAP_PROP_FPS`
- `cv2.CAP_PROP_FRAME_WIDTH`
- `cv2.CAP_PROP_FRAME_HEIGHT`
- `cv2.CAP_PROP_FRAME_COUNT`
- `cv2.CAP_PROP_POS_FRAMES`

### Color and channels
- `cv2.cvtColor`
- `cv2.COLOR_BGR2RGB`
- `cv2.COLOR_BGR2GRAY`
- `cv2.COLOR_BGR2HSV`
- `cv2.COLOR_BGR2YUV`
- `cv2.split`
- `cv2.merge`

### Intensity/contrast/histogram
- `cv2.addWeighted`
- `cv2.convertScaleAbs`
- `cv2.equalizeHist`
- `cv2.calcHist`
- `cv2.normalize`
- `cv2.NORM_MINMAX`

### Resize/crop/interpolation
- `cv2.resize`
- `cv2.INTER_LINEAR`
- `cv2.INTER_CUBIC`

### Filtering, denoising, sharpening
- `cv2.blur`
- `cv2.GaussianBlur`
- `cv2.medianBlur`
- `cv2.filter2D`
- `cv2.Laplacian`
- `cv2.CV_64F`

### Edge and morphology
- `cv2.Canny`
- `cv2.dilate`
- `cv2.erode`

### Thresholding
- `cv2.threshold`
- `cv2.adaptiveThreshold`
- `cv2.THRESH_BINARY`
- `cv2.THRESH_BINARY_INV`
- `cv2.ADAPTIVE_THRESH_GAUSSIAN_C`

### Contours and shape extraction
- `cv2.findContours`
- `cv2.RETR_TREE`
- `cv2.RETR_EXTERNAL`
- `cv2.CHAIN_APPROX_SIMPLE`
- `cv2.contourArea`
- `cv2.drawContours`
- `cv2.boundingRect`
- `cv2.rectangle`

### Segmentation / masking
- `cv2.inRange`
- `cv2.bitwise_and`

### Quality metric
- `cv2.PSNR`

### Detection
- `cv2.CascadeClassifier`
- `detectMultiScale` (method on cascade object)
- `cv2.HOGDescriptor`
- `cv2.HOGDescriptor_getDefaultPeopleDetector`

---

## C) Minimal code skeletons to memorize

### 1) Simple thresholding
```python
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, th = cv2.threshold(gray, 90, 255, cv2.THRESH_BINARY)
```

### 2) Adaptive thresholding
```python
ad = cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    11, 2
)
```

### 3) Canny + morphology
```python
edges = cv2.Canny(img, 100, 200)
edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
edges = cv2.erode(edges, np.ones((3, 3), np.uint8), iterations=1)
```

### 4) Contours + bounding boxes
```python
contours, _ = cv2.findContours(bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
for c in contours:
    if cv2.contourArea(c) > 200:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
```

### 5) Haar cascade face detection
```python
cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
faces = cascade.detectMultiScale(gray, 1.1, 5)
```

### 6) HOG people detection
```python
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
rects, weights = hog.detectMultiScale(img, winStride=(8, 8), padding=(8, 8), scale=1.05)
```

---

## D) Fast exam recall formulas

- Linear brightness/contrast: `I_out = alpha * I_in + beta`
- Gamma correction: `I_out = I_in^gamma`
- Gradient magnitude: `|grad| = sqrt(gx^2 + gy^2)`
- Laplacian sharpening idea: `I_sharp = I + c * Laplacian(I)`
- PSNR: `PSNR = 10 * log10(MAX_I^2 / MSE)`

---

## E) Best practice mapping (concept -> method)

- Improve global contrast -> `equalizeHist`, contrast stretching
- Remove Gaussian-like noise -> `GaussianBlur`
- Remove salt-and-pepper noise -> `medianBlur`
- Preserve edges while denoising -> bilateral filtering concept
- Detect strong boundaries -> `Canny`
- Segment under uneven light -> `adaptiveThreshold`
- Count/track blob-like objects -> threshold + `findContours`
- Fast frontal-face baseline -> Haar cascade
- Shape-based human/object cues -> HOG descriptor + SVM
