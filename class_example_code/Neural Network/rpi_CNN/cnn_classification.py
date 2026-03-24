# Import the packages
from PIL import Image
import numpy as np
import onnxruntime
import torch
import cv2

def preprocess_image(image_path, height, width):
    """Preprocess an image for ONNX inference"""
    image = Image.open(image_path).convert("RGB")  # Ensure 3 channels
    image = image.resize((width, height), Image.LANCZOS)
    image_data = np.asarray(image).astype(np.float32) / 255.0  # Normalize to [0,1]
    image_data = image_data.transpose([2, 0, 1])  # Convert to CHW

    # Standard ImageNet normalization (change if needed)
    mean = np.array([0.485, 0.456, 0.406]).reshape(3, 1, 1)
    std = np.array([0.229, 0.224, 0.225]).reshape(3, 1, 1)

    # Apply normalization
    image_data = (image_data - mean) / std

    # Add batch dimension
    image_data = np.expand_dims(image_data, axis=0).astype(np.float32)
    return image_data

def softmax(x):
    """Compute softmax values for each set of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def run_sample(session, image_path, categories):
    """Run inference on a single image"""
    input_tensor = preprocess_image(image_path, 64, 64)
    output = session.run(None, {'input': input_tensor})[0]  # Get model output
    output = output.flatten()
    output = softmax(output)  # Apply softmax if needed
    top5_catid = np.argsort(-output)

    # Print top predictions
    for catid in top5_catid[:5]:  # Display only top-5 results
        print(categories[catid], output[catid])

# Main function to run inference
if __name__ == "__main__":
    categories = ['hot_dog', 'pizza', 'steak', 'sushi', 'tacos']

    # Create ONNX Inference Session
    session = onnxruntime.InferenceSession("model.onnx")

    # Image file path (Fix: Load image in preprocess function)
    image_file = "steak.jpg"

    # Run inference
    run_sample(session, image_file, categories)
