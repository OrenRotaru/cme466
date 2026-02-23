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
    ret, thresh = cv2.threshold (img_gray, 90, 255, cv2.THRESH_BINARY)

    # Could be used in image segmentation and detection!!!
    gray_thresh = cv2.blur (thresh, (5, 5))
    ret, thresh_2 = cv2.threshold (gray_thresh, 80, 255, cv2.THRESH_BINARY)

    # Visualization
    cv2.imshow ("Grayed Image!", img_gray)
    cv2.imshow ("1st Threshold applied", thresh)
    cv2.imshow ("2nd Threshold applied", thresh_2)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()