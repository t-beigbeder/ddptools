import os


def _home() -> str:
    return os.path.expanduser("~")


def xdg_config_dir() -> str:
    cd = os.environ.get("XDG_CONFIG_DIR", _home() + "/.config")
    if os.path.exists(cd):
        return cd
    os.makedirs(cd, 0o700)
    return cd
