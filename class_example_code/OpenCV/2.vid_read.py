#!/home/mokarrameh/usask/TA/CME466/env/bin/python3.9
import os
import cv2

# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
video_path = os.path.join('..', 'data', 'BR99.mp4')

video_cap = cv2.VideoCapture(video_path)

# Check if camera opened successfully
if (video_cap.isOpened()== False): 
  print("Error opening video stream or file")

# Get video details
fps = video_cap.get(cv2.CAP_PROP_FPS)
width = int(video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

while video_cap.isOpened():
    # Reading frames of the video
    ret, frame = video_cap.read ()

    if not ret:
        break
        
    cv2.imshow('frame', frame)
    
    # Break the loop if 'q' is pressed
    if cv2.waitKey(int(1000 / fps)) & 0xFF == ord('q'):
        break

# Release the VideoCapture object and close all windows
video_cap.release()
cv2.destroyAllWindows()
