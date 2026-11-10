import base64
import io
import json
import os
import random
import time
from queue import Empty, Queue
from threading import Lock, Thread

import cats

fernet = None

COMMON_WORDS_SET = set(cats.lines_from_file("data/common_words.txt"))
COMMON_CAPTCHA_WORDS = tuple(
    word for word in COMMON_WORDS_SET if len(word) < 10
)
CAPTCHA_QUEUE_LEN = 40
CAPTCHA_LENGTH = 10
CAPTCHA_WORD_LEN = 10
CAPABILITY_TTL = 6 * 60 * 60

captcha_queue = Queue(maxsize=CAPTCHA_QUEUE_LEN)
producer_lock = Lock()
producer_running = False


class TokenError(ValueError):
    pass


def get_fernet():
    global fernet
    if fernet is None:
        from cryptography.fernet import Fernet

        key = os.environ.get("FERNET_KEY")
        if not key and os.environ.get("CATS_REQUIRE_FERNET_KEY") == "1":
            raise RuntimeError("FERNET_KEY is required for the Cats server.")
        fernet = Fernet(key.encode() if key else Fernet.generate_key())
    return fernet


def encode_token(payload):
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return get_fernet().encrypt(raw).decode()


def decode_token(token):
    from cryptography.fernet import InvalidToken

    if not token:
        raise TokenError("Missing verification token.")
    try:
        return json.loads(get_fernet().decrypt(token.encode()).decode())
    except (AttributeError, InvalidToken, TypeError, ValueError) as error:
        raise TokenError("Invalid or expired verification token.") from error


def create_capability(kind, subject, owner=None):
    now = time.time()
    payload = {
        "kind": "{}_capability".format(kind),
        "subject": str(subject),
        "issuedAt": now,
        "expiresAt": now + CAPABILITY_TTL,
    }
    if owner is not None:
        payload["owner"] = str(owner)
    return encode_token(payload)


def verify_capability(kind, subject, token, owner=None):
    try:
        payload = decode_token(token)
    except TokenError:
        return False
    valid = (
        payload.get("kind") == "{}_capability".format(kind)
        and payload.get("subject") == str(subject)
        and payload.get("expiresAt", 0) >= time.time()
    )
    if owner is not None:
        valid = valid and payload.get("owner") == str(owner)
    return valid


def generate_captcha():
    from PIL import Image, ImageDraw, ImageFont

    word = random.choice(COMMON_CAPTCHA_WORDS)
    font = ImageFont.truetype(
        os.path.join(os.path.dirname(__file__), "FreeMono.ttf"),
        32,
    )
    scratch = Image.new("RGB", (1, 1))
    bounds = ImageDraw.Draw(scratch).textbbox((0, 0), word, font=font)
    width = bounds[2] - bounds[0] + 40
    height = bounds[3] - bounds[1] + 24
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for _ in range(4):
        draw.line(
            (
                random.randrange(width),
                random.randrange(height),
                random.randrange(width),
                random.randrange(height),
            ),
            fill=(180, 180, 180),
            width=1,
        )
    draw.text((20, 8 - bounds[1]), word, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode()
    return "data:image/png;base64," + image_b64, word


def populate_captcha_queue():
    global producer_running
    try:
        while not captcha_queue.full():
            captcha_queue.put(generate_captcha())
    finally:
        with producer_lock:
            producer_running = False


def start_captcha_producer():
    global producer_running
    with producer_lock:
        if producer_running:
            return
        producer_running = True
        Thread(target=populate_captcha_queue, daemon=True).start()


def get_captcha_urls(num_words=CAPTCHA_LENGTH):
    start_captcha_producer()
    images, words = [], []
    for _ in range(num_words):
        try:
            image, word = captcha_queue.get(timeout=15)
        except Empty as error:
            raise RuntimeError("Captcha generation timed out.") from error
        images.append(image)
        words.append(word)
    start_captcha_producer()
    return images, words
