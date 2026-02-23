#!/usr/bin/python3
import os
import cv2

image_path = os.path.join ('.', 'data', 'squirel.jpg')
img = cv2.imread (image_path)

img_gray = cv2.cvtColor (img, cv2.COLOR_BGR2GRAY)

# Global threshold
ret, simple_thresh = cv2.threshold (img_gray, 90, 255, cv2.THRESH_BINARY)

# Adaptive threshold
adaptive_thresh = cv2.adaptiveThreshold (img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

# Could be used in image segmentation and detection!!!
#gray_thresh = cv2.blur (thresh, (10, 10))
#ret, final_thresh = cv2.threshold (gray_thresh, 80, 255, cv2.THRESH_BINARY)

# Visualization
cv2.imshow ("Image", img)
cv2.imshow ("Grayed Image!", img_gray)
cv2.imshow ("Adaptive Threshold applied", adaptive_thresh)
cv2.imshow ("Simple Threshold Applied", simple_thresh)
#cv2.imshow ("Doing it all over again ...", final_thresh)
cv2.waitKey (0)

cv2.destroyAllWindows ()