from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import webbrowser, json, os, threading, functools, urllib.parse
from ants import *
import bees_ext
import ants_plans
import level
import workshop


STARTUP = {"difficulty": "normal", "food": 3, "deploys_limit": 4, "layout": None}

SERVE_PORT = 31415

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
# the token from the last sign in, so restarting the gui is not a new login
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ants-session")


# ---------------------------------------------------------------------------
# game state
# ---------------------------------------------------------------------------


class Game:
    lock = threading.RLock()  # reentrant, routes call snapshot() while holding it
    pending = []              # events waiting to be shipped to the page
    snapshot_seq = 0
    phase_counter = 0         # how many times next() has been called since new()
    over = False
    state = None              # the GameState
    sim = None                # the generator driving it
    by_shot = False           # set while inside throw_at, read by reduce_health


# ---------------------------------------------------------------------------
# tracing
# ---------------------------------------------------------------------------


def outermost(key):
    """Only the outermost call for (object, key) runs the wrapper.
    A nested call, such as an override calling super(), falls straight
    through to the original method, so the event is recorded once."""
    guard = "_gui_" + key

    def wrap(make_decorator):
        def decorator(fn):
            body = make_decorator(fn)

            @functools.wraps(fn)
            def decorated(self, *args, **kwargs):
                if getattr(self, guard, False):
                    return fn(self, *args, **kwargs)
                setattr(self, guard, True)
                try:
                    return body(self, *args, **kwargs)
                finally:
                    setattr(self, guard, False)

            return decorated
        return decorator
    return wrap


@outermost("reduce_health")
def reduce_health_decorator(reduce_health_o):
    def decorated(self, amount):
        before = self.health
        try:
            res = reduce_health_o(self, amount)
        finally:
            after = self.health
            record("reduce_health", id=self.id, health=after, amount=before - after, byShot=Game.by_shot)
            if before > 0 and after <= 0:
                record("die", id=self.id)
        return res
    return decorated


@outermost("throw_at")
def throw_at_decorator(throw_at_o):
    def decorated(self, target):
        Game.by_shot = True
        try:
            res = throw_at_o(self, target)
        finally:
            Game.by_shot = False
        if target is not None:
            record("throw_at", source_kind=self.name, source=self.id, target=target.id, damage=self.damage)
        return res
    return decorated


@outermost("buff")
def buff_decorator(buff_o):
    def decorated(self):
        if not getattr(self, "_guitrace_buffed", False):
            self._guitrace_buffed = True
            record("buffed", id=self.id)
        return buff_o(self)
    return decorated


@outermost("move")
def move_to_decorator(move_to_o):
    def decorated(self, place):
        old_kind, old_row, old_col = place_data(self.place)
        new_kind, new_row, new_col = place_data(place)
        try:
            return move_to_o(self, place)
        finally:
            record("move", id=self.id, old=[old_row, old_col], new=[new_row, new_col],
                    fromPlace=old_kind, toPlace=new_kind, info=insect_to_dict(self))
            if isinstance(self, bees_ext.BossHeart) and old_kind == "hive":
                record("hive_fade")
    return decorated


@outermost("harvester_action")
def harvester_action_decorator(harvester_action_o):
    def decorated(self, gamestate):
        record("harvest", source=self.id)
        return harvester_action_o(self, gamestate)
    return decorated


# An ugly way to trace slow and scare due to not prescribed naming of attr... Literally copies an answer...
# Perhaps you can fix it yourself?
@outermost("slow")
def slow_throw_at_decorator(throw_at_o):
    def decorated(self, target):
        res = throw_at_o(self, target)
        if target is not None:
            if getattr(target, "_guitrace_slow_length", None) is None:
                target._guitrace_slow_length = 0
            target._guitrace_slow_length += 3
            record("slow", id=target.id)
        return res
    return decorated


