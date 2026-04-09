import cv2
import time
from ultralytics import YOLO

# Load YOLO model
model = YOLO("yolov8n.pt")

# Start webcam
cap = cv2.VideoCapture(0)

# FPS calculation
prev_time = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Run detection
    results = model(frame)

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label == "person":
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

                # Worker label
                cv2.putText(frame, "Worker", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                # 🔴 RED ALERT BOX (Professional UI)
                cv2.rectangle(frame, (x1, y2+10), (x2, y2+40), (0,0,255), -1)

                cv2.putText(frame, "NO HELMET", (x1+5, y2+30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)

                # ALERT text (top)
                cv2.putText(frame, "ALERT!", (50,50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

                print("⚠️ Safety Violation Detected!")

    # 🟡 FPS DISPLAY
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time) if prev_time != 0 else 0
    prev_time = curr_time

    cv2.putText(frame, f"FPS: {int(fps)}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

    # Window title
    cv2.imshow("AI Worker Safety Monitoring System", frame)

    if cv2.waitKey(1) == 27:  # press ESC to exit
        break

cap.release()
cv2.destroyAllWindows()