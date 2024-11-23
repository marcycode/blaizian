import cv2
import mediapipe as mp
import time
import math
from collections import deque

QUEUE_SIZE = 5
# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

# Open webcam
cap = cv2.VideoCapture(0)

# Variables to track wrist positions and time
prev_time = 0
right_prev_wrist_position = None
left_prev_wrist_position = None
right_speeds = deque(maxlen=QUEUE_SIZE)
left_speeds = deque(maxlen=QUEUE_SIZE)
for i in range(QUEUE_SIZE):
    right_speeds.append(0)
    left_speeds.append(0)

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    dist = math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    return dist if point1[0] >= point2[0] else -dist

def detect_jab(landmarks):
    """
    Simple logic to detect a jab: 
    Checks if the wrist moves forward (in the x-axis) relative to the shoulder.
    """
    right_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    
    left_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
    left_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

    # Detect a "jab" motion
    left_jab = left_wrist.x > left_shoulder.x - 0.1 # Left jab threshold
    right_jab = right_wrist.x < right_shoulder.x + 0.1  # Right jab threshold

    return left_jab, right_jab

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error accessing the camera.")
        break

    # Flip the frame and convert to RGB
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Process the frame with MediaPipe
    results = pose.process(rgb_frame)

    # Get the current time
    current_time = time.time()

    if results.pose_landmarks:
        # Draw pose landmarks
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Extract landmarks
        landmarks = results.pose_landmarks.landmark

        # Get the right wrist coordinates
        right_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
        left_wrist = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
        right_wrist_position = (right_wrist.x * frame.shape[1], right_wrist.y * frame.shape[0])
        left_wrist_position = (left_wrist.x * frame.shape[1], left_wrist.y * frame.shape[0])


        # If a previous wrist position exists, calculate speed
        if right_prev_wrist_position is not None and left_prev_wrist_position is not None:
            # Calculate displacement
            right_displacement = calculate_distance(right_wrist_position, right_prev_wrist_position)
            left_displacement = calculate_distance(left_wrist_position, left_prev_wrist_position)

            # Calculate time difference
            time_diff = current_time - prev_time

            # Calculate speed (pixels per second)
            if time_diff > 0:  # Avoid division by zero
                right_speed = right_displacement / time_diff
                left_speed = left_displacement / time_diff
                right_speeds.append(right_speed)
                left_speeds.append(left_speed)
                right_average = sum(right_speeds) / len(right_speeds)
                left_average = sum(left_speeds) / len(left_speeds)
                

                # Display the speed on the video frame
                # cv2.putText(frame, f"Right Speed: {right_speed:.2f} px/s", (50, 50),
                #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                # cv2.putText(frame, f"Left Speed: {left_speed:.2f} px/s", (50, 50),
                #             cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Detect jabs
                left_jab, right_jab = detect_jab(landmarks)

                if right_average > 100 and right_jab:
                    cv2.putText(frame, "RIGHT PUNCH!", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)

                if left_average < -100 and left_jab:
                    cv2.putText(frame, "LEFT PUNCH!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)


        # Update the previous wrist position and time
        right_prev_wrist_position = right_wrist_position
        left_prev_wrist_position = left_wrist_position
        prev_time = current_time

    # Show the video frame
    cv2.imshow("Wrist Speed Tracking", frame)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
