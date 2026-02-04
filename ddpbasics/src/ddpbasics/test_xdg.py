from .xdg import xdg_config_dir, xdg_cache_dir


def test_xdg_wo_env_mkd(monkeypatch, tmp_path):
    home = str(tmp_path / "home")
    monkeypatch.setenv("HOME", home)
    monkeypatch.delenv("XDG_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    cd = xdg_config_dir()
    assert cd == str(tmp_path / "home" / ".config")
    cd = xdg_cache_dir()
    assert cd == str(tmp_path / "home" / ".cache")


def test_xdg_wo_env_no_mkd(monkeypatch, tmp_path):
    h2p = tmp_path / "home2"
    home2 = str(h2p)
    h2p.mkdir(0o770, parents=True)
    (h2p / ".config").mkdir(0o700)
    (h2p / ".cache").mkdir(0o700)
    monkeypatch.setenv("HOME", home2)
    monkeypatch.delenv("XDG_CONFIG_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    cd = xdg_config_dir()
    assert cd == str(tmp_path / "home2" / ".config")
    cd = xdg_cache_dir()
    assert cd == str(tmp_path / "home2" / ".cache")


def test_xdg_with_env(monkeypatch, tmp_path):
    xdg_cod = str(tmp_path / "xdg_cod")
    monkeypatch.setenv("XDG_CONFIG_DIR", xdg_cod)
    cod = xdg_config_dir()
    assert cod == str(xdg_cod)
    xdg_cad = str(tmp_path / "xdg_cad")
    monkeypatch.setenv("XDG_CACHE_HOME", xdg_cad)
    cad = xdg_cache_dir()
    assert cad == str(xdg_cad)
