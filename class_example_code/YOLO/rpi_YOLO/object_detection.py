import cv2

from ultralytics import YOLO

# Load the exported NCNN model
ncnn_model = YOLO("yolo11n_ncnn_model")

image_path = "goat.jpg"
image = cv2.imread(image_path)

results = ncnn_model(image)

# Visualize the results
annotated_img = results[0].plot()

cv2.imshow("img", annotated_img)
cv2.waitKey(0)
# Release resources and close windows
cv2.destroyAllWindows()