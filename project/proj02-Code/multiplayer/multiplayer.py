import time
import math
from collections import namedtuple, defaultdict
from datetime import datetime, timedelta
from random import randrange

import cats
from gui_files.common_server import route, forward_to_server, server_only
from .leaderboard_integrity import (
    create_capability,
    verify_capability,
)

MIN_PLAYERS = 2
MAX_PLAYERS = 4
QUEUE_TIMEOUT = timedelta(seconds=15)
MAX_WAIT = timedelta(seconds=5)
ABANDON_TIMEOUT = 30
GAME_TTL = 30 * 60
COMPLETED_TTL = 2 * 60

MAX_NAME_LENGTH = 90


def validate_user(user):
    if not isinstance(user, (str, int)) or not str(user):
        raise ValueError("user/id must be a non-empty string or integer")
    return str(user)


def validate_wpm(wpm):
    if (
        isinstance(wpm, bool)
        or not isinstance(wpm, (int, float))
        or not math.isfinite(wpm)
        or wpm < 0
    ):
        raise ValueError("wpm must be a finite non-negative number")
    return float(wpm)


def validate_name(name):
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    name = name.strip()
    if not name or len(name) > MAX_NAME_LENGTH:
        raise ValueError(
            "name must contain 1 to {} characters".format(MAX_NAME_LENGTH)
        )
    return name


def require_capability(kind, subject, token):
    if not verify_capability(kind, subject, token):
        raise ValueError("invalid or expired {} capability".format(kind))


