#!/home/mokarrameh/usask/TA/CME466/env/bin/python3.9
import os
import cv2

image_path = os.path.join('..', 'data', 'sample1.jpg')

img = cv2.imread(image_path)

print(img.shape)
cv2.imshow('image', img)

resized_img = cv2.resize (img, (int(img.shape[0]/2), int(img.shape[1]/2)))

print(resized_img.shape)

cv2.imshow('resized image', resized_img)

cv2.waitKey(0)

cv2.destroyAllWindows()


