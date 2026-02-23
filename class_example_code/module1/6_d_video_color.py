import cv2

# Create a VideoCapture object and read from input file
cap = cv2.VideoCapture('imgs/BR99.mp4')

# Check if video opened successfully
if not cap.isOpened():
    print("Error opening video file")
    exit()

# Get the frame rate of the video
fps = cap.get(cv2.CAP_PROP_FPS)
frame_delay = int(1000 / fps)  # Convert FPS to milliseconds per frame

# Read until video is completed
while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        #img = cv2.cvtColor (frame, cv2.COLOR_BGR2HSV)
        img = cv2.cvtColor (frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow ('HSV image', img)

        # Press 'q' to exit
        if cv2.waitKey(frame_delay) & 0xFF == ord('q'):
            break
    else:
        break

# Release everything
cap.release()
cv2.destroyAllWindows()
