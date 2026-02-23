#!/home/mokarrameh/usask/TA/CME466/env/bin/python3.9
import os
import cv2

# read image
image_path = os.path.join('..', 'data', 'sample1.jpg')

img = cv2.imread (image_path)

# write image
cv2.imwrite(os.path.join('..', 'data', 'sample1_copy.jpg'), img)

# visualize images
cv2.imshow('image', img)
cv2.waitKey(0)
