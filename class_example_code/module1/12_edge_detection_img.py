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

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()