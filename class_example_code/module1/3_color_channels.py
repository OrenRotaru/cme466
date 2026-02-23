#!/usr/bin/python
import cv2
import sys
import os
import numpy as np

# read image
image_path = os.path.join('.', 'imgs', 'jackie.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

blank = np.zeros_like(img[:,:,0])

# Extract the Blue, Green, and Red channels
b_img = cv2.merge([img[:, :, 0], blank, blank])  # Only blue
g_img = cv2.merge([blank, img[:, :, 1], blank])  # Only green
r_img = cv2.merge([blank, blank, img[:, :, 2]])    # Only red

cv2.imshow('original', img)
# show Blue values
cv2.imshow('image-G', g_img)
cv2.imshow('image_B', b_img)
cv2.imshow('image_R', r_img)
cv2.waitKey(0)
cv2.destroyAllWindows()

