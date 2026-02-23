import cv2
import numpy as np
import os

# Read the image
image_path = os.path.join('..', 'data', 'batman.png')
img = cv2.imread(image_path)

# Displaying the image
cv2.imshow('image', img)

# Adjust the brightness and contrast
# Adjusts the brightness by adding 10 to each pixel value
brightness = 10
# Adjusts the contrast by scaling the pixel values by 2.3
contrast = 2.3
enhanced_img = cv2.addWeighted(
    img, contrast, np.zeros(img.shape, img.dtype), 0, brightness)


cv2.imshow('Enhanced image (brightness and contrast)', enhanced_img)

cv2.waitKey(0)
cv2.destroyAllWindows()
