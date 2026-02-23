import cv2 
import numpy as np 
import os
  
# Read the image
image_path = os.path.join('..', 'data', 'menu.png')
img = cv2.imread (image_path)

# Displaying the image
cv2.imshow('Original image', img)

# Create the sharpening kernel 
kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]]) 
  
# Sharpen the image 
sharpened_img = cv2.filter2D(img, -1, kernel) 

cv2.imshow('Sharpened Image', sharpened_img)

cv2.waitKey (0)
cv2.destroyAllWindows()
