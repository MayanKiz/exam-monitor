# MAYANK Exam Monitor

A local webcam proctoring demo with face presence and landmark tracking, head-pose/gaze indicators, multi-face checks, phone-object detection, event snapshots, and optional Telegram or administrator-email alerts.

## Quick start (three commands)

Clone the repository, enter the project folder, and run setup. The script creates a virtual environment, installs dependencies, copies the sample settings file if needed, then starts the application.

```bash
git clone https://github.com/MayanKiz/exam-monitor.git
cd exam-monitor
bash setup.sh
```

On Windows, use the same `git clone` and `cd` commands in PowerShell, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

The first run downloads the face-landmarker model if needed and a small YOLOv4-tiny COCO model for phone detection (~23 MB). Allow network access for that one-time download. Later, start the app with `./run.sh` on macOS/Linux or `.\run.ps1` in PowerShell. Press `q` or `Esc` to exit, and `c` to recalibrate.

## What it does

- Finds faces and displays a face box plus a dense landmark-dot/contour overlay.
- Estimates head pose and gaze direction after a short calibration.
- Detects multiple faces, face absence, sustained looking-away, and optional unusual movement.
- Detects the COCO `cell phone` object class; detected devices are boxed and labeled in the camera preview.
- Captures an annotated JPEG snapshot when a configured alert fires.
- Writes alert events and snapshot paths to a local SQLite database (`events.sqlite3`).
- Optionally sends Telegram notifications and/or SMTP email to an administrator, with the alert snapshot attached where available.
- Displays a large MAYANK splash briefly at startup.

The database and snapshots stay on the computer by default. Telegram/email data and snapshot attachments leave the computer only when those integrations are configured and enabled. Face/behavior signals are heuristics, phone detection can miss or misclassify objects, and lighting/camera quality can cause false positives. This is an assistive flagging demo, not proof of misconduct or a substitute for human review. Use with clear notice and consent.

## Optional alerts

The setup script creates `.env` from `.env.example`. Leave the placeholders unchanged to run with local logging only.

For email, configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `ALERT_FROM_EMAIL`, and `ADMIN_EMAIL` in `.env`. Use an SMTP app password. `SMTP_STARTTLS=true` is the default; for an SSL-only provider, set `SMTP_USE_SSL=true` and `SMTP_STARTTLS=false`. Emails are sent only for detected alert events and describe them as possible policy events; the app does not claim to determine conclusively whether someone cheated.

Telegram can also be enabled with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. The app asks before enabling Telegram if credentials are present. Email notifications are sent automatically only when complete SMTP/admin settings are provided.

## Useful settings

```env
PHONE_DETECTION_ENABLED=true
PHONE_CONFIDENCE=0.35
PHONE_CONFIRM_SECONDS=0.35
CAMERA_INDEX=0
FACE_BACKEND=auto
SHOW_WINDOW=true
ALERT_COOLDOWN_SECONDS=5
LOOK_AWAY_SECONDS=2
DATABASE_PATH=events.sqlite3
```

Set `PHONE_DETECTION_ENABLED=false` to turn off object detection, or change `PHONE_CONFIDENCE` (0–1) to tune its sensitivity. Configure camera and gaze thresholds in `.env`; do not edit source code for routine setup. Use Python 3.9–3.12 and a webcam. A GUI/display is needed for the live preview; terminal-only mode is available with `python main.py --no-window`.

## Data and troubleshooting

- Alert images are saved to `snapshots/`; event records are stored in `events.sqlite3`.
- Both are local by default. `.env`, snapshots, database files, virtual environments, and downloaded model weights are excluded from version control.
- If the webcam cannot open, close other camera apps or set `CAMERA_INDEX=1` in `.env`.
- If face tracking is unavailable, try `python main.py --backend tasks` or `python main.py --backend haar` (Haar has no landmarks).
- If phone detection cannot download/load its model, face/gaze monitoring continues and a warning is shown. Check network access and retry.
- For a headless run: `python main.py --no-window`.

## License

MIT. See `LICENSE`.