@outermost("scare")
def scare_throw_at_decorator(throw_at_o):
    def decorated(self, target):
        res = throw_at_o(self, target)
        if target is not None:
            if getattr(target, "_guitrace_scared", None) is None:
                target._guitrace_scared = False
                target._guitrace_scare_length = 0
            if not target._guitrace_scared:
                target._guitrace_scare_length = 3
                target._guitrace_scared = True
                record("scare", id=target.id)
        return res
    return decorated


@outermost("bee_action")
def bee_action_decorator(bee_action_o):
    def decorated(self, gamestate):
        scare_left = getattr(self, "_guitrace_scare_length", 0)
        slow_left = getattr(self, "_guitrace_slow_length", 0)
        # Bee.action picks its branch before pre_action runs, and a slowed bee on an
        # odd turn does nothing at all, so one scare turn is only spent on the others
        advances = self.health > 0 and not self.blocked()
        slowed_now = slow_left > 0 and gamestate.time % 2 != 0
        res = bee_action_o(self, gamestate)
        # pre_action can kill the bee before it ever reaches advance
        if scare_left > 0 and advances and not slowed_now and self.health > 0:
            self._guitrace_scare_length = scare_left - 1
        return res
    return decorated


def slow_tick_decorator(bees_take_actions_o):
    """Spend one slow turn per bee per turn.

    Not done in Bee.action: a student may replace target.action with a wrapper that
    skips the real method on the slowed turns, and then nothing would tick.
    """
    def decorated(self, keep=lambda insect: True):
        try:
            return bees_take_actions_o(self, keep)
        finally:
            for bee in list(getattr(self, "active_bees", ())):
                length = getattr(bee, "_guitrace_slow_length", 0)
                if length > 0:
                    bee._guitrace_slow_length = length - 1
    return decorated


@outermost("add_bee")
def add_bee_decorator(add_bee_o):
    def decorated(self, bee, place, join=True):
        res = add_bee_o(self, bee, place, join)
        record("deploy", id=bee.id, info=insect_to_dict(bee))
        return res
    return decorated


@outermost("waxer_wax")
def waxer_wax_decorator(wax_o):
    def decorated(self, layer=None):
        res = wax_o(self, layer)
        record("wax", id=self.id, layer=self.wax_layer, layer_max=self.wax_max)
        return res
    return decorated


@outermost("waxer_reduce_health")
def waxer_reduce_health_decorator(reduce_health_o):
    def decorated(self, amount):
        res = reduce_health_o(self, amount)
        record("rh_wax", id=self.id, layer=self.wax_layer, layer_max=self.wax_max)
        return res
    return decorated


@outermost("bossheart_frenzy")
def bossheart_frenzy_decorator(frenzy_o):
    def decorated(self):
        new_frenzied = frenzy_o(self)
        for bee in new_frenzied:
            if bee is None:
                continue
            record("buffed", id=bee.id)
        return new_frenzied
    return decorated


@outermost("bossheart_impale")
def bossheart_impale_decorator(impale_o):
    def decorated(self, level):
        res = impale_o(self, level)
        for _, ant in self.poisoned_ants_pairs:
            if ant is None:
                continue
            record("poison", id=ant.id)
        return res
    return decorated


@outermost("bossheart_feed")
def bossheart_feed_decorator(feed_o):
    def decorated(self, level):
        res = feed_o(self, level)
        record("feed", id=self.id, health=self.health)
        return res
    return decorated


def all_subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from all_subclasses(sub)


def decorate_all(base, name, decorator):
    """Wrap NAME on BASE and on every subclass that overrides it."""
    for cls in [base, *all_subclasses(base)]:
        fn = cls.__dict__.get(name)
        if fn is not None:
            setattr(cls, name, decorator(fn))


