import os
import cv2

# Kind of an object detector :)
image_path = os.path.join ('..', 'data', 'birds.jpg')

img = cv2.imread (image_path)

img_gray = cv2.cvtColor (img, cv2.COLOR_BGR2GRAY)

ret, thresh = cv2.threshold (img_gray, 127, 255, cv2.THRESH_BINARY_INV)

contours, hierarchy = cv2.findContours (thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    #print (cv2.contourArea(cnt))
    # Removing noise
    if cv2.contourArea(cnt) > 200:
        # cv2.drawContours (img, cnt, -1, (0, 255, 0), 1)

        # Drawing bounding boxes around the objects
        x1, y1, width, height = cv2.boundingRect (cnt)

        cv2.rectangle (img, (x1, y1), (x1+ width, y1 + height), (0, 255, 0), 2)



# Visualization
cv2.imshow ("Oroginal Image", img)
cv2.imshow ("GRAY image", img_gray)
cv2.imshow ("Threshold", thresh)

cv2.waitKey (0)

cv2.destroyAllWindows ()
