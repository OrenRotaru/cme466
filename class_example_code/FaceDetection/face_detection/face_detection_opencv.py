# Add the necessary libraries
import os
import cv2 as cv
import matplotlib.pyplot as plt

# Load the target image
image_path = os.path.join('..', 'data', 'people3.jpg')
img = cv.imread(image_path)
print(f"image shape: {img.shape}")

cv.imshow('original image', img)
cv.waitKey(0)
cv.destroyAllWindows()

face_cascade = cv.CascadeClassifier()
eyes_cascade = cv.CascadeClassifier()

# Using pretrained models
# Loading pretrained classifiers
if not face_cascade.load(cv.samples.findFile('../data/haarcascades/haarcascade_frontalface_alt.xml')):
    print('--(!)Error loading face cascade')
    exit(0)
if not eyes_cascade.load(cv.samples.findFile('../data/haarcascades/haarcascade_eye_tree_eyeglasses.xml')):
    print('--(!)Error loading eyes cascade')
    exit(0)

# Optimized for people.jpg


def detectAndDisplay(frame):
    frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame_gray = cv.equalizeHist(frame_gray)
    # -- Detect faces
    faces = face_cascade.detectMultiScale(
        frame_gray, scaleFactor=1.0001, minNeighbors=20, minSize=(200, 200), maxSize=(225, 225))

    print(faces)
    print(f"{len (faces)} faces are detected")

    for (x, y, w, h) in faces:
        center = (x + w//2, y + h//2)
        frame = cv.ellipse(frame, center, (w//2, h//2),
                           0, 0, 360, (255, 0, 255), 4)
        faceROI = frame_gray[y:y+h, x:x+w]
        # -- In each face, detect eyes
        eyes = eyes_cascade.detectMultiScale(
            faceROI, scaleFactor=1.01, minNeighbors=10, minSize=(10, 10), maxSize=(50, 50))
        for (x2, y2, w2, h2) in eyes:
            eye_center = (x + x2 + w2//2, y + y2 + h2//2)
            radius = int(round((w2 + h2)*0.25))
            frame = cv.circle(frame, eye_center, radius, (255, 0, 0), 4)
    cv.imshow('output', frame)

# Optimized for people3.jpg


def detectAndDisplay2(frame):
    frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    frame_gray = cv.equalizeHist(frame_gray)
    # -- Detect faces
    faces = face_cascade.detectMultiScale(
        frame_gray, scaleFactor=1.001, minNeighbors=12, minSize=(70, 70), maxSize=(500, 500))

    print(faces)
    print(f"{len (faces)} faces are detected")

    for (x, y, w, h) in faces:
        center = (x + w//2, y + h//2)
        frame = cv.ellipse(frame, center, (w//2, h//2),
                           0, 0, 360, (255, 0, 255), 4)
        faceROI = frame_gray[y:y+h, x:x+w]
        # -- In each face, detect eyes
        eyes = eyes_cascade.detectMultiScale(
            faceROI, scaleFactor=1.01, minNeighbors=10, minSize=(10, 10), maxSize=(50, 50))
        for (x2, y2, w2, h2) in eyes:
            eye_center = (x + x2 + w2//2, y + y2 + h2//2)
            radius = int(round((w2 + h2)*0.25))
            frame = cv.circle(frame, eye_center, radius, (255, 0, 0), 4)

    cv.imshow('output', frame)
    cv.waitKey(0)
    cv.destroyAllWindows()


detectAndDisplay2(img)