Insect.reduce_health = reduce_health_decorator(Insect.reduce_health)
decorate_all(ThrowerAnt, "throw_at", throw_at_decorator)
Ant.buff = buff_decorator(Ant.buff)
Bee.move_to = move_to_decorator(Bee.move_to)
SlowThrower.throw_at = slow_throw_at_decorator(SlowThrower.throw_at)
ScaryThrower.throw_at = scare_throw_at_decorator(ScaryThrower.throw_at)
Bee.action = bee_action_decorator(Bee.action)
GameState.bees_take_actions = slow_tick_decorator(GameState.bees_take_actions)
HarvesterAnt.action = harvester_action_decorator(HarvesterAnt.action)
bees_ext.gamestate_add_extra_bee = add_bee_decorator(bees_ext.gamestate_add_extra_bee)
bees_ext.Waxer.wax = waxer_wax_decorator(bees_ext.Waxer.wax)
bees_ext.Waxer.reduce_health = waxer_reduce_health_decorator(bees_ext.Waxer.reduce_health)
bees_ext.BossHeart.frenzy = bossheart_frenzy_decorator(bees_ext.BossHeart.frenzy)
bees_ext.BossHeart.impale = bossheart_impale_decorator(bees_ext.BossHeart.impale)
bees_ext.BossHeart.feed = bossheart_feed_decorator(bees_ext.BossHeart.feed)


# ---------------------------------------------------------------------------
# game loop
# ---------------------------------------------------------------------------


# ants in here bank their food at the start of the turn, before the player places
# EARLY_ACTORS = (HarvesterAnt,)
EARLY_ACTORS = ()


def simulate(gamestate):
    """Drive the game from the GUI."""
    try:
        while True:
            gamestate.beehive_strategy() # Bees invade from hive
            gamestate.deploys_this_turn = 0 # a new turn, the deploy quota refills
            gamestate.ants_take_actions(lambda insect: isinstance(insect, EARLY_ACTORS))
            yield None # After yielding, players have time to place ants
            gamestate.ants_take_actions(lambda insect: not isinstance(insect, EARLY_ACTORS))
            gamestate.time += 1
            yield None # After yielding, wait for throw leaf animation to play, then ask bees to take action
            gamestate.bees_take_actions()
    except AntsWinException:
        print('All bees are vanquished. You win!')
        yield True
    except AntsLoseException:
        print('The bees reached homebase or the queen ant queen has perished. Please try again :(')
        yield False


# ---------------------------------------------------------------------------
# api handlers
# ---------------------------------------------------------------------------

MAX_EVENTS = 3000
def record(event, **fields):
    if len(Game.pending) >= MAX_EVENTS:
        return
    Game.pending.append({"event": event, "seq": len(Game.pending), **fields})


def record_insert(idx, event, **fields):
    Game.pending.insert(idx, {"event": event, "seq": len(Game.pending), **fields})


def merge_moves(events):
    """Collapse consecutive hops of the same insect into one."""
    out = []
    for ev in events:
        if ev["event"] != "move":
            out.append(ev)
            continue
        if ev["old"] == ev["new"]:
            continue
        prev = out[-1] if out else None
        if (prev is not None
                and prev["event"] == "move"
                and prev["id"] == ev["id"]
                and prev["new"] == ev["old"]
                and prev["new"] != [-1, -1]):
            prev["new"] = ev["new"]
            prev["toPlace"] = ev["toPlace"]
            prev["info"] = ev.get("info", prev.get("info"))
            continue
        out.append(ev)
    return out


def flush():
    batch = list(Game.pending)
    Game.pending.clear()
    return merge_moves(batch)


def next_actor():
    """Who acts when the player's clock next runs out."""
    # resumption 1 of simulate() only spawns bees, ants and bees alternate after
    return "ant" if Game.phase_counter % 2 == 1 else "bee"


def next_action():
    with Game.lock:
        if Game.sim is None:
            return fail("not_started", "call /api/new first")
        try:
            res = next(Game.sim)
        except StopIteration:
            return {"ok": False, "snapshot": snapshot()}
        else:
            Game.phase_counter += 1
            Game.over = res is not None
            return {"ok": True, "snapshot": snapshot(), "events": flush(), "over": Game.over, "win": res}


