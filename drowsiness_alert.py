"""
Employee Drowsiness Detector
-----------------------------
Watches a webcam feed. If the employee's eyes stay closed for longer than
EYES_CLOSED_SECONDS, the app treats them as "sleeping" and sends an email
alert to the boss. A cooldown prevents spamming repeated alerts.

Run:
    python drowsiness_alert.py

Press 'q' to quit the video window.

Setup:
    1. pip install -r requirements.txt
    2. Fill in the CONFIG section below (or set the same names as
       environment variables instead of hardcoding them).
    3. If using Gmail, create an "App Password" (not your normal password):
       https://myaccount.google.com/apppasswords
"""

import os
import time
import smtplib
from email.mime.text import MIMEText

import cv2
import mediapipe as mp
import numpy as np

# ======================= CONFIG =======================
EMPLOYEE_NAME = os.environ.get("EMPLOYEE_NAME", "Employee")

# How long (seconds) eyes must stay closed before we call it "sleeping"
EYES_CLOSED_SECONDS = 3.0

# EAR (Eye Aspect Ratio) below this = eyes considered closed.
# Lower = more strict (harder to trigger). Typical range: 0.18 - 0.25
EAR_THRESHOLD = 0.21

# Don't send another email more often than this (seconds), even if the
# person keeps sleeping / wakes and sleeps again.
ALERT_COOLDOWN_SECONDS = 300  # 5 minutes

# --- Email settings ---
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "sunilpawar10p@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "vbfg rzdf txyl bwfc")
BOSS_EMAIL = os.environ.get("BOSS_EMAIL", "sunilpawar914861@gmail.com")
# ========================================================


# MediaPipe eye landmark indices (Face Mesh, 468-point model)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def eye_aspect_ratio(landmarks, eye_indices, image_w, image_h):
    """Compute EAR for one eye from 6 landmark points."""
    pts = []
    for idx in eye_indices:
        lm = landmarks[idx]
        pts.append((lm.x * image_w, lm.y * image_h))
    pts = np.array(pts)

    # vertical distances
    v1 = np.linalg.norm(pts[1] - pts[5])
    v2 = np.linalg.norm(pts[2] - pts[4])
    # horizontal distance
    h = np.linalg.norm(pts[0] - pts[3])

    if h == 0:
        return 0.0
    return (v1 + v2) / (2.0 * h)


def send_alert_email(employee_name):
    """Send a plain 'employee is sleeping' notification to the boss."""
    subject = f"Alert: {employee_name} appears to be asleep"
    body = (
        f"{employee_name} has had their eyes closed for over "
        f"{EYES_CLOSED_SECONDS:.0f} seconds and may be asleep at their desk.\n\n"
        f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"(Automated message from the drowsiness monitor.)"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = BOSS_EMAIL

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, [BOSS_EMAIL], msg.as_string())
        print(f"[ALERT SENT] Boss notified about {employee_name}.")
        return True
    except Exception as e:
        print(f"[ERROR] Could not send email: {e}")
        return False


def check_config():
    missing = [
        name for name, val in [
            ("SENDER_EMAIL", SENDER_EMAIL),
            ("SENDER_PASSWORD", SENDER_PASSWORD),
            ("BOSS_EMAIL", BOSS_EMAIL),
        ] if not val
    ]
    if missing:
        print(
            "[ERROR] Missing required environment variable(s): "
            + ", ".join(missing)
            + "\nSet them before running, e.g.:\n"
            "  export SENDER_EMAIL=\"you@gmail.com\"\n"
            "  export SENDER_PASSWORD=\"your-app-password\"\n"
            "  export BOSS_EMAIL=\"boss@example.com\"\n"
            "See README.md for details."
        )
        raise SystemExit(1)


def main():
    check_config()

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    eyes_closed_start = None
    last_alert_time = 0.0
    status_text = "Watching..."
    status_color = (0, 255, 0)

    print("Starting drowsiness monitor. Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            left_ear = eye_aspect_ratio(landmarks, LEFT_EYE, w, h)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE, w, h)
            ear = (left_ear + right_ear) / 2.0

            eyes_closed = ear < EAR_THRESHOLD

            if eyes_closed:
                if eyes_closed_start is None:
                    eyes_closed_start = time.time()
                closed_duration = time.time() - eyes_closed_start

                if closed_duration >= EYES_CLOSED_SECONDS:
                    status_text = f"SLEEPING ({closed_duration:.1f}s)"
                    status_color = (0, 0, 255)

                    now = time.time()
                    if now - last_alert_time >= ALERT_COOLDOWN_SECONDS:
                        send_alert_email(EMPLOYEE_NAME)
                        last_alert_time = now
                else:
                    status_text = f"Eyes closed ({closed_duration:.1f}s)"
                    status_color = (0, 165, 255)
            else:
                eyes_closed_start = None
                status_text = "Awake"
                status_color = (0, 255, 0)

            cv2.putText(
                
                frame, f"EAR: {ear:.2f}", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2,
            )
        else:
            eyes_closed_start = None
            status_text = "No face detected"
            status_color = (128, 128, 128)

        cv2.putText(
            frame, status_text, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, status_color, 2,
        )

        cv2.imshow("Drowsiness Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    face_mesh.close()


if __name__ == "__main__":
    main()
