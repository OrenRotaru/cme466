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

    # Classical Blur
    k_size = 3
    blurred_img = cv2.blur (img, (k_size, k_size))

    # Gaussian Blur
    gauss_blur = cv2.GaussianBlur (img, (k_size, k_size), 5)

    # Median blur
    median_blur = cv2.medianBlur (img, k_size)

    cv2.imshow("original", img)
    cv2.imshow("blurred", blurred_img)
    cv2.imshow("Gaussian", gauss_blur)
    cv2.imshow("median", median_blur)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()