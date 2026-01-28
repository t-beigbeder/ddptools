import os


def _home() -> str:
    return os.environ.get("HOME", "")


def xdg_config_dir() -> str:
    cd = os.environ.get("XDG_CONFIG_DIR", _home() + "/.config")
    if os.path.exists(cd):
        return cd
    os.makedirs(cd, 0o700)
    return cd


def xdg_cache_dir() -> str:
    cd = os.environ.get("XDG_CACHE_HOME", _home() + "/.cache")
    if os.path.exists(cd):
        return cd
    os.makedirs(cd, 0o700)
    return cd
