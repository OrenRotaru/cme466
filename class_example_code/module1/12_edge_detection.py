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

    # Canny
    image_edge = cv2.Canny (img, 100, 200)

    # Dialate
    image_edge_dilate = cv2.dilate (image_edge, np.ones ((3, 3), dtype=np.int8))

    # Erode
    image_edge_erode = cv2.erode (image_edge_dilate, np.ones ((3, 3), dtype=np.int8))

    # Visualization
    cv2.imshow ("Original Image", img)
    cv2.imshow ("Edges", image_edge)
    cv2.imshow ("Dilated", image_edge_dilate)
    cv2.imshow ("Erode", image_edge_erode)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()