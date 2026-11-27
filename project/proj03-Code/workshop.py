"""Local copies of workshop levels, plus a client for the workshop server."""

import base64
import hashlib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request

import level


HERE = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(HERE, "downloads")

REMOTE_URL = os.environ.get("ANTS_WORKSHOP_URL", "https://sicp.pascal-lab.net/ants").rstrip("/")
REMOTE_TIMEOUT = 8.0
# Cloudflare answers 403 to the default Python-urllib agent
REMOTE_UA = "NJU-SICP-Ants/2026"

# the judge's own login page for local apps; the callback is fixed on that side
OJ_WEB = os.environ.get("ANTS_OJ_WEB", "https://sicp.pascal-lab.net/oj/web").rstrip("/")
LOGIN_PORT = 31415

MAX_RECORD_BYTES = 256 * 1024
HEX = set("0123456789abcdef")


class WorkshopError(Exception):
    """A refusal the api layer turns into a response."""

    def __init__(self, status, reason, message):
        super().__init__(message)
        self.status = status
        self.reason = reason


def download_root():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    return DOWNLOAD_DIR


def record_path(level_id):
    # the id doubles as a filename, so only hex is allowed through
    if not level_id or not set(level_id) <= HEX:
        raise WorkshopError(404, "not_found", "no such level")
    return os.path.join(download_root(), level_id + ".json")


def read_record(level_id):
    path = record_path(level_id)
    if not os.path.exists(path):
        raise WorkshopError(404, "not_found", "no such level")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        raise WorkshopError(500, "server_error", "the stored level is unreadable")


def write_record(record):
    path = record_path(record.get("id"))
    body = json.dumps(record, ensure_ascii=False)
    if len(body.encode("utf-8")) > MAX_RECORD_BYTES:
        raise WorkshopError(413, "too_large", "the level record is too large")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(body)


def summarise(record):
    """The shape both lists use, without the full board."""
    plain = record.get("level") or {}
    waves = plain.get("waves") or []
    dimensions = plain.get("dimensions") or [0, 0]
    return {
        "id": record.get("id") or "",
        "name": record.get("name") or "",
        "userId": record.get("userId") or "",
        "authorName": record.get("authorName") or "",
        "description": record.get("description") or "",
        "createdAt": record.get("createdAt") or 0,
        "rows": dimensions[0],
        "cols": dimensions[1],
        "waves": len(waves),
        "bees": sum(int(wave.get("count") or 0) for wave in waves),
    }


def list_downloads():
    summaries = []
    for name in os.listdir(download_root()):
        if not name.endswith(".json"):
            continue
        try:
            summaries.append(summarise(read_record(name[:-len(".json")])))
        except WorkshopError:
            continue
    summaries.sort(key=lambda item: item["createdAt"], reverse=True)
    return summaries


def get_download(level_id):
    return read_record(level_id)


def save_download(record):
    """Store a record as it came from the server, id and all."""
    if not isinstance(record, dict) or not record.get("id"):
        raise WorkshopError(400, "bad_request", "the record has no id")
    write_record(record)
    return summarise(record)


def delete_download(level_id):
    path = record_path(level_id)
    if not os.path.exists(path):
        raise WorkshopError(404, "not_found", "no such level")
    os.remove(path)


def load_level(level_id):
    """The LevelData behind a downloaded record."""
    return level.LevelData.from_plain(read_record(level_id)["level"])


# ---------------------------------------------------------------------------
# the workshop server
# ---------------------------------------------------------------------------

def remote_configured():
    return bool(REMOTE_URL)


def call_remote(method, path, body=None, token=None):
    if not REMOTE_URL:
        raise WorkshopError(503, "remote_unavailable", "no workshop server configured")

    headers = {"Accept": "application/json", "User-Agent": REMOTE_UA}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token

    request = urllib.request.Request(
        REMOTE_URL + path, data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=REMOTE_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            payload = {}
        raise WorkshopError(
            error.code,
            payload.get("reason") or "remote_error",
            payload.get("error") or "the workshop server refused the request",
        )
    except (urllib.error.URLError, OSError, ValueError):
        raise WorkshopError(503, "remote_unavailable", "the workshop server is unreachable")


def remote_levels(title="", author="", description="", level_id="", exact="",
                  owner="", sort="", offset=0, limit=0, token=""):
    """One page of the catalogue: the rows and how many matched in total.

    Leaving limit at 0 asks for everything, which the staff console relies on.
    A token is optional; with one the rows say whether that account liked them.
    """
    params = {"title": title, "author": author, "description": description,
              "id": level_id, "exact": exact, "owner": owner, "sort": sort}
    params = {key: value for key, value in params.items() if value}
    if limit:
        params["limit"] = str(limit)
        if offset:
            params["offset"] = str(offset)
    data = call_remote("GET", "/levels?" + urllib.parse.urlencode(params), token=token)
    return data.get("levels") or [], data.get("total") or 0


def remote_list():
    return remote_levels()[0]


def check_level_id(level_id):
    if not level_id or not set(level_id) <= HEX:
        raise WorkshopError(400, "bad_request", "bad level id")


def remote_get(level_id):
    check_level_id(level_id)
    return call_remote("GET", "/levels/" + level_id).get("level")


def download(level_id):
    """Pull a level from the server and keep a local copy."""
    record = remote_get(level_id)
    level.LevelData.from_plain(record["level"])  # refuse anything that cannot be built
    return save_download(record)


def remote_publish(body, token):
    return call_remote("POST", "/levels", body=body, token=token).get("level")


def remote_delete(level_id, token):
    check_level_id(level_id)
    call_remote("DELETE", "/levels/" + level_id, token=token)


def remote_like(level_id, token, liked=True):
    """One vote per account; the server owns the count, not the caller."""
    check_level_id(level_id)
    method = "POST" if liked else "DELETE"
    return call_remote(method, "/levels/" + level_id + "/like", token=token).get("level")


# ---------------------------------------------------------------------------
# the online judge
# ---------------------------------------------------------------------------

def oj_login_url():
    return OJ_WEB + "/auth/cats" if OJ_WEB else ""


def pkce_pair():
    """A verifier, its S256 challenge, and a state, all URL safe."""
    verifier = secrets.token_urlsafe(48)
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge, secrets.token_urlsafe(24)


def login_url(challenge, state):
    # audience names a role, not an app, so we sign in as the student we are
    query = urllib.parse.urlencode({
        "audience": "player",
        "callback": "http://localhost:%d/" % LOGIN_PORT,
        "challenge": challenge,
        "state": state,
    })
    return oj_login_url() + "?" + query


def remote_login(code, verifier, state):
    """Hand the code to the workshop server, which redeems it with the judge."""
    return call_remote("POST", "/auth/session", body={
        "code": code,
        "verifier": verifier,
        "state": state,
    })


def remote_logout(token):
    """Best effort: the local copy is dropped either way."""
    if not token:
        return
    try:
        call_remote("DELETE", "/auth/session", token=token)
    except WorkshopError:
        pass


def remote_session(token):
    """Ask the workshop server whether this token is still good."""
    return call_remote("GET", "/auth/session", token=token)
