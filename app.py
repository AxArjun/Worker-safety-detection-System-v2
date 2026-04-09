import streamlit as st
import cv2
from typing import Any, cast
from ultralytics import YOLO

st.title("AI Worker Safety Monitoring Dashboard")

# Load model
model = YOLO("yolov8n.pt")

# Button
if st.button("Start Monitoring"):

    st.write("Camera starting...")

    cap = cv2.VideoCapture(0)

    frame_placeholder = st.empty()

    for i in range(200):   # limited loop (IMPORTANT)
        ret, frame = cap.read()

        if not ret:
            st.error("Camera not working")
            break

        results = model(frame)

        for r in results:
            res = cast(Any, r)
            for box in res.boxes:
                cls = int(box.cls[0])
                label = model.names[cls]

                if label == "person":
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                    cv2.putText(frame, "Worker", (x1, y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                    cv2.putText(frame, "NO HELMET!", (x1, y2+20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

                    st.warning("⚠️ Safety Violation Detected!")

        frame_placeholder.image(frame, channels="BGR")

    cap.release()

else:
    st.write("Click button to start")