def place_data(place):
    if place is None:
        return "", -1, -1
    if isinstance(place, Hive):
        return "hive", -1, -1
    if isinstance(place, AntHomeBase):
        return "base", -1, -1
    kind, row, col = place.name.split('_')
    row, col = int(row), int(col)
    return kind, row, col


def new(data=None):
    with Game.lock:
        Game.pending.clear()
        Game.phase_counter = 0
        Game.over = False
        Game.state = parse_level(data or {})
        Game.sim = simulate(Game.state)
        try:
            next(Game.sim)
            Game.phase_counter = 1
        except StopIteration:
            pass
        return {"ok": True, "board": board(), "snapshot": snapshot(), "availableAnts": available_ants()}


def parse_level(data=None):
    """The level page opens a built-in level by name, the custom one, or a
    level downloaded from the workshop."""
    if data and data.get("levelFile"):
        if not level.ENABLE_PLAYABLE_LEVELS:
            raise workshop.WorkshopError(403, "disabled", "playable levels are turned off")
        print("===== Start {} =====".format(data["levelFile"]))
        return level.make_level_game_state(workshop.load_level(data["levelFile"]))
    if level.ENABLE_PLAYABLE_LEVELS:
        name = (data or {}).get("level", level.CUSTOM_LEVEL)
        print("===== Start {} =====".format(name))
        return level.make_level_game_state(level.make_level(name))
    print("===== Start testing difficulty {} =====".format(STARTUP["difficulty"]))
    return ants_plans.make_difficulty_game_state(STARTUP["difficulty"], STARTUP["food"], STARTUP["layout"], STARTUP["deploys_limit"])


RANDOMLIZED_OFFSET = (bees_ext.Beeling,)


def insect_to_dict(insect):
    kind, row, col = place_data(insect.place)
    tags = []
    if isinstance(insect, Ant):
        isAnt = True
        if isinstance(insect, ContainerAnt): tags.append("container")
        if getattr(insect, "chew_countdown", 0) > 0: tags.append("chewing")
        if getattr(insect, "poisoned", False): tags.append("poison")
        if getattr(insect, "_guitrace_buffed", False): tags.append("buffed")
        if isinstance(insect, QueenAnt): tags.append("queen")
    else:
        isAnt = False
        if getattr(insect, "_guitrace_slow_length", 0) > 0: tags.append("slow")
        if getattr(insect, "_guitrace_scare_length", 0) > 0: tags.append("scare")
        if getattr(insect, "frenzied", False): tags.append("buffed")
        if isinstance(insect, bees_ext.BossHeart): tags.append("boss")
        if isinstance(insect, bees_ext.Waxer) and insect.wax_layer > 0:
            tags.append("wax_{0}_{1}".format(insect.wax_layer, insect.wax_max))
    return {
        "kind": insect.name,
        "health": insect.health,
        "maxHealth": insect.max_health,
        "place": kind,
        "row": row,
        "col": col,
        "isAnt": isAnt,
        "randomlized_offset": isinstance(insect, RANDOMLIZED_OFFSET),
        "tags": tags
    }


def available_ants():
    assert Game.state is not None
    return {name: cls.food_cost for name, cls in Game.state.ant_types.items() if cls.implemented}


def deploys_limit():
    return getattr(Game.state, "max_deploys_per_turn", None)


def deploys_left():
    limit = deploys_limit()
    if limit is None:
        return None
    return max(0, limit - getattr(Game.state, "deploys_this_turn", 0))


