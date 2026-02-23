import cv2
import time
from ffpyplayer.player import MediaPlayer

video_path = "imgs/BR99.mp4"

# Open the video file
cap = cv2.VideoCapture(video_path)
player = MediaPlayer(video_path)  # Load the audio player

# Check if video opened successfully
if not cap.isOpened():
    print("Error opening video file")
    exit()

# Get video FPS and calculate frame delay
fps = cap.get(cv2.CAP_PROP_FPS)
frame_time = 1 / fps  # Time per frame in seconds

# Start the video playback
while cap.isOpened():
    start_time = time.time()  # Track frame start time

    ret, frame = cap.read()
    if not ret:
        break

    # Get the current audio frame
    audio_frame, val = player.get_frame()

    # Display the video frame
    cv2.imshow("Frame", frame)

    # Sync the video playback time
    elapsed_time = time.time() - start_time
    sleep_time = max(0, frame_time - elapsed_time)
    time.sleep(sleep_time)  # Adjust frame timing

    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
player.close()
