import argparse
import json
import mimetypes
import re
import threading
import time
import webbrowser
import os
from http.cookies import SimpleCookie
from functools import wraps
from http import HTTPStatus, server
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse, parse_qs
from urllib.request import Request, urlopen

STATIC_PATHS = {}
PATHS = {}
REMOTE_TIMEOUT = 8
REMOTE_FAILURE_LIMIT = 3
REMOTE_COOLDOWN = 5
REMOTE_FAILURES = 0
REMOTE_OPEN_UNTIL = 0
REMOTE_STATE_LOCK = threading.Lock()
MAX_REQUEST_BYTES = 1024 * 1024
REQUEST_CONTEXT = threading.local()
LOCAL_PORT = 31415

CONTENT_TYPE_LOOKUP = dict(
    html="text/html",
    css="text/css",
    js="application/javascript",
    svg="image/svg+xml",
    gif="image/gif",
    ico="image/x-icon",
)


def path_optional(decorator):
    def wrapped(func_or_path):
        if callable(func_or_path):
            return decorator("/" + func_or_path.__name__)(func_or_path)
        else:

            def actual_decorator(f):
                return decorator(func_or_path)(f)

            return actual_decorator

    return wrapped


def route(path):
    """Register a route handler."""

    if callable(path):
        return route("/" + path.__name__)(path)

    if not path.startswith("/"):
        path = "/" + path

    def wrap(f):
        if "." in path:
            STATIC_PATHS[path] = f
        else:
            PATHS[path] = f
        return f

    return wrap


class Handler(server.BaseHTTPRequestHandler):
    """HTTP handler."""

    def do_GET(self):
        try:
            parsed_url = urlparse(unquote(self.path))
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)

            if path in STATIC_PATHS:
                out = bytes(STATIC_PATHS[path](**snakify(query_params)), "utf-8")
                content_type = CONTENT_TYPE_LOOKUP.get(
                    path.rsplit(".", 1)[-1],
                    "application/octet-stream",
                )
            else:
                root = os.path.realpath(GUI_FOLDER)
                path = os.path.realpath(os.path.join(root, path.lstrip("/")))
                if os.path.commonpath([root, path]) != root:
                    raise PermissionError("Path escapes gui_files")
                if "scripts" in path and not path.endswith(".js"):
                    path += ".js"
                if path == root:
                    path = os.path.join(root, "index.html")
                with open(path, "rb") as f:
                    out = f.read()
                content_type = (
                    mimetypes.guess_type(path)[0] or "application/octet-stream"
                )
        except PermissionError:
            self.send_response(HTTPStatus.FORBIDDEN)
            self.end_headers()
        except FileNotFoundError:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
        except Exception as e:
            print(e)
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.end_headers()
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

    def do_POST(self):
        try:
            self.validate_local_request()
            REQUEST_CONTEXT.cookies = SimpleCookie(
                self.headers.get("Cookie", "")
            )
            content_length = int(self.headers["Content-Length"])
            if content_length < 0 or content_length > MAX_REQUEST_BYTES:
                raise RequestTooLarge()
            raw_data = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw_data)
            if not isinstance(data, dict):
                raise ValueError("JSON request body must be an object.")
            path = urlparse(unquote(self.path)).path
            if path not in PATHS:
                raise RouteNotFound(path)
            result = PATHS[path](**snakify(data))
        except RemoteServiceError as error:
            self.send_json(
                error.status,
                error_payload(
                    error.code,
                    str(error),
                    retryable=error.retryable,
                    retry_after=error.retry_after,
                ),
            )
        except RouteNotFound as error:
            self.send_json(
                HTTPStatus.NOT_FOUND,
                error_payload("route_not_found", str(error), retryable=False),
            )
        except RequestTooLarge as error:
            self.send_json(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                error_payload("request_too_large", str(error), retryable=False),
            )
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as error:
            self.send_json(
                HTTPStatus.BAD_REQUEST,
                error_payload("invalid_request", str(error), retryable=False),
            )
        except Exception as error:
            print(error)
            self.send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                error_payload(
                    "internal_error",
                    "The local Cats server could not process the request.",
                    retryable=False,
                ),
            )
        else:
            if isinstance(result, LocalResponse):
                self.send_json(result.status, result.data, result.headers)
            else:
                self.send_json(HTTPStatus.OK, result)
            if path == "/kill" and not IS_SERVER:
                threading.Thread(target=self.server.shutdown, daemon=True).start()
        finally:
            REQUEST_CONTEXT.cookies = SimpleCookie()

    def validate_local_request(self):
        host = self.headers.get("Host", "")
        allowed_hosts = {
            "localhost:{}".format(LOCAL_PORT),
            "127.0.0.1:{}".format(LOCAL_PORT),
        }
        if host not in allowed_hosts:
            raise ValueError("Invalid local Host header.")
        origin = self.headers.get("Origin")
        allowed_origins = {
            "http://localhost:{}".format(LOCAL_PORT),
            "http://127.0.0.1:{}".format(LOCAL_PORT),
        }
        if origin and origin not in allowed_origins:
            raise ValueError("Invalid local Origin header.")

    def send_json(self, status, data, headers=None):
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args, **kwargs):
        pass


class LocalHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class LocalResponse:
    def __init__(self, data, status=HTTPStatus.OK, headers=None):
        self.data = data
        self.status = status
        self.headers = headers or {}


def session_cookie():
    cookies = getattr(REQUEST_CONTEXT, "cookies", SimpleCookie())
    morsel = cookies.get("cats_session")
    return morsel.value if morsel else None


def cookie_header(value=None):
    if value:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{20,200}", value):
            raise ValueError("The course server returned an invalid login session.")
        return (
            "cats_session={}; HttpOnly; SameSite=Strict; Path=/; Max-Age={}"
        ).format(value, 6 * 60 * 60)
    return "cats_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"


def get_default_server():
    return DEFAULT_SERVER


class Server:
    def __getattr__(self, item):
        def f(**kwargs):
            if IS_SERVER:
                return PATHS["/" + item](**kwargs)
            else:
                return multiplayer_post(item, kwargs)

        return f


Server = Server()


class RemoteServiceError(RuntimeError):
    def __init__(
        self,
        message,
        status=HTTPStatus.SERVICE_UNAVAILABLE,
        code="remote_unavailable",
        retryable=True,
        retry_after=None,
    ):
        super().__init__(message)
        self.status = status
        self.code = code
        self.retryable = retryable
        self.retry_after = retry_after


class RouteNotFound(KeyError):
    def __str__(self):
        return "Unknown Cats route: {}".format(self.args[0])


class RequestTooLarge(ValueError):
    def __str__(self):
        return "Cats requests are limited to {} bytes.".format(MAX_REQUEST_BYTES)


