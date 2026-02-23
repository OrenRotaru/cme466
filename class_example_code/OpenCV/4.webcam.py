#!/home/mokarrameh/usask/TA/CME466/env/bin/python3.9
import cv2

# read webcam
webCam = cv2.VideoCapture(0)

# Display
while True:
    ret, frame = webCam.read()

    cv2.imshow('frame', frame)

    if cv2.waitKey(40) & 0xFF == ord('q'):
        break
    
webCam.release()
cv2.destroyAllWindows()
