#!/usr/bin/python
import os
import cv2
import sys

image_path = os.path.join ('.', 'imgs', 'jackie.jpg')
#image_path = os.path.join ('..', 'data', 'miguel.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

cv2.imshow('BGR image', img)
print(img.shape)

img_rgb = cv2.cvtColor (img, cv2.COLOR_BGR2RGB)
cv2.imshow ('RGB image', img_rgb)
print(img_rgb.shape)

img_gray = cv2.cvtColor (img, cv2.COLOR_BGR2GRAY)
cv2.imshow ('Gray image', img_gray)
print(img_gray.shape)

img_hsv = cv2.cvtColor (img, cv2.COLOR_BGR2HSV)
cv2.imshow ('HSV image', img_hsv)
print(img_hsv.shape)


cv2.waitKey (0)
cv2.destroyAllWindows ()
