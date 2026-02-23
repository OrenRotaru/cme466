#!/usr/bin/python
import os
import cv2
import sys

# read image
image_path = os.path.join('.', 'imgs', 'jackie.jpg')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

# write image
cv2.imwrite(os.path.join('.', 'imgs', 'sample1_copy.jpg'), img)

# This line opens a pop up window
# visualize images
cv2.imshow('image', img)
cv2.waitKey(0)
# cv2.destroyAllWindows() simply destroys all the windows we created.
cv2.destroyAllWindows()


