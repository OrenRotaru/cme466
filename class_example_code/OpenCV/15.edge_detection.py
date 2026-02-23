import os
import cv2
import numpy as np

image_path = os.path.join ('..', 'data', 'CB2.jpg')

img = cv2.imread (image_path)

# Canny
image_edge = cv2.Canny (img, 100, 200)

# Dialate
image_edge_dilate = cv2.dilate (image_edge, np.ones ((3, 3), dtype=np.int8))

# Erode
image_edge_erode = cv2.erode (image_edge_dilate, np.ones ((3, 3), dtype=np.int8))

# Visualization
cv2.imshow ("Oroginal Image", img)
cv2.imshow ("Edges", image_edge)
cv2.imshow ("Dilated", image_edge_dilate)
cv2.imshow ("Erode", image_edge_erode)

cv2.waitKey (0)

cv2.destroyAllWindows ()
