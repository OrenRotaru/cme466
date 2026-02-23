#!/usr/bin/python

import cv2
import numpy as np
from picamera2 import Picamera2

# Grab images as numpy arrays and leave everything else to OpenCV.
cv2.startWindowThread()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

# Create the sharpening kernel
kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])

while True:
    img = picam2.capture_array()
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    
    sharpened_img = cv2.filter2D(img, -1, kernel)

    cv2.imshow("Camera", sharpened_img)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
