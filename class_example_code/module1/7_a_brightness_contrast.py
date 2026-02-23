#!/usr/bin/python

import cv2
import numpy as np
from picamera2 import Picamera2


# Adjust the brightness and contrast
# Adjusts the brightness by adding 10 to each pixel value
brightness = 1
# Adjusts the contrast by scaling the pixel values by 2.3
contrast = 1

# Grab images as numpy arrays and leave everything else to OpenCV.
cv2.startWindowThread()

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))
picam2.start()

while True:
    img = picam2.capture_array()

    # Adjust the brightness and contrast
    enhanced_img = cv2.addWeighted(img, contrast, np.zeros(img.shape, img.dtype), 0, brightness)
    cv2.imshow("Camera", enhanced_img)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
