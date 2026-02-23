#!/usr/bin/python

import cv2
import numpy as np
import os
import sys

# read image
image_path = os.path.join('.', 'imgs', 'birds.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

img_gray = cv2.cvtColor (img, cv2.COLOR_BGR2GRAY)

# here the birds are blabk with white wky. But object to be found should be white with black background.
# So, we need to perform inverse threshold
ret, thresh = cv2.threshold (img_gray, 127, 255, cv2.THRESH_BINARY_INV)

contours, hierarchy = cv2.findContours (thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

contours_num = 0

for cnt in contours:
    #print (cv2.contourArea(cnt))
    # Removing noise
    if cv2.contourArea(cnt) > 200:
        cv2.drawContours (img, cnt, -1, (0, 255, 0), 1)
        # Count the counturs!!!
        # Drawing bounding boxes around the objects
        x1, y1, width, height = cv2.boundingRect (cnt)

        cv2.rectangle (img, (x1, y1), (x1+ width, y1 + height), (0, 255, 0), 2)
        contours_num += 1

print (f"Number of contours: {contours_num}")


# Visualization
cv2.imshow ("Original Image", img)
cv2.imshow ("GRAY image", img_gray)
cv2.imshow ("Inverse Threshold", thresh)

cv2.waitKey(0) 
# Release the VideoCapture object and close all windows
cv2.destroyAllWindows()