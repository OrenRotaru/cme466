#!/usr/bin/python

import cv2
import numpy as np
import os
import sys

# read image
image_path = os.path.join('.', 'imgs', 'noisy_image_2.png')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

# Remove noise using a flat/box blur or averaging filter
filtered_img = cv2.blur(img,(5,5))

cv2.imshow("original", img)
cv2.imshow('Filtered Image', filtered_img)

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
