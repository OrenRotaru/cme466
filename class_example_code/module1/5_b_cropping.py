#!/usr/bin/python

# Import necessary modules
import os
import cv2
import sys

# Read the image
image_path = os.path.join('.', 'imgs', 'jackie_big.jpg')
img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

# check for errors
if img is None:
    sys.exit("Could not read the image.")

# Printing the shape of the image (height, width, channels)
print(img.shape)

# Displaying the image
cv2.imshow('image', img)

# image is just a numpy array. So, to crop it we can just use slicing techniques
cropped_img = img[600:1050, 150:1250]
cv2.imshow('cropped image', cropped_img)
print(cropped_img.shape)

cv2.waitKey (0)
cv2.destroyAllWindows()
