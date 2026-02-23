#!/usr/bin/python
# Import necessary modules
import os
import cv2
import sys

# Read the image
image_path = os.path.join('.', 'imgs', 'jackie.jpg')

img = cv2.imread(image_path)

# check for errors
if img is None:
    sys.exit("Could not read the image.")

# Printing the shape of the image (height, width, channels)
print(img.shape)

# Displaying the image
cv2.imshow('image', img)

# Resizing the image
resized_img = cv2.resize (img,None,fx=2, fy=2, interpolation = cv2.INTER_CUBIC)

print(resized_img.shape)

cv2.imshow('resized image', resized_img)

# another way
height, width = img.shape[:2]
resized_img_2 = cv2.resize(img,(2*width, 2*height), interpolation = cv2.INTER_LINEAR)

print(resized_img_2.shape)

cv2.imshow('resized image (2)', resized_img_2)

cv2.waitKey(0)

cv2.destroyAllWindows()
