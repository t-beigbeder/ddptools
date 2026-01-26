def cat(target: str, *origins: str) -> None:
    with open(target, "wb") as fo:
        for origin in origins:
            with open(origin, "rb") as fi:
                fo.write(fi.read())
    return None


def read_pass_file(path: str) -> str | None:
    with open(path, "r") as f:
        for line in f:
            password = line[:-1] if line.endswith("\n") else line
            return password
    return None


def read_creds_file(path: str) -> tuple[str, str] | None:
    with open(path, "r") as f:
        for line in f:
            if line.endswith("\n"):
                line = line[:-1]
            auth = line.split(":")
            if len(auth) == 2:
                return auth[0], auth[1]
            raise ValueError(f"{path}: {line}")
    return None