def snapshot():
    with Game.lock:
        if Game.state is None:
            return None

        Game.snapshot_seq += 1

        insects = {}
        for place in Game.state.places.values():
            kind, row, col = place_data(place)

            if place.ant is not None:
                insects[place.ant.id] = insect_to_dict(place.ant)
                contained = getattr(place.ant, "ant_contained", None)
                if contained is not None:
                    insects[contained.id] = insect_to_dict(contained)

            if kind != "hive":  # bees still waiting in the hive are not on the board
                for bee in place.bees:
                    insects[bee.id] = insect_to_dict(bee)

        return {
            "seq": Game.snapshot_seq,
            "turn": Game.state.time,
            "food": Game.state.food,
            "hive": len(Game.state.beehive.bees),  # bees still queued in the hive
            "next": next_actor(),                  # who acts on the next action
            "maxDeploys": deploys_limit(),        # None when the level has no cap
            "deploysLeft": deploys_left(),
            "insects": insects,
            "antTypes": [{"name": cls.name, "cost": cls.food_cost}
                         for cls in Game.state.ant_types.values()],
        }


def board():
    with Game.lock:
        if Game.state is None:
            return None
        places = []
        for place in Game.state.places.values():
            kind, row, col = place_data(place)
            places.append({"kind": kind, "row": row, "col": col})
        return {"dimensions": list(Game.state.dimensions), "places": places}


def fail(reason, message):
    return {"ok": False, "reason": reason, "error": message}


def parse_place(pos):
    """Check a place from the page. Returns (place_name, (status, payload))."""
    if not isinstance(pos, dict) or not {"kind", "row", "col"} <= set(pos):
        return None, (400, fail("bad_request", "place needs kind, row and col"))
    try:
        place_name = f'{pos["kind"]}_{int(pos["row"])}_{int(pos["col"])}'
    except (TypeError, ValueError):
        return None, (400, fail("bad_request", "row and col must be numbers"))
    if place_name not in Game.state.places:
        return None, (400, fail("bad_place", f"no such place: {place_name}"))
    return place_name, None


def deploy(pos, ant_name):
    """Returns (http_status, payload). 4xx only for bad requests, a refused
    but well-formed move is still a 200 with ok: false."""
    with Game.lock:
        if Game.state is None:
            return 409, fail("not_started", "call /api/new first")
        if Game.over:
            return 200, fail("game_over", "the game has already ended")

        place_name, error = parse_place(pos)
        if error is not None:
            return error
        if ant_name not in Game.state.ant_types:
            return 400, fail("unknown_ant", f"no such ant: {ant_name}")

        try:
            ant = Game.state.deploy_ant(place_name, ant_name)
        except AssertionError as exc:
            return 200, fail("occupied", str(exc))

        if ant is None:
            return 200, fail("deploy_failed", "deploy failed due to not enough food, no deploys left this turn or queen has been existed")
        info = insect_to_dict(ant)
        info["place"] = pos["kind"]
        info["row"] = int(pos["row"])
        info["col"] = int(pos["col"])
        record_insert(0, "deploy", id=ant.id, info=info)
        return 200, {"ok": True, "events": flush(), "snapshot": snapshot()}


def remove(pos):
    with Game.lock:
        if Game.state is None:
            return 409, fail("not_started", "call /api/new first")
        if Game.over:
            return 200, fail("game_over", "the game has already ended")

        place_name, error = parse_place(pos)
        if error is not None:
            return error

        place = Game.state.places[place_name]
        before = place.ant

        if before is None:
            return 200, fail("empty", "no ant in this place")
        
        Game.state.remove_ant(place_name)
        if place.ant is before:
            return 200, fail("not_removable", f"{before.name} is not removable")
        record_insert(0, "remove", id=before.id)
        return 200, {"ok": True, "events": flush(), "snapshot": snapshot()}


# ---------------------------------------------------------------------------
# workshop: local copies and the remote catalogue
# ---------------------------------------------------------------------------

def reply(fn):
    try:
        return 200, fn()
    except workshop.WorkshopError as exc:
        return exc.status, {"ok": False, "reason": exc.reason, "error": str(exc)}


def workshop_call(fn):
    # the whole workshop hangs off the playable-levels switch
    if not level.ENABLE_PLAYABLE_LEVELS:
        return 403, {"ok": False, "reason": "disabled",
                     "error": "playable levels are turned off"}
    return reply(fn)


