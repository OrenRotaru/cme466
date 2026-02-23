#!/usr/bin/python3.9
import os
import cv2
image_path = os.path.join ('..', 'data', 'elephant.jpg')

img = cv2.imread (image_path)



# Visualization
cv2.imshow ("Oroginal Image", img)

cv2.waitKey (0)

cv2.destroyAllWindows ()
