#!/usr/bin/python

import cv2
import numpy as np
import os
import sys

# Adjust the brightness and contrast
# Adjusts the brightness by adding 10 to each pixel value
brightness = 10
# Adjusts the contrast by scaling the pixel values by 2.3
contrast = 2.3

# read image
image_path = os.path.join('.', 'imgs', 'jackie.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

# cv2.addWeighted() is actually used to add two images together!!
# final pixel values look like this: contrast * img + 0 * zero_array + brightness!
enhanced_img = cv2.addWeighted(img, contrast, np.zeros(img.shape, img.dtype), 0, brightness)
cv2.imshow("original", img)
cv2.imshow("enhanced", enhanced_img)

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