def query_int(query, key):
    """A page parameter from the query string; anything odd just means zero."""
    raw = (query.get(key) or [""])[0].strip()
    if not raw:
        return 0
    try:
        return int(raw)
    except ValueError:
        return 0


def query_text(query, key):
    return (query.get(key) or [""])[0].strip()


def workshop_downloads():
    return workshop_call(lambda: {"ok": True, "levels": workshop.list_downloads()})


def workshop_download(data):
    level_id = (data or {}).get("id")
    return workshop_call(lambda: {"ok": True, "level": workshop.download(level_id)})


def workshop_local(level_id):
    return workshop_call(lambda: {"ok": True, "level": workshop.get_download(level_id)})


def workshop_forget(level_id):
    def run():
        workshop.delete_download(level_id)
        return {"ok": True}
    return workshop_call(run)


def workshop_catalogue(query):
    def run():
        levels, total = workshop.remote_levels(
            title=query_text(query, "title"),
            author=query_text(query, "author"),
            description=query_text(query, "description"),
            level_id=query_text(query, "id"),
            exact=query_text(query, "exact"),
            owner=query_text(query, "owner"),
            sort=query_text(query, "sort"),
            offset=query_int(query, "offset"),
            limit=query_int(query, "limit"),
            token=stored_token())
        return {"ok": True, "total": total, "levels": levels}
    return workshop_call(run)


def workshop_remote(level_id):
    return workshop_call(lambda: {"ok": True, "level": workshop.remote_get(level_id)})


def workshop_publish(data):
    def run():
        return {"ok": True, "level": workshop.remote_publish(data, current_token())}
    return workshop_call(run)


def workshop_unpublish(level_id):
    def run():
        workshop.remote_delete(level_id, current_token())
        return {"ok": True}
    return workshop_call(run)


def workshop_like(level_id, liked):
    def run():
        return {"ok": True, "level": workshop.remote_like(level_id, current_token(), liked)}
    return workshop_call(run)


class Session:
    lock = threading.RLock()
    token = ""
    identity = {}


class Login:
    lock = threading.RLock()
    verifier = ""
    state = ""


# held until the stored token has been checked, so a page load sees the real answer
SESSION_READY = threading.Event()
SESSION_READY.set()


def forget_stored_session():
    try:
        os.remove(SESSION_FILE)
    except OSError:
        pass


def store_session():
    with Session.lock:
        token = Session.token
        username = Session.identity.get("username") or ""
    if not token:
        return
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as handle:
            json.dump({"token": token, "username": username}, handle)
    except OSError:
        pass


def load_stored_session():
    """Bring back the last token, unless the workshop server has forgotten it."""
    try:
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as handle:
                stored = json.load(handle)
        except (OSError, ValueError):
            return
        token = stored.get("token") if isinstance(stored, dict) else ""
        if not token:
            return
        try:
            identity = workshop.remote_session(token)
        except workshop.WorkshopError as exc:
            # a server that is merely down should not cost the player a sign in
            if exc.status in (401, 403):
                forget_stored_session()
            return
        with Session.lock:
            Session.token = token
            Session.identity = {
                "userId": identity.get("userId") or "",
                "username": identity.get("username") or "",
            }
    finally:
        SESSION_READY.set()


def stored_token():
    """The token this page holds, or empty: listing works without a sign in."""
    with Session.lock:
        return Session.token


def current_token():
    token = stored_token()
    if not token:
        raise workshop.WorkshopError(401, "authentication_required", "sign in first")
    return token


def login_available():
    # the callback address is fixed at 31415, so no other port can finish a login
    return SERVE_PORT == workshop.LOGIN_PORT and workshop.remote_configured()


