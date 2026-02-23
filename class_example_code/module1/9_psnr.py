#!/usr/bin/python

import cv2
import numpy as np
import os

# read image
image_path = os.path.join('.', 'imgs', 'noisy_image_2.png')

img = cv2.imread (image_path)

if img is None:
    sys.exit("Could not read the image.")

# Classical Blur
k_size = 3
blurred_img = cv2.blur (img, (k_size, k_size))

# Gaussian Blur
gauss_blur = cv2.GaussianBlur (img, (k_size, k_size), 5)

# Median blur
median_blur = cv2.medianBlur (img, k_size)


psnr1 = cv2.PSNR(img, blurred_img)
psnr2 = cv2.PSNR(img, gauss_blur)
psnr3 = cv2.PSNR(img, median_blur)

print(psnr1, 'in dB in Box Blur')
print(psnr2, 'in dB in Gauss Blur')
print(psnr3, 'in dB in Median Blur')