def error_payload(code, message, retryable, retry_after=None):
    payload = {
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    if retry_after is not None:
        payload["retryAfter"] = retry_after
    return payload


def multiplayer_post(path, data, server_url=None):
    """Post DATA to a multiplayer server PATH and return the response."""
    global REMOTE_FAILURES, REMOTE_OPEN_UNTIL
    if not server_url:
        server_url = DEFAULT_SERVER
    now = time.monotonic()
    with REMOTE_STATE_LOCK:
        if now < REMOTE_OPEN_UNTIL:
            raise RemoteServiceError(
                "The course Cats service is temporarily paused after repeated failures.",
                retry_after=max(1, round(REMOTE_OPEN_UNTIL - now)),
            )
    data_bytes = bytes(json.dumps(data), encoding="utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "NJU-SICP-Cats/2026",
    }
    token = session_cookie()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(
        server_url + "/" + path,
        data_bytes,
        method="POST",
        headers=headers,
    )
    try:
        with urlopen(request, timeout=REMOTE_TIMEOUT) as response:
            text = response.read().decode("utf-8")
            with REMOTE_STATE_LOCK:
                REMOTE_FAILURES = 0
                REMOTE_OPEN_UNTIL = 0
            if text.strip():
                return json.loads(text)
    except HTTPError as error:
        try:
            payload = json.loads(error.read().decode())
        except (TypeError, ValueError):
            payload = {}
        finally:
            error.close()
        retry_after = payload.get("retryAfter")
        if error.code >= 500:
            with REMOTE_STATE_LOCK:
                REMOTE_FAILURES += 1
                if REMOTE_FAILURES >= REMOTE_FAILURE_LIMIT:
                    REMOTE_OPEN_UNTIL = time.monotonic() + REMOTE_COOLDOWN
                    retry_after = REMOTE_COOLDOWN
        raise RemoteServiceError(
            payload.get("message", "The course Cats service rejected the request."),
            status=error.code,
            code=payload.get(
                "code",
                "remote_unavailable"
                if error.code >= 500
                else "remote_request_rejected",
            ),
            retryable=payload.get("retryable", error.code >= 500),
            retry_after=retry_after,
        ) from error
    except Exception as e:
        with REMOTE_STATE_LOCK:
            REMOTE_FAILURES += 1
            retry_after = None
            if REMOTE_FAILURES >= REMOTE_FAILURE_LIMIT:
                REMOTE_OPEN_UNTIL = time.monotonic() + REMOTE_COOLDOWN
                retry_after = REMOTE_COOLDOWN
        raise RemoteServiceError(
            "The course Cats service is unavailable. Please try again.",
            retry_after=retry_after,
        ) from e


def multiplayer_route(path, server_path=None):
    """Convert a function that takes (data, send) into a route."""
    if not server_path:
        server_path = path

    def wrap(f):
        def send(data):
            return multiplayer_post(server_path, data)

        def routed_fn(data):
            response = f(data, send)
            return response

        route(path)(routed_fn)
        return f

    return wrap


@path_optional
def forward_to_server(path):
    def wrap(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if IS_SERVER:
                return f(*args, **kwargs)
            else:
                return multiplayer_post(path, kwargs)

        return wrapped

    return wrap


def server_only(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if IS_SERVER:
            return f(*args, **kwargs)
        else:
            raise Exception("Method not available locally!")

    return wrapped


def sendto(f):
    def wrapped(data):
        return f(**data)

    return wrapped


def start_server():
    global IS_SERVER
    IS_SERVER = True
    from flask import Flask, request, jsonify, send_from_directory, Response

    app = Flask(__name__, static_url_path="", static_folder="")
    for route, handler in PATHS.items():

        def wrapped_handler(handler=handler):
            return jsonify(handler(**snakify(request.get_json(force=True))))

        app.add_url_rule(route, handler.__name__, wrapped_handler, methods=["POST"])

    for route, handler in STATIC_PATHS.items():

        def wrapped_handler(route=route, handler=handler):
            query_params = parse_qs(request.query_string.decode())
            return Response(
                handler(**snakify(query_params)),
                mimetype=CONTENT_TYPE_LOOKUP[route.split(".")[-1]],
            )

        app.add_url_rule(
            route, handler.__name__ + route, wrapped_handler, methods=["GET"]
        )

    @app.route("/")
    def index():
        return send_from_directory("", "index.html")

    return app


def start_client(port, default_server, gui_folder, standalone):
    """Start web server."""
    global DEFAULT_SERVER, GUI_FOLDER, IS_SERVER, LOCAL_PORT
    DEFAULT_SERVER = default_server
    GUI_FOLDER = gui_folder
    IS_SERVER = False
    LOCAL_PORT = port

    httpd = LocalHTTPServer(("localhost", port), Handler)
    local_url = "http://localhost:{}".format(port)
    print("Cats is running at {}".format(local_url), flush=True)
    if not standalone:
        webbrowser.open(local_url, new=0, autoraise=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()


def snakify(data):
    out = {}
    for key, val in data.items():
        snake_key = []
        for x in key:
            if x != x.lower():
                snake_key += "_"
            snake_key += x.lower()
        out["".join(snake_key)] = val
    return out


@route("/kill")
def kill():
    return None


def start(port, default_server, gui_folder, db_init=None):
    global DEFAULT_SERVER
    DEFAULT_SERVER = default_server

    parser = argparse.ArgumentParser(description="Project GUI Server")
    parser.add_argument(
        "-s", help="Stand-alone: do not open browser", action="store_true"
    )
    parser.add_argument("-f", help="Force Flask app", action="store_true")
    args, unknown = parser.parse_known_args()

    import __main__

    if "gunicorn" not in os.environ.get("SERVER_SOFTWARE", "") and not args.f:
        request = Request(
            "http://127.0.0.1:{}/kill".format(port),
            bytes(json.dumps({}), encoding="utf-8"),
            method="POST",
        )
        try:
            urlopen(request, timeout=1)
            print("Killing existing gui process...")
            time.sleep(1)
        except (URLError, TimeoutError):
            pass

        start_client(port, default_server, gui_folder, args.s)
    else:
        if db_init:
            db_init()
        app = start_server()
        if args.f:
            app.run(port=port, threaded=False, processes=1)
        else:
            return app
