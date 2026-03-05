# TruthGuard

TruthGuard is a lightweight Flask web application for detecting AI-generated images and videos. It serves as a prototype for an "AI-generated media detector" with future plans for user accounts, batch processing, and an API.

## Features

- Upload or provide URLs for images (JPEG/PNG) and short videos (MP4/MOV/AVI/WebM).
- Returns a confidence score and classification (Real vs AI/Deepfake).
- Simple REST endpoint (`/api/detect`) for programmatic use.
- Designed to be deployed on platforms like Railway, Heroku, or any container-based host.

## Getting started

### Requirements

- Python 3.10+
- `git` (to clone model repositories)

### Setup

```bash
# clone repo and enter directory
git clone <your-repo-url> truthguard
cd truthguard

# create virtual environment
python -m venv venv
. venv/bin/activate  # or \"venv\Scripts\activate\" on Windows

# install dependencies
pip install -r requirements.txt
```

### Configuration

Configuration is driven by environment variables. You can copy `.env.example` to `.env` and adjust values.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | random | Flask secret key |
| `UPLOAD_DIR` | `uploads` | Directory for temporary uploads |
| `MODEL_DIR` | `models` | Path where detectors store weights |


### Running locally

```bash
export FLASK_APP=app.py
export FLASK_ENV=development  # enables debug
flask run
```

or simply:

```bash
python app.py
```

Open http://127.0.0.1:5000 in the browser.

### Deploying to Railway

1. Push the repo to GitHub.
2. Sign in to Railway and create a new project from GitHub.
3. Set environment variables on Railway dashboard (`SECRET_KEY`, etc.).
4. Railway will build using `requirements.txt` and run the `Procfile`.

## Extending the app

- Replace dummy detector logic with real models (see `detectors/` directory). Clone and load weights from:
  - https://github.com/ojha11/UniversalFakeDetect (image)
  - https://github.com/HaozheWu/MesoNet-PyTorch or https://github.com/siddharthksah/DeepSafe (video)
- Add `flask-login` for authentication and Stripe/Flutterwave for payments.
- Create batch endpoints and API keys for programmatic access.
- Add static assets and enhance the UI with Bootstrap or another frontend framework.

## Notes

This project is a starting point for building the **TruthGuard** product described in the conversation. It intentionally keeps detection models abstracted behind simple classes (`ImageDetector`, `VideoDetector`) to make swapping in real implementations trivial.