def login_start():
    def run():
        if not login_available():
            raise workshop.WorkshopError(
                503, "login_unavailable",
                "sign in needs port %d and a workshop server" % workshop.LOGIN_PORT)
        verifier, challenge, state = workshop.pkce_pair()
        with Login.lock:
            Login.verifier = verifier
            Login.state = state
        return {"ok": True, "url": workshop.login_url(challenge, state)}
    return workshop_call(run)


def login_finish(code, state):
    def run():
        with Login.lock:
            verifier, expected = Login.verifier, Login.state
            Login.verifier = ""
            Login.state = ""
        if not verifier or not expected:
            raise workshop.WorkshopError(400, "login_failed", "no sign in was started")
        if state != expected:
            raise workshop.WorkshopError(400, "login_failed", "the login state did not match")
        if not code:
            raise workshop.WorkshopError(400, "login_failed", "the judge returned no code")

        result = workshop.remote_login(code, verifier, state)
        token = result.get("token") or ""
        if not token:
            raise workshop.WorkshopError(502, "login_failed", "the workshop server issued no session")
        with Session.lock:
            Session.token = token
            Session.identity = {
                "userId": result.get("userId") or "",
                "username": result.get("username") or "",
            }
        store_session()
        return {"ok": True}
    return workshop_call(run)


def session_state():
    def run():
        SESSION_READY.wait(timeout=10)
        with Session.lock:
            signed_in = bool(Session.token)
            identity = dict(Session.identity)
        return {
            "ok": True,
            "signedIn": signed_in,
            "userId": identity.get("userId") or "",
            "username": identity.get("username") or "",
        }
    return workshop_call(run)


def session_logout():
    def run():
        with Session.lock:
            token = Session.token
            Session.token = ""
            Session.identity = {}
        forget_stored_session()
        # the server keeps the session until it is told, or until it expires
        workshop.remote_logout(token)
        return {"ok": True}
    return workshop_call(run)


