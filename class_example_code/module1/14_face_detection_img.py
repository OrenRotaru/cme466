#!/usr/bin/python

import cv2
import os
import sys

face_detector = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml")

# read image
image_path = os.path.join('.', 'imgs', 'people3.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_detector.detectMultiScale(grey, 1.1, 5)

for (x, y, w, h) in faces:
    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0))

cv2.imshow("Camera", img)

cv2.waitKey(0)
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()