def db_init():
    global connect_db
    from common.db import connect_db

    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS leaderboard (
        name varchar(128),
        user_id varchar(128),
        wpm double,
        PRIMARY KEY (`user_id`)
    );"""
        )


def create_multiplayer_server():
    State = namedtuple(
        "State",
        [
            "queue",
            "game_lookup",
            "game_data",
            "progress",
            "last_seen",
            "completed_at",
        ],
    )
    State = State({}, {}, {}, defaultdict(list), {}, {})

    def remove_game(game_id):
        game = State.game_data.pop(game_id, None)
        State.completed_at.pop(game_id, None)
        if not game:
            return
        for player in game["players"]:
            State.game_lookup.pop(player, None)
            State.progress.pop(player, None)
            State.last_seen.pop(player, None)

    def cleanup_state():
        now = time.time()
        for game_id, game in list(State.game_data.items()):
            completed = State.completed_at.get(game_id)
            if (
                now - game["createdAt"] > GAME_TTL
                or completed is not None
                and now - completed > COMPLETED_TTL
            ):
                remove_game(game_id)

    @route
    @server_only
    def provide_id():
        player_id = str(randrange(1000000000))
        return {
            "id": player_id,
            "token": create_capability("player", player_id),
        }

    @route
    @forward_to_server
    def request_match(id, player_token):
        id = validate_user(id)
        require_capability("player", id, player_token)
        cleanup_state()
        if id in State.game_lookup:
            game_id = State.game_lookup[id]
            State.last_seen[id] = time.time()
            return {
                "start": True,
                "text": State.game_data[game_id]["text"],
                "players": State.game_data[game_id]["players"],
            }

        if id not in State.queue:
            State.queue[id] = [None, datetime.now()]

        State.queue[id][0] = datetime.now()

        to_remove = []

        for player, (recent_time, join_time) in State.queue.items():
            if datetime.now() - recent_time > QUEUE_TIMEOUT:
                to_remove.append(player)

        for player in to_remove:
            del State.queue[player]

        if (
            len(State.queue) >= MAX_PLAYERS
            or max(
                datetime.now() - join_time
                for recent_time, join_time in State.queue.values()
            )
            >= MAX_WAIT
            and len(State.queue) >= MIN_PLAYERS
        ):
            # start game!
            import cats_gui

            curr_text = cats_gui.load_paragraph()
            if not curr_text:
                return {"start": False, "numWaiting": len(State.queue)}
            game_id = str(randrange(1000000000))

            for player in State.queue:
                State.game_lookup[player] = game_id

            queue = State.queue
            players = list(queue.keys())

            State.game_data[game_id] = {
                "text": curr_text,
                "players": players,
                "createdAt": time.time(),
            }

            for player in queue:
                State.progress[player] = [(0, time.time())]
                State.last_seen[player] = time.time()

            State.queue.clear()

            return {"start": True, "text": curr_text, "players": players}
        else:
            return {"start": False, "numWaiting": len(State.queue)}

    @route
    @server_only
    def set_progress(id, progress, player_token):
        """Record progress message."""
        id = validate_user(id)
        require_capability("player", id, player_token)
        if (
            isinstance(progress, bool)
            or not isinstance(progress, (int, float))
            or not math.isfinite(progress)
            or not 0 <= progress <= 1
        ):
            raise ValueError("progress must be a finite number from 0 to 1")
        if id not in State.progress:
            raise ValueError("unknown player id")
        State.last_seen[id] = time.time()
        State.progress[id].append((progress, time.time()))
        game_id = State.game_lookup.get(id)
        if game_id is not None and all(
            State.progress[player][-1][0] == 1
            for player in State.game_data[game_id]["players"]
        ):
            State.completed_at.setdefault(game_id, time.time())
        return ""

    @route
    @forward_to_server
    def request_progress(id, targets, player_token):
        id = validate_user(id)
        require_capability("player", id, player_token)
        if not isinstance(targets, list) or not targets:
            raise ValueError("targets must be a non-empty list")
        targets = [validate_user(target) for target in targets]
        if any(target not in State.progress for target in targets):
            raise ValueError("targets contains an unknown player id")
        game_id = State.game_lookup.get(id)
        if game_id is None or not set(targets).issubset(
            State.game_data[game_id]["players"]
        ):
            raise ValueError("targets are not in the player's game")
        State.last_seen[id] = time.time()
        now = time.time()
        latest = {t: State.progress[t][-1] for t in targets}
        elapsed = [
            [
                latest[target][0],
                latest[target][1] - State.progress[target][0][1],
                now - State.last_seen.get(target, 0) > ABANDON_TIMEOUT,
            ]
            for target in targets
        ]
        return elapsed

    @route
    @forward_to_server
    def request_all_progress(id, targets, player_token):
        id = validate_user(id)
        require_capability("player", id, player_token)
        if not isinstance(targets, list) or not targets:
            raise ValueError("targets must be a non-empty list")
        targets = [validate_user(target) for target in targets]
        if any(target not in State.progress for target in targets):
            raise ValueError("targets contains an unknown player id")
        game_id = State.game_lookup.get(id)
        if game_id is None or not set(targets).issubset(
            State.game_data[game_id]["players"]
        ):
            raise ValueError("targets are not in the player's game")
        return [State.progress[target] for target in targets]

    @route
    @forward_to_server
    def leave_match(id, player_token):
        id = validate_user(id)
        require_capability("player", id, player_token)
        State.queue.pop(id, None)
        if id in State.last_seen:
            State.last_seen[id] = 0
        return {"success": True}

    @route
    @forward_to_server
    def record_wpm(name, wpm):
        raise RuntimeError("Leaderboard scoring is available on the course server.")

    @route
    @forward_to_server
    def check_on_leaderboard():
        raise RuntimeError("The leaderboard is available on the course server.")

    @route
    @forward_to_server
    def update_name(new_name):
        raise RuntimeError("The leaderboard is available on the course server.")

    @route
    @forward_to_server
    def check_leaderboard_eligibility(wpm):
        raise RuntimeError("The leaderboard is available on the course server.")

    @route
    @forward_to_server
    def request_wpm_challenge(wpm, round_trip_ms=0):
        raise RuntimeError("Score verification is available on the course server.")

    @route
    @forward_to_server
    def claim_wpm_challenge(challenge_id, typed):
        raise RuntimeError("Score verification is available on the course server.")

    @route
    @forward_to_server
    def leaderboard():
        with connect_db() as db:
            return list(
                list(x)
                for x in db(
                    "SELECT name, wpm FROM leaderboard "
                    "WHERE name <> '' AND wpm >= 0 "
                    "ORDER BY wpm DESC LIMIT 20"
                ).fetchall()
            )

    return State
