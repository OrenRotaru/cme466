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

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()