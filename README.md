# Employee Drowsiness Detector

Watches a webcam feed with MediaPipe Face Mesh. If the employee's eyes stay
closed for a set number of seconds, it's treated as "sleeping" and an email
alert is sent to the boss.

## 1. Install

```bash
pip install -r requirements.txt
```

## 2. Configure

Open `drowsiness_alert.py` and fill in the CONFIG section near the top,
**or** set these as environment variables instead (recommended, so you don't
put your password in the code):

| Variable          | Meaning                                   |
|-------------------|--------------------------------------------|
| `EMPLOYEE_NAME`   | Name shown in the alert email              |
| `SENDER_EMAIL`    | The email account the alert is sent *from* |
| `SENDER_PASSWORD` | App password for that account              |
| `BOSS_EMAIL`      | The boss's email address (alert goes *to*) |
| `SMTP_SERVER`     | Defaults to Gmail's (`smtp.gmail.com`)     |
| `SMTP_PORT`       | Defaults to `587`                          |

### If using Gmail
Gmail blocks your normal password for this. Instead:
1. Turn on 2-Step Verification on the sender's Google account.
2. Create an "App Password" at https://myaccount.google.com/apppasswords
3. Use that 16-character app password as `SENDER_PASSWORD`.

Example (Mac/Linux):
```bash
export EMPLOYEE_NAME="Rahul"
export SENDER_EMAIL="monitor.bot@gmail.com"
export SENDER_PASSWORD="abcd efgh ijkl mnop"
export BOSS_EMAIL="boss@company.com"
python drowsiness_alert.py
```

Example (Windows PowerShell):
```powershell
$env:EMPLOYEE_NAME="Rahul"
$env:SENDER_EMAIL="monitor.bot@gmail.com"
$env:SENDER_PASSWORD="abcd efgh ijkl mnop"
$env:BOSS_EMAIL="boss@company.com"
python drowsiness_alert.py
```

## 3. Run

```bash
python drowsiness_alert.py
```

A window opens showing the webcam feed with a live status ("Awake",
"Eyes closed...", "SLEEPING"). Press **q** to quit.

## Tuning

These constants are at the top of `drowsiness_alert.py`:

- `EYES_CLOSED_SECONDS` — how long eyes must stay shut before it counts as
  sleeping (default: 3 seconds). Raise this if short blinks trigger false
  alerts.
- `EAR_THRESHOLD` — how closed an eye must be to count as "closed"
  (default: 0.21). Lower = stricter/harder to trigger.
- `ALERT_COOLDOWN_SECONDS` — minimum gap between two alert emails for the
  same person (default: 300s / 5 min), so it doesn't spam the boss.

## Notes / Next steps

- This uses **email** as the "normal message" channel. If you'd rather send
  a Telegram message, Slack message, or SMS, only the `send_alert_email()`
  function needs to change — everything else (detection, timing) stays the
  same. Happy to add one of those instead if you'd like.
- For **multiple employees/cameras**, this would need to run one instance
  per camera (or be extended to loop over multiple video sources) — let me
  know if you want that version.
- Camera index `0` is used by default (`cv2.VideoCapture(0)`) — change it if
  you have multiple cameras.
