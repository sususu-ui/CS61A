"""Ask Ok whether Phase 1–3 problems pass."""

import os
import sys
import threading
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PHASE1_PROBLEMS = (
    ("choose", "01"),
    ("about", "02"),
    ("accuracy", "03"),
    ("wpm", "04"),
)

PHASE2_PROBLEMS = (
    ("autocorrect", "05"),
    ("sphinx_fixes", "06"),
    ("minimum_mewtations", "07"),
)

PHASE3_PROBLEMS = (
    ("report_progress", "08"),
    ("time_per_word", "09"),
    ("fastest_words", "10"),
)

_ASSIGNMENT = None
_STATUS = None
_GRADE_LOCK = threading.Lock()


def _ok_zip():
    for candidate in (ROOT / "ok", ROOT.parent / "pack" / "ok"):
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "Could not find the Ok runner (ok). Re-download the project zip."
    )


@contextmanager
def _in_root():
    previous = os.getcwd()
    os.chdir(ROOT)
    try:
        yield
    finally:
        os.chdir(previous)


def _ensure_ok_path():
    ok_path = str(_ok_zip())
    if ok_path not in sys.path:
        sys.path.insert(0, ok_path)


def _output():
    _ensure_ok_path()
    from client.utils import output

    return output


@contextmanager
def _ok_silent():
    output = _output()
    logger = output._logger
    saved = logger._stdout
    logger._stdout = logger._devnull
    logger.off()
    try:
        yield
    finally:
        logger._stdout = saved
        logger.on()


def _assignment():
    global _ASSIGNMENT
    if _ASSIGNMENT is not None:
        return _ASSIGNMENT
    _ensure_ok_path()
    from client.api.assignment import Settings, load_assignment

    with _in_root():
        _ASSIGNMENT = load_assignment(
            str(ROOT / "proj02.ok"),
            Settings(
                local=True,
                nointeract=True,
                verbose=False,
                no_update=True,
            ),
        )
    return _ASSIGNMENT


def _grade(question):
    with _GRADE_LOCK, _in_root(), _ok_silent():
        return _assignment().grade(question, env={}, skip_locked_cases=True)


def _phase(problems):
    failures = []
    for name, question in problems:
        result = _grade(question)
        if result.get("failed") or result.get("locked"):
            failures.append({"name": name, "detail": f"python ok -q {question}"})
    return {"ready": not failures, "failures": failures}


def require_phase1():
    """Exit before the GUI port opens if Phase 1 is unfinished or locked."""
    locked = []
    failed = []
    try:
        for name, question in PHASE1_PROBLEMS:
            result = _grade(question)
            if result.get("locked"):
                locked.append(question)
            elif result.get("failed"):
                failed.append((name, question))
    except Exception as error:
        print("The Cats GUI can't start until Ok can run Phase 1 tests.")
        print()
        print(error)
        sys.exit(1)
    if locked:
        print("The Cats GUI can't start until Phase 1 Ok tests are unlocked.")
        print()
        print("Unlock them with:")
        for question in locked:
            print(f"  python ok -q {question} -u")
        print()
        print("Then run: python cats_gui.py")
        sys.exit(1)
    if failed:
        print("The Cats GUI can't start until Phase 1 works.")
        print()
        print("These functions still fail the Ok tests:")
        for name, question in failed:
            print(f"  - {name}   (python ok -q {question})")
        print()
        print("Fix them, then run: python cats_gui.py")
        sys.exit(1)
    global _STATUS
    _STATUS = _current_status()


def _current_status():
    import cats

    multiplayer = _phase(PHASE3_PROBLEMS)
    multiplayer["enabled"] = bool(getattr(cats, "enable_multiplayer", False))
    return {
        "autocorrect": _phase(PHASE2_PROBLEMS),
        "multiplayer": multiplayer,
    }


def implementation_status():
    # Ok's timeout uses SIGALRM, which only works on the main thread.
    # Grade during require_phase1() and reuse that result here.
    if _STATUS is None:
        return {
            "autocorrect": {"ready": False, "failures": []},
            "multiplayer": {
                "ready": False,
                "failures": [],
                "enabled": False,
            },
        }
    return _STATUS
