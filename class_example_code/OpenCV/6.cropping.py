#!/home/mokarrameh/usask/TA/CME466/env/bin/python3.9
import os
import cv2

image_path = os.path.join('..', 'data', 'fedor.jpg')
img = cv2.imread (image_path)

cv2.imshow('image', img)
print(img.shape)

# resized_img = cv2.resize(img, (int(img.shape[0]/2), int(img.shape[1]/2)))
# cv2.imshow('resized image', resized_img)
# print(resized_img.shape)

# image is just a numpy array. So, to crop it we can just use slicing techniques
cropped_img = img[600:1050, 150:1250]
cv2.imshow('cropped image', cropped_img)
print(cropped_img.shape)

cv2.waitKey (0)
cv2.destroyAllWindows()
