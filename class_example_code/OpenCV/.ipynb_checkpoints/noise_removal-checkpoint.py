#!/usr/bin/python3
import os
import cv2

image_path = os.path.join ('.', 'data', 'noisy_image_2.png')

try:
    img = cv2.imread (image_path)
except:
    print ("Error while reading the image ...")

# Classical Blur
k_size = 5
blurred_img = cv2.blur (img, (k_size, k_size))

# Gaussian Blur
gauss_blur = cv2.GaussianBlur (img, (k_size, k_size), 5)

# Median blur
median_blur = cv2.medianBlur (img, k_size)


# Visualization
cv2.imshow ("Noisy Image", img)
cv2.imshow ("Classical Blur", blurred_img)
cv2.imshow ("Gaussina Blur", gauss_blur)
cv2.imshow ("Median Blur", median_blur)
cv2.waitKey(0)

cv2.destroyAllWindows ()