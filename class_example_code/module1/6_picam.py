#!/usr/bin/python

import cv2
from picamera2 import Picamera2

# Grab images as numpy arrays and leave everything else to OpenCV.
cv2.startWindowThread()

# Create a Picamera2 object
picam2 = Picamera2()

# Generate a camera configuration and configure camera
# create_preview_configuration(): will generate a configuration suitable for displaying camera preview images
# on the display, or prior to capturing a still image
# XRGB8888: - every pixel is packed into 32-bits, with a dummy 255 value at the end, so a pixel would look like [B, G, R,
# 255] when captured in Python. (These format descriptions can seem counter-intuitive, but the underlying
# infrastructure tends to take machine endianness into account, which can mix things up!)

picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (640, 480)}))

# Start the preview window
picam2.start()

while True:
    im = picam2.capture_array()

    #grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

    cv2.imshow("Camera", im)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):    
        break

# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
