import onnxruntime as ort
import numpy as np
import cv2
import os

# Load the ONNX model
session = ort.InferenceSession("model.onnx")

# Define class labels
class_names = [
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
]

# Directory containing images
image_dir = "sample_images"

# Loop through all images in the directory
for filename in os.listdir(image_dir):
    if filename.endswith(".png") or filename.endswith(".jpg"):  # Check for image files
        file_path = os.path.join(image_dir, filename)

        # Load and preprocess the image
        image = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
        image = image.astype(np.float32)
        image = np.expand_dims(image, axis=0)

        # Run inference
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name
        output = session.run([output_name], {input_name: image})

        # Get predicted class
        predicted_label = np.argmax(output)
        predicted_class = class_names[predicted_label]

        # Print filename and prediction
        print(f"{filename}: Predicted Class -> {predicted_label}: {predicted_class}")

                # Convert image back to displayable format
        display_image = (image.squeeze() * 255).astype(np.uint8)  # Convert back to 8-bit grayscale

        # Resize for better visualization
        display_image = cv2.resize(display_image, (280, 280), interpolation=cv2.INTER_NEAREST)

        # Overlay text with prediction
        cv2.putText(display_image, predicted_class, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Show the image
        cv2.imshow(filename, display_image)

        # Wait for a key press before moving to the next image
        cv2.waitKey(0)

# Close all OpenCV windows
cv2.destroyAllWindows()
