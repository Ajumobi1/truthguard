import os
import tempfile
import logging
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import numpy as np
import cv2
import sqlite3
import re
from datetime import datetime
from detectors.text_detector import score_text
from detectors.humanizer import humanize
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
import stripe

# optional imports for future features
# from flask_login import LoginManager, login_required, login_user, logout_user, current_user
# import stripe

# configuration
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "uploads")
MODEL_DIR = os.environ.get("MODEL_DIR", "models")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "mp4", "mov", "avi", "webm"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_DIR
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB max upload
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

# ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# simple sqlite usage DB to track per-IP daily word usage for free tier
DB_PATH = os.path.join(MODEL_DIR, 'usage.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS usage (
        ip TEXT,
        date TEXT,
        words_used INTEGER,
        PRIMARY KEY (ip, date)
    )''')
    # users table for basic auth and subscriptions
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password_hash TEXT,
        is_premium INTEGER DEFAULT 0,
        stripe_customer_id TEXT
    )''')
    conn.commit()
    conn.close()


init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("truthguard")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class ImageDetector:
    """Wrapper around an image-based fake detector model."""

    def __init__(self, model_path: str | None = None):
        # TODO: replace placeholder with real model loading code
        # e.g. self.model = torch.load(model_path)
        self.model = None
        logger.info("ImageDetector initialized (placeholder)")

    def detect(self, img_path: str) -> tuple[str, float]:
        # placeholder logic: randomly say AI or Real
        # model inference should return a confidence score in [0,1]
        score = np.random.rand()
        label = "AI-Generated" if score > 0.5 else "Real"
        return label, float(score * 100)


class VideoDetector:
    """Wrapper around a video/deepfake detector model."""

    def __init__(self, model_path: str | None = None):
        # TODO: load your deepfake detection network here
        self.model = None
        logger.info("VideoDetector initialized (placeholder)")

    def detect(self, video_path: str) -> tuple[str, float]:
        cap = cv2.VideoCapture(video_path)
        frames = []
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (256, 256))
            frames.append(frame)
        cap.release()
        if not frames:
            return "Error", 0.0

        # fake inference: average uniform noise
        scores = np.random.uniform(0.4, 0.6, size=len(frames))
        avg = scores.mean()
        label = "Deepfake" if avg > 0.5 else "Real"
        return label, float(avg * 100)


# instantiate detectors once (could be lazy-loaded)
image_detector = ImageDetector()
video_detector = VideoDetector()
IMAGE_TEXT_MAX_FREE = 1000  # free words/day per IP


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(temp_path)

    try:
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            result, score = image_detector.detect(temp_path)
        else:
            result, score = video_detector.detect(temp_path)
    except Exception as exc:
        logger.exception("detection failed")
        os.remove(temp_path)
        return jsonify({'error': 'detection error'}), 500

    os.remove(temp_path)
    return jsonify({'result': result, 'confidence': f"{score:.2f}%"})


# simple health check / API endpoint for programmatic access
@app.route('/api/detect', methods=['POST'])
def api_detect():
    return detect()


def _client_ip():
    # respects typical proxy header if present
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'


def get_words_used(ip: str, date_str: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT words_used FROM usage WHERE ip=? AND date=?', (ip, date_str))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def add_words_used(ip: str, date_str: str, words: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT words_used FROM usage WHERE ip=? AND date=?', (ip, date_str))
    row = cur.fetchone()
    if row:
        cur.execute('UPDATE usage SET words_used=? WHERE ip=? AND date=?', (row[0] + words, ip, date_str))
    else:
        cur.execute('INSERT INTO usage (ip, date, words_used) VALUES (?, ?, ?)', (ip, date_str, words))
    conn.commit()
    conn.close()


def create_user(email: str, password: str) -> int:
    pw = generate_password_hash(password)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, pw))
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_email(email: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, email, password_hash, is_premium, stripe_customer_id FROM users WHERE email=?', (email,))
    row = cur.fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, email, password_hash, is_premium, stripe_customer_id FROM users WHERE id=?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_user_premium(user_id: int, value: bool = True):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET is_premium=? WHERE id=?', (1 if value else 0, user_id))
    conn.commit()
    conn.close()


@app.route('/text_detect', methods=['POST'])
def text_detect():
    data = request.form.get('text') or request.json and request.json.get('text')
    if not data or not data.strip():
        return jsonify({'error': 'No text provided'}), 400
    label, score = score_text(data)
    return jsonify({'result': label, 'confidence': f"{score:.2f}%"})


@app.route('/humanize', methods=['POST'])
def text_humanize():
    data = request.form.get('text') or request.json and request.json.get('text')
    if not data or not data.strip():
        return jsonify({'error': 'No text provided'}), 400
    # check if user is logged in and premium
    user = None
    if session.get('user_id'):
        user = get_user_by_id(session['user_id'])

    words_in = len(re.findall(r"\w+", data))

    if user and user[3]:
        # premium user: allow full humanize
        humanized, used = humanize(data, max_words=words_in)
        return jsonify({'humanized': humanized, 'words_used': used, 'words_remaining': 'unlimited'})

    # non-premium: fall back to IP-based free quota
    ip = _client_ip()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    current_used = get_words_used(ip, today)
    if current_used >= IMAGE_TEXT_MAX_FREE:
        return jsonify({'error': 'Free daily limit reached. Upgrade to continue.'}), 402
    allowed = min(IMAGE_TEXT_MAX_FREE - current_used, words_in)

    # humanize only up to allowed words for free tier
    humanized, used = humanize(data, max_words=allowed)
    add_words_used(ip, today, used)
    remaining = IMAGE_TEXT_MAX_FREE - get_words_used(ip, today)
    return jsonify({'humanized': humanized, 'words_used': used, 'words_remaining': remaining})


if __name__ == '__main__':
    # development server
    app.run(host='0.0.0.0', port=5000, debug=True)


@app.route('/signup', methods=['POST'])
def signup():
    payload = request.form or request.json or {}
    email = payload.get('email')
    password = payload.get('password')
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400
    existing = get_user_by_email(email)
    if existing:
        return jsonify({'error': 'user exists'}), 400
    uid = create_user(email, password)
    session['user_id'] = uid
    return jsonify({'id': uid, 'email': email})


@app.route('/login', methods=['POST'])
def login():
    payload = request.form or request.json or {}
    email = payload.get('email')
    password = payload.get('password')
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400
    row = get_user_by_email(email)
    if not row or not check_password_hash(row[2], password):
        return jsonify({'error': 'invalid credentials'}), 401
    session['user_id'] = row[0]
    return jsonify({'id': row[0], 'email': row[1]})


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.route('/create_checkout_session', methods=['POST'])
def create_checkout_session():
    # creates a Stripe checkout session for upgrading to premium
    stripe_key = os.environ.get('STRIPE_API_KEY')
    price_id = os.environ.get('STRIPE_PRICE_ID')
    if not stripe_key or not price_id:
        return jsonify({'error': 'payment not configured'}), 501
    stripe.api_key = stripe_key
    domain = request.host_url.rstrip('/')
    try:
        session_obj = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=domain + '/upgrade_success',
            cancel_url=domain + '/upgrade_cancel',
        )
        return jsonify({'url': session_obj.url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