def new_game(data):
    # starting a game is not a workshop feature, only the error mapping is shared
    return reply(lambda: new(data))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC, **kwargs)

    def do_GET(self):
        if self.path.startswith("/?catsAuthCode="):
            return self.finish_login()
        if not self.path.startswith("/api/"):
            return super().do_GET()

        if self.path == "/api/board":
            return self.send_json(board())
        if self.path == "/api/snapshot":
            return self.send_json(snapshot())
        if self.path == "/api/config":
            return self.send_json({
                "levelPage": level.ENABLE_PLAYABLE_LEVELS,
                "difficulty": STARTUP["difficulty"],
                "customLevel": level.CUSTOM_LEVEL,
                "builtinLevels": list(level.BUILTIN_LEVELS) if level.ENABLE_PLAYABLE_LEVELS else [],
                "workshopRemote": workshop.remote_configured(),
                "ojLoginUrl": workshop.oj_login_url() if login_available() else "",
            })
        if self.path == "/api/workshop/login/start":
            return self.send_result(login_start())
        if self.path == "/api/workshop/session":
            return self.send_result(session_state())
        if self.path == "/api/workshop/downloads":
            return self.send_result(workshop_downloads())
        if self.path.startswith("/api/workshop/downloads/"):
            level_id = self.path[len("/api/workshop/downloads/"):]
            return self.send_result(workshop_local(level_id))
        if self.path == "/api/workshop/remote" or self.path.startswith("/api/workshop/remote?"):
            query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return self.send_result(workshop_catalogue(query))
        if self.path.startswith("/api/workshop/remote/"):
            level_id = self.path[len("/api/workshop/remote/"):]
            return self.send_result(workshop_remote(level_id))
        if self.path == "/api/level/custom-plain":
            if not level.ENABLE_PLAYABLE_LEVELS:
                return self.send_json({"ok": False, "reason": "disabled",
                                       "error": "playable levels are turned off"}, status=403)
            return self.send_json({"ok": True, "level": level.make_custom_level().to_plain()})
        return self.send_json({"ok": False, "error": "not found"}, status=404)

    def do_POST(self):
        if not self.path.startswith("/api/"):
            return self.send_json({"ok": False, "error": "not found"}, status=404)

        try:
            data = self.read_json()
        except (ValueError, UnicodeDecodeError):
            return self.send_json({"ok": False, "error": "invalid json"}, status=400)

        if self.path == "/api/new":
            return self.send_result(new_game(data))
        if self.path == "/api/deploy":
            status, payload = deploy(data.get("place"), data.get("ant"))
            return self.send_json(payload, status=status)
        if self.path == "/api/remove":
            status, payload = remove(data.get("place"))
            return self.send_json(payload, status=status)
        if self.path == "/api/action":
            return self.send_json(next_action())
        if self.path == "/api/workshop/downloads":
            return self.send_result(workshop_download(data))
        if self.path == "/api/workshop/publish":
            return self.send_result(workshop_publish(data))
        if self.path.startswith("/api/workshop/likes/"):
            level_id = self.path[len("/api/workshop/likes/"):]
            return self.send_result(workshop_like(level_id, True))
        if self.path == "/api/workshop/logout":
            return self.send_result(session_logout())
        return self.send_json({"ok": False, "error": "not found"}, status=404)

    def do_DELETE(self):
        if self.path.startswith("/api/workshop/downloads/"):
            level_id = self.path[len("/api/workshop/downloads/"):]
            return self.send_result(workshop_forget(level_id))
        if self.path.startswith("/api/workshop/likes/"):
            level_id = self.path[len("/api/workshop/likes/"):]
            return self.send_result(workshop_like(level_id, False))
        if self.path.startswith("/api/workshop/remote/"):
            level_id = self.path[len("/api/workshop/remote/"):]
            return self.send_result(workshop_unpublish(level_id))
        return self.send_json({"ok": False, "error": "not found"}, status=404)

    def finish_login(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = (params.get("catsAuthCode") or [""])[0]
        state = (params.get("state") or [""])[0]
        status, payload = login_finish(code, state)
        if status != 200:
            print("login failed: %s %s" % (
                payload.get("reason"), payload.get("error")), flush=True)
            return self.redirect("/workshop.html?login=failed")
        return self.redirect("/workshop.html")

    def redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_result(self, result):
        status, payload = result
        self.send_json(payload, status=status)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def log_message(self, format, *args):
        pass
        # print("%s %s" % (self.command, self.path), flush=True)


def cli_options(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Play Ants vs. SomeBees")

    parser.add_argument('-d', type=str, metavar='DIFFICULTY', help='sets difficulty of game (test/easy/normal/hard/extra-hard)')
    parser.add_argument('-w', '--water', action='store_true', help='loads a full layout with water')
    parser.add_argument('--food', type=int, help='number of food to start with when testing', default=3)
    parser.add_argument('--deploys-limit', type=int, help='number of max deploys per turn, no limit if 0', default=4)
    args = parser.parse_args(argv)

    return {
        "difficulty": ants_plans.parse_difficulty(args.d),
        "food": args.food,
        "deploys_limit": None if args.deploys_limit == 0 else args.deploys_limit,
        "layout": wet_layout if args.water else dry_layout,
    }


def main():
    if not level.ENABLE_PLAYABLE_LEVELS:
        STARTUP.update(cli_options())

    try:
        server = ThreadingHTTPServer(("localhost", SERVE_PORT), Handler)
    except OSError:
        print(f"port {SERVE_PORT} is already in use.")
        return

    url = f"http://localhost:{SERVE_PORT}/"
    print('\n******************** Ants vs SomeBees GUI ********************\n')
    print(f'Game available at: {url}')
    print('Hit Control + C to stop running this file\n')
    if SERVE_PORT != workshop.LOGIN_PORT:
        print(f"sign in disabled: the judge only calls back on {workshop.LOGIN_PORT}")

    if workshop.remote_configured():
        SESSION_READY.clear()
        threading.Thread(target=load_stored_session, daemon=True).start()
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server.server_close() 


if __name__ == "__main__":
    main()