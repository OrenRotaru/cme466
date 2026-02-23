#!/usr/bin/python
import cv2
import sys
import os

# read image
image_path = os.path.join('.', 'imgs', 'jackie.jpg')

image = cv2.imread(image_path)

# Print the dimensions of the image
print(f"Image shape: {image.shape} (Height, Width, Channels)")

# Access pixel values
height, width, _ = image.shape

# Example: Print the pixel values at (0, 0), (1, 1), and (2, 2) (coordinates are row, column)
print("\nPixel Values:")
for i in range(3):  # Print for the first 3 pixels (0, 0), (1, 1), (2, 2)
    if i < height and i < width:  # Check bounds
        b, g, r = image[i, i]  # Extract the BGR values
        print(f"Pixel ({i}, {i}): Blue={b}, Green={g}, Red={r}")

# Extract pixel values for a single channel (e.g., Green)
print("\nFirst few Green channel values:")
for i in range(3):
    if i < height and i < width:
        green_value = image[i, i, 1]  # Access the green channel directly
        print(f"Pixel ({i}, {i}): Green={green_value}")

