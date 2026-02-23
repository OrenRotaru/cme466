#!/usr/bin/python

import cv2
import numpy as np
import os
import sys

# read image
image_path = os.path.join('.', 'imgs', 'jackie.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

sharpened_img = cv2.Laplacian(img, cv2.CV_64F)


cv2.imshow("original", img)
cv2.imshow("sharpened", sharpened_img)

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
