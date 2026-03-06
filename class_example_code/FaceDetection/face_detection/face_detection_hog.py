# Add the necessary libraries
import matplotlib.pyplot as plt
import dlib
import os
import cv2 as cv

# Afunction to display images using OpenCV library


def display_img_cv(img):
    cv.imshow("Original Image", img)
    cv.waitKey(0)
    # simply destroys all the windows we created.
    cv.destroyAllWindows()


# Load the target image
image_path = os.path.join('..', 'data', 'people3.jpg')
img = cv.imread(image_path)
print(f"image shape: {img.shape}")

# Displaying the image using Matplotlib library
display_img_cv(img)

# Create a face detctor
face_detector_hog = dlib.get_frontal_face_detector()

detections = face_detector_hog(img, 1)

# detections: bounding boxes aroud the faces
print(f"Detections {detections}")
print(f"Number of detected faces: {len(detections)}")


# Drawing a bounding box around detected faces
for face in detections:
    # position of the detected face
    # print(face)
    # print(face.left())
    # print(face.top())
    # print(face.right())
    # print(face.bottom())
    l, t, r, b = face.left(), face.top(), face.right(), face.bottom()
    cv.rectangle(img, (l, t), (r, b), (0, 255, 255), 2)


display_img_cv(img)
