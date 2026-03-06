import cv2
from matplotlib import pyplot as plt

FILENAME = "received_image.jpg"

try:
    # Read the image using OpenCV [cite: 483]
    img = cv2.imread(FILENAME)
    
    if img is None:
        print("Could not read image. Did the subscriber save it correctly?")
    else:
        # Convert BGR (OpenCV default) to RGB (Matplotlib standard) [cite: 485]
        img_rgb = img[...,::-1]
        
        # Show the image [cite: 486]
        plt.imshow(img_rgb)
        plt.axis('off') # Optional: hide axes
        plt.show() # [cite: 487]

except ImportError:
    print("Libraries missing. Install them with: pip install opencv-python matplotlib")