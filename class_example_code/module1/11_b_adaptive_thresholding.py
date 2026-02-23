#!/usr/bin/python

import cv2
import numpy as np
import os
from picamera2 import Picamera2

# Grab images as numpy arrays and leave everything else to OpenCV.
cv2.startWindowThread()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

while True:
    img = picam2.capture_array()

    img_gray = cv2.cvtColor (img, cv2.COLOR_BGR2GRAY)

    # Global threshold
    ret, simple_thresh = cv2.threshold (img_gray, 90, 255, cv2.THRESH_BINARY)

    # Adaptive threshold
    adaptive_thresh = cv2.adaptiveThreshold (img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Visualization
    cv2.imshow ("Gray Image!", img_gray)
    cv2.imshow ("Adaptive Threshold Applied", adaptive_thresh)
    cv2.imshow ("Simple Threshold Applied", simple_thresh)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()