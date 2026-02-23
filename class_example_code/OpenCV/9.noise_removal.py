import cv2 
import numpy as np 
import os
  
# Read the image
image_path = os.path.join('..', 'data', 'noisy_image_2.png')
img = cv2.imread (image_path)

# Displaying the image
cv2.imshow('image', img)
  
# Remove noise using a median filter 
filtered_img = cv2.medianBlur(img, 11) 

cv2.imshow('Filtered Image', filtered_img)

cv2.waitKey (0)
cv2.destroyAllWindows()
