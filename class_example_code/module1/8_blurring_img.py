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

# Classical Blur
k_size = 3
blurred_img = cv2.blur (img, (k_size, k_size))

# Gaussian Blur
gauss_blur = cv2.GaussianBlur (img, (k_size, k_size), 5)

# Median blur
median_blur = cv2.medianBlur (img, k_size)


# Visualization
cv2.imshow ("Original Noisy", img)
cv2.imshow ("Box Blurred Legends", blurred_img)
cv2.imshow ("Gaussina Blur", gauss_blur)
cv2.imshow ("Median Blur", median_blur)

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()
