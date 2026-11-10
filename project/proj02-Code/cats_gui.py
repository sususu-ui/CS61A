"""Web server for the typing GUI."""

import base64
import os
import random
import string
import urllib.parse

import cats
from gui_files.implementation_checks import (
    implementation_status as current_implementation_status,
    require_phase1,
)
from gui_files.common_server import (
    LocalResponse,
    RemoteServiceError,
    Server,
    cookie_header,
    get_default_server,
    route,
    sendto,
    session_cookie,
    start,
)
from multiplayer import multiplayer

PORT = 31415
DEFAULT_SERVER = "https://sicp.pascal-lab.net/cats"
GUI_FOLDER = "gui_files/"
PARAGRAPH_PATH = "./data/sample_paragraphs.txt"
WORDS_LIST = cats.lines_from_file("data/words.txt")
WORDS_SET = set(WORDS_LIST)
LETTER_SETS = [(w, set(w)) for w in WORDS_LIST]
SIMILARITY_LIMIT = 2


def load_paragraph(topics=None):
    paragraphs = cats.lines_from_file(PARAGRAPH_PATH)
    random.shuffle(paragraphs)
    select = cats.about(topics) if topics else lambda x: True
    paragraph = cats.choose(paragraphs, select, 0)
    if not isinstance(paragraph, str) or not paragraph.strip():
        return None
    return paragraph


@route
def request_paragraph(topics=None):
    """Return a random paragraph."""
    paragraph = load_paragraph(topics)
    if paragraph is None:
        raise ValueError("No paragraphs match those topics.")
    return paragraph


@route
def analyze(prompted_text, typed_text, start_time, end_time):
    """Return [wpm, accuracy]."""
    return {
        "wpm": cats.wpm(typed_text, end_time - start_time),
        "accuracy": cats.accuracy(typed_text, prompted_text),
    }


def similar(w, v, n):
    """Whether W intersect V contains at least |W|-N and |V|-N elements."""
    intersect = len(w.intersection(v))
    return intersect >= len(w) - n and intersect >= len(v) - n


@route
def autocorrect(word=""):
    """Call autocorrect using the best score function available."""
    raw_word = word
    word = cats.lower(cats.remove_punctuation(raw_word))
    if word in WORDS_SET or word == "":
        return raw_word

    # Heuristically choose candidate words to score.
    letters = set(word)
    candidates = [w for w, s in LETTER_SETS if similar(s, letters, SIMILARITY_LIMIT)]

    # Try various diff functions until one doesn't raise an exception.
    for fn in [cats.final_diff, cats.minimum_mewtations, cats.sphinx_fixes]:
        try:
            guess = cats.autocorrect(word, candidates, fn, SIMILARITY_LIMIT)
            return reformat(guess, raw_word)
        except BaseException:
            pass

    return raw_word


def reformat(word, raw_word):
    """Reformat WORD to match the capitalization and punctuation of RAW_WORD."""
    # handle capitalization
    if raw_word != "" and raw_word[0].isupper():
        word = word.capitalize()

    # find the boundaries of the raw word
    first = 0
    while first < len(raw_word) and raw_word[first] in string.punctuation:
        first += 1
    last = len(raw_word) - 1
    while last > first and raw_word[last] in string.punctuation:
        last -= 1

    # add wrapping punctuation to the word
    if raw_word != word:
        word = raw_word[:first] + word
        word = word + raw_word[last + 1 :]

    return word


###############
# Multiplayer #
###############


@route
def implementation_status():
    """Return which later Cats phases the current cats.py can support."""
    return current_implementation_status()


@route
def request_id():
    if not cats.enable_multiplayer:
        return
    return Server.provide_id()


@route
def auth_start(challenge, state):
    if not isinstance(challenge, str) or not isinstance(state, str):
        raise ValueError("Invalid login request.")
    callback = "http://localhost:{}/".format(PORT)
    return {
        "loginUrl": get_default_server()
        + "/login?"
        + urllib.parse.urlencode(
            {"challenge": challenge, "state": state, "callback": callback}
        )
    }


def public_identity(identity):
    if not isinstance(identity, dict):
        raise ValueError("The course server returned an invalid login session.")
    user_id = identity.get("userId")
    username = identity.get("username")
    if not user_id or not username:
        raise ValueError("The course server returned an invalid login session.")
    return {
        "userId": str(user_id),
        "username": str(username),
        "fullName": str(identity.get("fullName") or username),
    }


@route
def auth_complete(code, verifier, state=None):
    callback = "http://localhost:{}/".format(PORT)
    payload = {"code": code, "verifier": verifier, "callback": callback}
    if state is not None:
        payload["state"] = state
    result = Server.redeem_login(**payload)
    if not isinstance(result, dict) or not result.get("session"):
        raise ValueError("The course server returned an invalid login session.")
    return LocalResponse(
        public_identity(result.get("identity")),
        headers={"Set-Cookie": cookie_header(result["session"])},
    )


@route
def auth_status():
    return Server.session_info()


@route
def auth_logout():
    if session_cookie():
        try:
            Server.logout()
        except RemoteServiceError:
            pass
    return LocalResponse(
        {"success": True},
        headers={"Set-Cookie": cookie_header()},
    )


@route
def report_progress(id, typed, prompt, player_token=None):
    """Report progress to the multiplayer server and also return it."""
    typed = typed.split()  # A list of word strings
    prompt = prompt.split()  # A list of word strings

    def upload(data):
        return Server.set_progress(
            id=data["id"],
            progress=data["progress"],
            player_token=player_token,
        )

    return cats.report_progress(typed, prompt, id, upload)


@route
def fastest_words(prompt, targets, id, player_token=None):
    """Return a list of word_speed values describing the match."""
    words = prompt.split()
    progress = Server.request_all_progress(
        id=id,
        targets=targets,
        player_token=player_token,
    )
    start_times = [p[0][1] for p in progress]
    times_per_player = [[p[1] - s for p in ps] for s, ps in zip(start_times, progress)]
    match = cats.time_per_word(words, times_per_player)
    return cats.fastest_words(match)


multiplayer_state = multiplayer.create_multiplayer_server()

###############
# Favicons #
###############


@route
@route("favicon.ico")
def favicon():
    favicon_folder = "favicons"
    favicons = os.listdir(favicon_folder)
    path = os.path.join(favicon_folder, random.choice(favicons))
    with open(path, "rb") as f:
        data = f.read()
    image_b64 = base64.b64encode(data).decode("utf-8")
    return "data:image/png;base64," + image_b64


if __name__ == "__main__" or os.environ.get("ENV") == "prod":
    require_phase1()
    app = start(PORT, DEFAULT_SERVER, GUI_FOLDER, multiplayer.db_init)
