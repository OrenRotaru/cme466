# CME 466 Exam Reference: Face Detection (Cascade + HOG)

## 1) Classification pipeline context (FaceDetect_module1)

Traditional CV classifier pipeline:
1. Preprocessing
2. Feature extraction
3. Classification

Key preprocessing ideas from lecture:
- Brightness/contrast normalization
- Mean/std normalization
- Gamma correction
- Color-space conversion (example: RGB -> LAB)
- Crop/resize to fixed input size

Feature extraction purpose:
- Keep discriminative information
- Discard non-essential variation

---

## 2) Haar cascade face detection (Viola-Jones)

### Core method
- Uses Haar-like rectangular features over windows (classically `24 x 24`).
- Feature value = sum(white region) - sum(black region).
- Very large candidate feature set (>160k for 24x24 window).

### Feature selection and boosting
- AdaBoost selects informative weak classifiers.
- Weak classifiers are weighted and combined into a strong classifier.

### Cascade logic for speed
- Stages are arranged from cheap to expensive.
- Most windows are rejected early in first stages.
- Only windows that pass all stages are declared faces.

### Practical OpenCV code pattern
```python
import cv2

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

img = cv2.imread("class_example_code/imgs/people3.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

faces = face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.1,
    minNeighbors=5,
    minSize=(30, 30)
)

for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
```

### Exam-relevant `detectMultiScale` parameter intuition
- `scaleFactor`: image pyramid step. Lower value -> more scales, slower.
- `minNeighbors`: stricter grouping; larger value reduces false positives.
- `minSize`: reject tiny detections.

---

## 3) HOG-based object detection (FaceDetect_module1b)

### What HOG is
- HOG = Histogram of Oriented Gradients.
- Represents local shape/edge structure using gradient orientation histograms.

### Steps covered in lecture material
1. Crop/resize patch to fixed aspect ratio (classical `64 x 128`).
2. Compute x/y gradients (e.g., Sobel).
3. Compute magnitude + angle per pixel.
4. Build 9-bin orientation histograms over `8 x 8` cells.
5. Normalize over `16 x 16` blocks (L2-Hys style).
6. Concatenate block vectors to final feature vector (3780 dims for 64x128).

### Signed vs unsigned gradients
- Common HOG setup uses unsigned orientation (`0..180`), often better for pedestrian-style detection.

### OpenCV usage pattern
```python
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

img = cv2.imread("class_example_code/imgs/people.jpg")
rects, weights = hog.detectMultiScale(
    img,
    winStride=(8, 8),
    padding=(8, 8),
    scale=1.05
)

for (x, y, w, h) in rects:
    cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
```

---

## 4) Cascade vs HOG quick comparison

- **Cascade (Haar + AdaBoost + stage cascade)**
  - Very fast on CPU for constrained tasks
  - Sensitive to pose/lighting/domain shift
  - Great for classic frontal-face setups

- **HOG + SVM detector**
  - Strong shape-based descriptor
  - More robust than raw pixel features
  - Still weaker than modern deep detectors in hard conditions

---

## 5) Face-detection troubleshooting checklist

- Convert to grayscale before cascade detection.
- Tune `minNeighbors` upward if false positives are high.
- Tune `scaleFactor` and `minSize` for speed vs sensitivity.
- Use proper cascade XML path (`cv2.data.haarcascades` is portable).
- For HOG, increase image resolution if small objects are missed.

---

## 6) Practice code from class examples

- `class_example_code/module1/14_face_detection.py` (Pi camera live loop)
- `class_example_code/module1/14_face_detection_img.py` (image-based detection)
- `class_example_code/module1/12_edge_detection_img.py` (edge preprocessing ideas)
- `class_example_code/module1/10_object_tracking.py` (HSV masking, segmentation mindset)

---

## 7) Likely exam prompts and what to include

- "Explain cascade classifier"
  - Mention Haar features, AdaBoost feature selection, stage cascade rejection.

- "Why feature extraction?"
  - State dimensionality reduction + discriminative representation.

- "Explain HOG"
  - Mention gradient histograms, cell/block normalization, illumination robustness.

- "Code-level face detection"
  - Include `CascadeClassifier`, grayscale conversion, `detectMultiScale`, rectangle drawing.
