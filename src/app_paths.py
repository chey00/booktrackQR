import os
import sys


APP_NAME = "BooktrackQR"


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _bundle_base_dir() -> str:
    # PyInstaller: resources are unpacked to sys._MEIPASS
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts: str) -> str:
    """
    Resolve a read-only resource path for both dev and bundled (.app) runs.
    """
    return os.path.join(_bundle_base_dir(), *parts)


def resource_path_any(*candidates: str) -> str:
    """
    Return the first existing resource path from candidates.
    Each candidate is a relative path.
    """
    for rel in candidates:
        p = resource_path(rel)
        if os.path.exists(p):
            return p
    return resource_path(candidates[0]) if candidates else resource_path("")


def user_data_dir() -> str:
    """
    macOS user-writable app data directory.
    Allows override via BOOKTRACKQR_DATA_DIR for testing.
    """
    override = os.getenv("BOOKTRACKQR_DATA_DIR")
    if override:
        return override

    home = os.path.expanduser("~")
    return os.path.join(home, "Library", "Application Support", APP_NAME)


def user_data_path(*parts: str) -> str:
    return os.path.join(user_data_dir(), *parts)


def ensure_user_data_dir(*parts: str) -> str:
    path = user_data_path(*parts)
    os.makedirs(path, exist_ok=True)
    return path
